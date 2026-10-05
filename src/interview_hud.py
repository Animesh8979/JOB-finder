"""Real-Time Interview Whisper HUD & Sub-50ms Question-Matching Engine.

Provides real-time candidate assistance during live interviews:
- Ingests streaming speech transcripts.
- Performs sub-50ms System-1 classification of question intent (System Design, STAR, Coding, Deep Dive).
- Instantly matches and retrieves the optimal STAR+R story from the persistent story bank.
- Emits structured HUD flashcards: 3 core bullet points, metrics, pitfalls to avoid, and reverse questions.
- Optional Deep Prep Mode: Uses LLM for dynamic, context-specific deep dive coaching.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import story_bank

logger = logging.getLogger(__name__)


@dataclass
class HUDCard:
    category: str  # "SYSTEM_DESIGN", "BEHAVIORAL_STAR", "CODING_ALGO", "DEEP_DIVE", "FIT"
    detected_intent: str
    headline: str
    talking_points: List[str]
    star_story: Optional[Dict[str, Any]] = None
    architecture_snippet: Optional[str] = None
    pitfall_warnings: List[str] = field(default_factory=list)
    counter_question_to_ask: Optional[str] = None
    confidence: float = 0.95


class InterviewHUDEngine:
    """Sub-50ms question matcher and live interview copilot."""

    QUESTION_PATTERNS = {
        "BEHAVIORAL_STAR": [
            r"tell me about a time", r"describe a situation", r"disagreed with", r"conflict",
            r"failed", r"mistake", r"proudest", r"under pressure", r"tight deadline",
            r"leadership", r"ambiguity", r"how did you", r"walk me through", r"experience with"
        ],
        "DATA_SQL_ANALYTICS": [
            r"\bsql\b", r"window function", r"\bcte\b", r"\bcohort\b", r"\bretention\b",
            r"\bchurn\b", r"\brfm\b", r"\bkpi\b", r"\bfunnel\b", r"conversion rate",
            r"\beda\b", r"exploratory data analysis", r"dashboard", r"\bmetrics?\b",
            r"data modeling", r"data analysis", r"pandas", r"client dataset", r"business analysis",
            r"imbalanced", r"\bsmote\b", r"auc-roc", r"f1-score"
        ],
        "SYSTEM_DESIGN": [
            r"design\s+.*(system|architecture|twitter|uber|rate limiter|cache|youtube|whatsapp|crawler|url shortener)",
            r"\brate limiter\b", r"\bdesign\b",
            r"scale", r"high throughput", r"sharding", r"replication", r"cap theorem",
            r"load balancer", r"microservices architecture", r"event-driven"
        ],
        "CODING_ALGO": [
            r"time complexity", r"space complexity", r"big o", r"binary tree", r"graph",
            r"dynamic programming", r"linked list", r"two pointer", r"sliding window",
            r"hash map", r"dfs", r"bfs"
        ],
        "DEEP_DIVE": [
            r"how does\s+.*\s+work under the hood", r"garbage collection", r"gil", r"event loop",
            r"virtual memory", r"b-tree", r"lsm-tree", r"tls handshake", r"tcp vs udp",
            r"optimistic locking"
        ]
    }

    ARCHITECTURE_TEMPLATES = {
        "rate limiter": """
[Client] --> [API Gateway / Envoy]
                  |
        [Redis Cluster (Token Bucket Lua)]
                  |
        [Core Services Pool]
""",
        "cache": """
[Application] ---> (Read) ---> [Redis / Memcached]
      |                                | (Cache Miss)
      +----------> [Postgres DB] <-----+ (Populate Cache)
""",
        "event-driven": """
[Producers] ---> [Kafka / Redpanda Cluster]
                        |
            +-----------+-----------+
            |                       |
      [Consumer Group A]      [Consumer Group B]
            |                       |
      [ClickHouse OLAP]       [Elasticsearch]
