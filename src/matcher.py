"""Score jobs against the candidate profile using the AI.

Scoring is batched (several jobs per request) and uses the profile as *cached* context,
so scoring a whole page of results stays fast and costs very little.

Embedder model is configurable via the `JOB_FINDER_EMBEDDER` env var (overrides the default).
Approved drop-in models (all 384-dim — no DB migration needed between them):
    - "all-MiniLM-L6-v2"   (default, 33M params, ~130MB on disk, MTEB ~56)
    - "BAAI/bge-small-en-v1.5"  (33.4M, ~130MB, MTEB 62.17 — better recall, Apache-2.0)
Any other model must produce 384-dim vectors, OR a collection-name bump is required.
Set `JOB_FINDER_EMBEDDER=BAAI/bge-small-en-v1.5` in setup.bat to opt in.
"""
from __future__ import annotations

import os
from typing import Any, Callable
import threading
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

from . import llm
from .profile_parser import profile_context

# Configurable embedder. Default stays MiniLM to keep existing ChromaDB embeddings
# numerically valid; opt-in to bge-small via env for better recall on next full re-score.
_DEFAULT_EMBEDDER = "all-MiniLM-L6-v2"
EMBEDDER_NAME = os.environ.get("JOB_FINDER_EMBEDDER") or _DEFAULT_EMBEDDER

# Known-good 384-dim models. We refuse to bootstrap any other model unless the user
# overrides this allowlist — protects the hardcoded `np.zeros(...)` fallbacks below.
_384_DIM_ALLOWLIST = {
    "all-MiniLM-L6-v2",
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/bge-small-en-v1.5",
}
if EMBEDDER_NAME not in _384_DIM_ALLOWLIST:
    # Defensive: unknown model -> keep MiniLM, log to stderr (no crash, no surprise).
    import sys
    print(
        f"[matcher] WARNING: unknown embedder '{EMBEDDER_NAME}' — falling back to "
        f"{_DEFAULT_EMBEDDER}. Set JOB_FINDER_EMBEDDER to a 384-dim model.",
        file=sys.stderr,
    )
    EMBEDDER_NAME = _DEFAULT_EMBEDDER

# Vector dimension used for the `np.zeros(_EMBED_DIM)` fallbacks when encoding fails.
# All allowlisted models produce 384-dim embeddings.
_EMBED_DIM = 384

# Chroma collection suffix — bumped when we change embedder so we don't mix
# incompatible vector spaces in the same collection.
# Recent commit history: MiniLM = "jobs" (legacy). bge = "jobs_bge" (new space).
_COLLECTION_NAME = "jobs" if EMBEDDER_NAME == _DEFAULT_EMBEDDER else "jobs_bge"

_encoder_lock = threading.Lock()
_encoder_instance = None

def _get_encoder() -> SentenceTransformer:
    global _encoder_instance
    with _encoder_lock:
        if _encoder_instance is None:
            _encoder_instance = SentenceTransformer(EMBEDDER_NAME, device="cpu")
    return _encoder_instance


def preload_encoder() -> None:
    """Eagerly load the embedding model on startup so the first request isn't blocked.

    Call this from FastAPI's lifespan event in server.py.
    Safe to call multiple times — the global guard makes it a no-op after first load.
    """
    _get_encoder()

_SCORE_SYSTEM = (
    "You are a precise, no-nonsense technical recruiter and an ATS simulator. Given a candidate profile, "
    "a list of job postings, and their dense/sparse overlap metrics, rate how well the candidate fits "
    "EACH job from 1 (poor) to 10 (excellent). Judge realistically on skills, seniority, domain, and ATS "
    "keyword match probability. Give a reason of at most 15 words. Never invent candidate skills."
)

BATCH_SIZE = 6


def _trim(text: str, n: int = 700) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text[:n]


import chromadb
from . import config

_chroma_client = None

def get_chroma():
    global _chroma_client
    if _chroma_client is None:
        chroma_dir = config.DATA_DIR / "chroma"
        chroma_dir.mkdir(exist_ok=True, parents=True)
        _chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    return _chroma_client

def get_collection():
    client = get_chroma()
    return client.get_or_create_collection(name=_COLLECTION_NAME)

def _ensure_embeddings(jobs: list[dict[str, Any]]):
    """Ensure all jobs have embeddings in ChromaDB."""
    if not jobs:
        return
        
    collection = get_collection()
    job_ids = [str(j["id"]) for j in jobs]
    
    # Check what already exists
    existing = collection.get(ids=job_ids, include=["documents"])
    existing_ids = set(existing["ids"]) if existing and "ids" in existing else set()
    
    new_jobs = [j for j in jobs if str(j["id"]) not in existing_ids]
    if new_jobs:
        new_ids = [str(j["id"]) for j in new_jobs]
        new_texts = [_trim(j.get("description", "")) or _trim(j.get("title", "")) for j in new_jobs]
        
        try:
            encoder = _get_encoder()
            new_embeddings = encoder.encode(new_texts).tolist()
            collection.add(
                ids=new_ids,
                embeddings=new_embeddings,
                documents=new_texts
            )
        except Exception as e:
            print(f"Error encoding new jobs: {e}")