"""
    }

    def __init__(self):
        self.stories = story_bank.load_story_bank()

    def refresh_stories(self):
        """Reload stories from story bank."""
        self.stories = story_bank.load_story_bank()

    def classify_question(self, text: str) -> str:
        """Fast regex classification of interview query in < 5ms."""
        lower = text.lower()
        for cat, patterns in self.QUESTION_PATTERNS.items():
            if any(re.search(p, lower) for p in patterns):
                return cat
        return "FIT"

    def match_best_star_story(self, query: str) -> Optional[Dict[str, Any]]:
        """Find best matching candidate STAR story for behavioral query."""
        if not self.stories:
            return None

        lower = query.lower()
        best_story = None
        best_score = -1

        for s in self.stories:
            score = 0
            comp = s.get("competency", "").lower()
            title = s.get("title", "").lower()
            sit = s.get("situation", "").lower()
            act = s.get("action", "").lower()
            res = s.get("result", "").lower()

            for word in lower.split():
                if len(word) > 3:
                    root = word[:5] if len(word) >= 5 else word
                    if root in title or word in title:
                        score += 4
                    if root in comp or word in comp:
                        score += 3
                    if root in sit or root in act or root in res:
                        score += 1

            if score > best_score:
                best_score = score
                best_story = s

        return best_story or self.stories[0]

    def generate_hud_response(self, transcript_snippet: str, deep_prep: bool = False) -> HUDCard:
        """Generate structured HUD card in < 50ms from transcript snippet."""
        category = self.classify_question(transcript_snippet)
        lower = transcript_snippet.lower()

        # If deep prep requested via LLM
        if deep_prep:
            try:
                from . import llm
                prompt = (
                    f"You are an executive engineering interview coach. The interviewer just asked:\n"
                    f"\"{transcript_snippet}\"\n\n"
                    f"Return a JSON object with keys:\n"
                    f"- headline: 1-sentence strategic punchline\n"
                    f"- talking_points: list of 3-4 high-impact bullet points with quantified trade-offs\n"
                    f"- pitfall_warnings: list of 2 common failure traps candidates make on this question\n"
                    f"- counter_question_to_ask: 1 brilliant reverse question to ask back\n"
                )
                res = llm.generate_json(
                    prompt,
                    system="You are an elite Staff Engineering Interview Coach. Return ONLY valid JSON.",
                    temperature=0.2,
                    max_tokens=400
                )
                if isinstance(res, dict) and "talking_points" in res:
                    return HUDCard(
                        category=category,
                        detected_intent=f"AI Deep Prep: {category}",
                        headline=res.get("headline", "Strategic Response Blueprint"),
                        talking_points=res.get("talking_points", []),
                        pitfall_warnings=res.get("pitfall_warnings", []),
                        counter_question_to_ask=res.get("counter_question_to_ask")
                    )
            except Exception as e:
                logger.debug("InterviewHUD Deep Prep skipped: %s", e)

        # Baseline Sub-50ms Instant HUD Response
        if category == "BEHAVIORAL_STAR":
            story = self.match_best_star_story(transcript_snippet)
            if story:
                headline = f"STAR Strategy: {story.get('title', 'Project Experience')}"
                talking_points = [
                    f"Situation: {story.get('situation', '')[:100]}...",
                    f"Action: {story.get('action', '')[:120]}...",
                    f"Result: {story.get('result', '')[:100]}..."
                ]
            else:
                headline = "STAR Strategy: Core Engineering Ownership"
                talking_points = [
                    "Anchor on quantified metrics (latency reduction, revenue impact, scale).",
                    "Acknowledge trade-offs and alternative approaches considered.",
                    "Highlight post-mortem reflection and what was automated to prevent recurrences."
                ]

            return HUDCard(
                category="BEHAVIORAL_STAR",
                detected_intent="Behavioral Competency Evaluation",
                headline=headline,
                talking_points=talking_points,
                star_story=story,
                pitfall_warnings=[
                    "Avoid vague statements like 'we did this'. Use 'I architected', 'I measured'.",
                    "Do not speak longer than 2.5 minutes without checking in with the interviewer."
                ],
                counter_question_to_ask="How does the team currently measure success for this specific competency?"
            )

        elif category == "SYSTEM_DESIGN":
            arch = None
            for key, layout in self.ARCHITECTURE_TEMPLATES.items():
                if key in lower:
                    arch = layout
                    break
            if not arch:
                arch = self.ARCHITECTURE_TEMPLATES["event-driven"]

            return HUDCard(
                category="SYSTEM_DESIGN",
                detected_intent="Scalable Distributed System Architecture",
                headline="System Design Blueprint: Requirements -> High-Level -> Deep Dives",
                talking_points=[
                    "Clarify Functional Requirements (APIs, read/write ratio) & Non-Functional (p99 latency < 20ms, 99.99% SLA).",
                    "Perform back-of-the-envelope estimation (QPS, storage over 5 years).",
                    "Draw High-Level components first; do NOT jump prematurely into database sharding."
                ],
                architecture_snippet=arch,
                pitfall_warnings=[
                    "Never assume single-node database capacity without calculating IOPS.",
                    "Always address single point of failure (SPOF) and network partitions."
                ],
                counter_question_to_ask="Would you like me to dive deeper into the storage layer schema or the caching eviction policy?"
            )

        elif category == "CODING_ALGO":
            return HUDCard(
                category="CODING_ALGO",
                detected_intent="Data Structures & Algorithmic Problem Solving",
                headline="Coding Strategy: Clarify -> Brute Force -> Optimize -> Test",
                talking_points=[
                    "State constraints: input range, negative numbers, memory bounds.",
                    "Propose brute force approach first (e.g. O(N^2)) before optimizing.",
                    "Discuss optimal data structure (Hash Map for O(1) lookup, Two-Pointer for sorted arrays)."
                ],
                pitfall_warnings=[
                    "Do NOT start typing code before agreeing on the approach with the interviewer.",
                    "Test boundary conditions manually (empty array, single element, duplicates)."
                ],
                counter_question_to_ask="Are there specific memory constraints, or can we trade O(N) space for O(N) time?"
            )

        elif category == "DATA_SQL_ANALYTICS":
            story = self.match_best_star_story(transcript_snippet)
            points = [
                "Clarify Metric & Grain: Define business metrics precisely (active definition, temporal window, dimension vs fact).",
                "Query & Transformation: Structure via CTEs for clean staging, apply window functions (ROW_NUMBER, LAG/LEAD, DENSE_RANK), and avoid Cartesian joins.",
                "Business Actionability: Connect data movement directly to ROI, churn reduction, or operational resource allocation."
            ]
            if story and story.get("result"):
                headline = f"Data & Metrics Strategy: {story.get('title', 'Analytics Project')}"
                points.append(f"Candidate Proof: {story.get('result')[:120]}")
            else:
                headline = "Data & Metrics Strategy: SQL Grain -> Window Functions -> Business Levers"

            return HUDCard(
                category="DATA_SQL_ANALYTICS",
                detected_intent="SQL, Data Modeling & Business Analytics",
                headline=headline,
                talking_points=points,
                star_story=story,
                pitfall_warnings=[
                    "Never assume data is clean; always address NULL handling, duplicate keys, and timezone normalization.",
                    "Do not stop at the SQL query or metric number; always articulate what decision the executive makes with it."
                ],
                counter_question_to_ask="What is the primary operational metric your team is trying to move this quarter?"
            )

        else:
            return HUDCard(
                category="DEEP_DIVE",
                detected_intent="Technical Deep Dive / Domain Mastery",
                headline="Deep Dive: First Principles & Performance Trade-offs",
                talking_points=[
                    "Start with the core mental model (e.g. in-memory vs disk I/O, sync vs async).",
                    "Explain the trade-offs: why this design was chosen vs alternatives.",
                    "Reference a concrete production scenario where this made a measurable difference."
                ],
                pitfall_warnings=[
                    "Avoid reciting textbook definitions without real production context.",
                    "If unsure of an internal kernel detail, state your reasoning hypothesis transparently."
                ],
                counter_question_to_ask="In your current stack, have you encountered bottlenecks related to this?"
            )