def pre_filter_jobs(
    jobs: list[dict[str, Any]], profile: dict[str, Any], threshold: float = 0.25
) -> list[dict[str, Any]]:
    """Return only jobs above embedding similarity threshold using ChromaDB."""
    if not jobs:
        return []
    
    ctx = profile_context(profile)
    try:
        encoder = _get_encoder()
        profile_vec = encoder.encode([ctx])[0]
    except Exception:
        profile_vec = np.zeros(_EMBED_DIM)
        
    _ensure_embeddings(jobs)
    collection = get_collection()
    
    embeddings_data = collection.get(
        ids=[str(j["id"]) for j in jobs],
        include=["embeddings"]
    )
    
    emb_dict = {}
    if embeddings_data and "embeddings" in embeddings_data and embeddings_data["embeddings"]:
        emb_dict = {id_: emb for id_, emb in zip(embeddings_data["ids"], embeddings_data["embeddings"])}
        
    filtered = []
    norm_p = np.linalg.norm(profile_vec)
    
    for job in jobs:
        jvec = emb_dict.get(str(job["id"]))
        if jvec is None:
            jvec = np.zeros(_EMBED_DIM)
            
        norm_j = np.linalg.norm(jvec)
        sim = float(np.dot(profile_vec, jvec) / (norm_p * norm_j + 1e-9)) if norm_p > 0 and norm_j > 0 else 0.0
        
        if sim >= threshold:
            job["_pre_score"] = round(sim, 3)
            filtered.append(job)
            
    return sorted(filtered, key=lambda j: j.get("_pre_score", 0), reverse=True)


def score_jobs(
    jobs: list[dict[str, Any]],
    profile: dict[str, Any],
    prefs: dict[str, Any],
    progress: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """Return a list of {"job", "score", "reason"} aligned to the input jobs."""
    ctx = profile_context(profile)
    model = prefs.get("scoring_model")
    results: list[dict[str, Any]] = []
    total = len(jobs)
    
    _ensure_embeddings(jobs)
    collection = get_collection()

    # Steer scoring with the candidate's stated preferences (in addition to the resume).
    steer_bits = []
    if prefs.get("titles"):
        steer_bits.append("Target titles: " + ", ".join(prefs["titles"]))
    if prefs.get("keywords"):
        steer_bits.append("Wanted skills/keywords: " + ", ".join(prefs["keywords"]))
    if prefs.get("seniority"):
        steer_bits.append("Preferred seniority: " + prefs["seniority"])
    if prefs.get("min_salary"):
        steer_bits.append(f"Minimum salary: {prefs['min_salary']}")
    steer = ("CANDIDATE PREFERENCES (weigh these too):\n" + "\n".join(steer_bits) + "\n\n") if steer_bits else ""

    for start in range(0, total, BATCH_SIZE):
        batch = jobs[start : start + BATCH_SIZE]
        
        try:
            encoder = _get_encoder()
            profile_embed = encoder.encode([ctx])[0]
        except Exception:
            profile_embed = np.zeros(_EMBED_DIM)
            
        batch_ids = [str(j["id"]) for j in batch]
        embeddings_data = collection.get(ids=batch_ids, include=["embeddings"])
        emb_dict = {}
        if embeddings_data and "embeddings" in embeddings_data and embeddings_data["embeddings"]:
            emb_dict = {id_: emb for id_, emb in zip(embeddings_data["ids"], embeddings_data["embeddings"])}
            
        vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2))
        try:
            if not ctx.strip():
                raise ValueError("Empty context")
            profile_sparse = vectorizer.fit_transform([ctx]).toarray()[0]
        except ValueError:
            profile_sparse = np.zeros(1)
            
        listing = []
        for i, job in enumerate(batch):
            sal = ""
            if job.get("salary_min") or job.get("salary_max"):
                sal = f" | salary {job.get('salary_min')}-{job.get('salary_max')} {job.get('currency','')}"
                
            job_desc = _trim(job.get('description',''))
            try:
                job_embed = emb_dict.get(str(job["id"]))
                if job_embed is None:
                    job_embed = np.zeros(_EMBED_DIM)
                
                norm_p = np.linalg.norm(profile_embed)
                norm_j = np.linalg.norm(job_embed)
                dense_sim = float(np.dot(profile_embed, job_embed) / (norm_p * norm_j + 1e-9)) if norm_p > 0 and norm_j > 0 else 0.0
            except Exception:
                dense_sim = 0.0
            
            try:
                if not job_desc.strip():
                    raise ValueError("Empty description")
                job_sparse = vectorizer.transform([job_desc]).toarray()[0]
                sum_j = np.sum(job_sparse)
                sparse_overlap = float(np.sum(np.minimum(profile_sparse, job_sparse)) / (sum_j + 1e-9)) if sum_j > 0 else 0.0
            except ValueError:
                sparse_overlap = 0.0
                
            listing.append(
                f"[{i}] {job.get('title','')} @ {job.get('company','')} "
                f"({job.get('location','')}){sal}\n"
                f"tags: {', '.join(job.get('tags') or [])}\n"
                f"description: {job_desc}\n"
                f"ATS Dense Similarity: {dense_sim:.3f} | ATS Sparse Overlap: {sparse_overlap:.3f}"
            )
        prompt = (
            steer
            + "Score these jobs for the candidate. Return a JSON array; one object per job "
            'with keys: index (int), score (int 1-10), reason (str <=15 words).\n\n'
            + "\n\n".join(listing)
        )
        try:
            data = llm.generate_json(
                prompt, system=_SCORE_SYSTEM, cached_context=ctx, model=model, max_tokens=600
            )
        except llm.LLMError:
            data = []

        by_index = {}
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "index" in item:
                    by_index[int(item["index"])] = item

        for i, job in enumerate(batch):
            item = by_index.get(i, {})
            try:
                score = max(1, min(10, int(item.get("score", 5))))
            except Exception:
                score = 5
            reason = str(item.get("reason", "") or "Not scored").strip()
            results.append({"job": job, "score": score, "reason": reason})

        if progress:
            progress(min(start + BATCH_SIZE, total), total)

    return results
