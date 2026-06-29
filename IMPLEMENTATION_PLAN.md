# AI Job Finder — Comprehensive Implementation Plan

> 6 phases. Bug fixes → Foundation → Features. Every file, package, endpoint, and schema change specified.

---

## PHASE 0: Critical Bug Fixes (Priority: IMMEDIATE)

**Goal**: Make the existing codebase actually run without crashes.

### 0.1 — Fix `normalize()` call signature mismatch

**Files**: `src/sources/greenhouse.py`, `src/sources/lever.py`, `src/sources/hackernews.py`

**Problem**: `base.normalize()` uses keyword-only args (`def normalize(*, source, ...)`). All three files call it with a positional dict: `base.normalize({...}, source="greenhouse")`. This crashes with `TypeError`.

**Fix** — Convert positional dict to keyword unpacking in each file:

```python
# greenhouse.py line 35-44 — BEFORE:
norm = base.normalize({
    "id": str(j.get("internal_job_id") or j.get("id")),
    "url": j.get("absolute_url"),
    ...
}, source="greenhouse")

# AFTER:
norm = base.normalize(
    source="greenhouse",
    source_job_id=str(j.get("internal_job_id") or j.get("id")),
    url=j.get("absolute_url"),
    title=title,
    company=board.capitalize(),
    location=loc,
    tags=[j.get("department", "")] if j.get("department") else [],
    posted_at=j.get("updated_at"),
)
```

Same pattern for `lever.py` (lines 33-42) and `hackernews.py` (lines 60-68). Map each dict key to the corresponding keyword argument name from `base.normalize`'s signature.

**Complexity**: S

### 0.2 — Add missing `import json` to server.py

**File**: `server.py`

**Fix**: Add `import json` after line 1 (`import os`). Line 420 uses `json.dumps(profile)` inside `run_ats_check` but json is never imported.

**Complexity**: S

### 0.3 — Add missing dependencies to requirements.txt

**File**: `requirements.txt`

**Add these lines**:
```
numpy>=1.24.0
scikit-learn>=1.3.0
beautifulsoup4>=4.12.0
feedparser>=6.0.0
weasyprint>=60.0
```

Note: `numpy` and `scikit-learn` are transitive deps of `sentence-transformers` but must be explicit. `beautifulsoup4` is imported inline in `server.py:256`. `feedparser` is used in `weworkremotely.py`. `weasyprint` is needed for Phase 2 CV generator.

**Complexity**: S

### 0.4 — Fix auto_miner.py to use PostgreSQL

**File**: `auto_miner.py`

**Changes**:
- Remove `import sqlite3` and the `get_db()` function using sqlite3
- Import `from src.db import get_pool, _conn` (or use the db module's pool directly)
- Replace `get_db()` calls at lines 43, 66 with PostgreSQL queries via `src.db`
- Specifically: replace `conn.execute("SELECT ...")` with psycopg2 cursor against the connection pool

**Target code** (replace lines 1-11):
```python
import json
import logging
import time
from datetime import datetime
from src.db import get_pool
```

Replace `get_db().execute(...)` calls with:
```python
pool = get_pool()
with pool.connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, title, company, url, description FROM jobs WHERE match_score >= 70 ORDER BY match_score DESC LIMIT 5")
        jobs = cur.fetchall()
```

**Complexity**: M

### 0.5 — Implement cron_daemon.py

**File**: `cron_daemon.py`

**Current state**: Pure stub — logs messages but does nothing.

**Replace with actual implementation**:
```python
"""6-hour daemon: auto-mine, score, enrich, and queue outreach."""
import logging
import time
from auto_miner import run_pipeline

SLEEP = 6 * 60 * 60  # 6 hours

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

while True:
    logging.info("WAKE — starting mining pipeline")
    try:
        run_pipeline()
    except Exception as e:
        logging.exception("Pipeline failed: %s", e)
    logging.info("SLEEP %ds", SLEEP)
    time.sleep(SLEEP)
```

Also fix `start_daemon.bat` to call `python cron_daemon.py`.

**Complexity**: S

### 0.6 — Fix playwright-stealth import

**File**: `src/scraper.py` (or wherever playwright_stealth is imported)

Check import — the correct package name on PyPI is `playwright-stealth` and the import is:
```python
from playwright_stealth import stealth_sync  # correct
# NOT: from playwright_stealth.stealth import stealth_sync
```

Verify and fix if needed.

**Complexity**: S

---

## PHASE 1: Foundation Layer (Prerequisites for all features)

**Goal**: Establish the schema, state management, API foundation, and component architecture that all 4 features depend on.

### 1.1 — Resume JSON Schema Definition

**New file**: `src/resume_schema.py`

This is the canonical data model for the resume editor, CV generator, and auto-applier.

```python
"""Canonical resume schema used by editor, CV generator, and auto-applier."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class ResumeSection(BaseModel):
    id: str
    type: str  # "experience" | "education" | "skills" | "projects" | "certifications" | "summary" | "custom"
    title: str
    items: list[dict[str, Any]] = []
    visible: bool = True
    order: int = 0


class ResumeExperience(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    bullets: list[str] = []


class ResumeEducation(BaseModel):
    degree: str = ""
    field: str = ""
    school: str = ""
    year: str = ""


class ResumeData(BaseModel):
    id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""
    summary: str = ""
    sections: list[ResumeSection] = []
    template: str = "Corporate"  # Corporate | Modern | Minimalist
    accent_color: str = "#1F4E79"
    font: str = "Calibri"
    created_at: str = ""
    updated_at: str = ""
```

**Complexity**: S

### 1.2 — Database Schema Extension

**File**: `src/db.py`

Add new tables for resume storage and auto-apply tracking:

```sql
-- Resume storage
CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'Untitled Resume',
    data JSONB NOT NULL DEFAULT '{}',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TEXT DEFAULT NOW()::TEXT,
    updated_at TEXT DEFAULT NOW()::TEXT
);

-- Auto-apply job queue
CREATE TABLE IF NOT EXISTS auto_apply_queue (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'queued',  -- queued | applying | applied | failed | skipped
    form_answers JSONB DEFAULT '{}',
    error_message TEXT,
    applied_at TEXT,
    created_at TEXT DEFAULT NOW()::TEXT,
    updated_at TEXT DEFAULT NOW()::TEXT
);

-- Auto-apply session logs
CREATE TABLE IF NOT EXISTS auto_apply_logs (
    id SERIAL PRIMARY KEY,
    queue_id INTEGER REFERENCES auto_apply_queue(id) ON DELETE CASCADE,
    step TEXT,          -- navigate | detect_fields | fill_resume | fill_questions | upload_resume | submit | review
    status TEXT,        -- success | failed | skipped
    detail TEXT,
    screenshot_path TEXT,
    created_at TEXT DEFAULT NOW()::TEXT
);

-- Application form answer cache (LLM answers reused across similar questions)
CREATE TABLE IF NOT EXISTS form_answer_cache (
    id SERIAL PRIMARY KEY,
    question_hash TEXT UNIQUE,
    question_text TEXT,
    answer TEXT,
    context TEXT,        -- job title/company for relevance
    created_at TEXT DEFAULT NOW()::TEXT
);
```

Add helper functions:
- `save_resume(data: dict) -> int`
- `get_resume(resume_id: int) -> dict | None`
- `list_resumes() -> list[dict]`
- `delete_resume(resume_id: int) -> bool`
- `enqueue_auto_apply(job_id: int, resume_id: int) -> int`
- `get_auto_apply_queue(status: str = None) -> list[dict]`
- `update_auto_apply_status(queue_id: int, status: str, error: str = None)`
- `log_auto_apply_step(queue_id: int, step: str, status: str, detail: str = None)`
- `get_cached_answer(question_hash: str) -> str | None`
- `cache_answer(question_hash: str, question: str, answer: str, context: str)`

**Complexity**: M

### 1.3 — Error Boundaries in React

**New file**: `frontend/src/components/ErrorBoundary.tsx`

```tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-6 bg-red-950/30 border border-red-800 rounded-lg">
          <div className="flex items-center gap-2 text-red-400 mb-2">
            <AlertTriangle size={18} />
            <span className="font-semibold">Something went wrong</span>
          </div>
          <p className="text-red-300/70 text-sm">{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-3 px-3 py-1 text-xs bg-red-900/50 text-red-300 rounded hover:bg-red-900/80">
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

**File to modify**: `frontend/src/App.tsx` — wrap `renderContent()` in `<ErrorBoundary>`.

**Complexity**: S

### 1.4 — New API Routes Foundation

**File**: `server.py`

Add Pydantic models and endpoint stubs for all 4 features. These will be fleshed out in later phases.

**New Pydantic models** (add near line 100):
```python
class ResumePayload(BaseModel):
    name: str = "Untitled Resume"
    data: dict = {}
    template: str = "Corporate"
    accent_color: str = "#1F4E79"

class AutoApplyPayload(BaseModel):
    job_ids: list[int]
    resume_id: int
    dry_run: bool = True

class GenerateDocPayload(BaseModel):
    resume_id: int
    job_id: int | None = None
    doc_type: str = "resume"  # resume | cover_letter | both
    format: str = "pdf"  # pdf | docx | both
```

**New API endpoints** (add after existing routes):
```
# Resume CRUD
GET    /api/resumes                    → list all resumes
POST   /api/resumes                    → create/save resume
GET    /api/resumes/{id}               → get resume by ID
PUT    /api/resumes/{id}               → update resume
DELETE /api/resumes/{id}               → delete resume
POST   /api/resumes/{id}/activate      → set as primary

# CV Generation
POST   /api/generate                   → generate PDF/DOCX from resume data

# Auto-Apply
POST   /api/auto-apply/enqueue         → queue jobs for auto-application
GET    /api/auto-apply/queue           → get queue status
POST   /api/auto-apply/{id}/cancel     → cancel a queued item
GET    /api/auto-apply/{id}/logs       → get application logs
POST   /api/auto-apply/start           → trigger the auto-apply runner
```

**Complexity**: M

### 1.5 — API Client Module for React

**New file**: `frontend/src/api.ts`

Centralized fetch wrapper matching all backend endpoints:

```typescript
const BASE = '/api';

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts?.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Existing
  getStatus: () => request<any>('/status'),
  getProfile: () => request<any>('/profile'),
  saveProfile: (data: any) => request<any>('/profile', { method: 'POST', body: JSON.stringify(data) }),
  getJobs: (params?: Record<string, string>) => request<any[]>(`/jobs${params ? '?' + new URLSearchParams(params) : ''}`),
  // ... all existing endpoints ...

  // Resumes
  listResumes: () => request<any[]>('/resumes'),
  getResume: (id: number) => request<any>(`/resumes/${id}`),
  saveResume: (data: any) => request<any>('/resumes', { method: 'POST', body: JSON.stringify(data) }),
  updateResume: (id: number, data: any) => request<any>(`/resumes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteResume: (id: number) => request<void>(`/resumes/${id}`, { method: 'DELETE' }),

  // CV Generation
  generateDoc: (data: any) => request<any>('/generate', { method: 'POST', body: JSON.stringify(data) }),

  // Auto-Apply
  enqueueAutoApply: (data: any) => request<any>('/auto-apply/enqueue', { method: 'POST', body: JSON.stringify(data) }),
  getAutoApplyQueue: () => request<any[]>('/auto-apply/queue'),
  startAutoApply: () => request<any>('/auto-apply/start', { method: 'POST' }),
};
```

**Complexity**: S

---

## PHASE 2: Resume Editor + CV Generator

**Goal**: Interactive drag-and-drop resume editing with real-time preview and professional PDF/DOCX export.

### 2.1 — New npm Packages

```bash
cd frontend
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
npm install zustand
```

- `@dnd-kit` — modern drag-and-drop (replaces deprecated react-beautiful-dnd, better React 19 support)
- `zustand` — lightweight state management for resume data

### 2.2 — Resume State Store

**New file**: `frontend/src/store/resumeStore.ts`

```typescript
import { create } from 'zustand';

interface ResumeSection {
  id: string;
  type: string;
  title: string;
  items: any[];
  visible: boolean;
  order: number;
}

interface ResumeState {
  resume: {
    id: number | null;
    name: string;
    email: string;
    phone: string;
    location: string;
    linkedin: string;
    github: string;
    website: string;
    summary: string;
    sections: ResumeSection[];
    template: string;
    accent_color: string;
    font: string;
  };
  selectedSectionId: string | null;
  isDirty: boolean;
  isSaving: boolean;

  // Actions
  setResume: (data: any) => void;
  updateField: (field: string, value: string) => void;
  addSection: (type: string) => void;
  removeSection: (id: string) => void;
  reorderSections: (oldIndex: number, newIndex: number) => void;
  updateSectionItem: (sectionId: string, itemIndex: number, field: string, value: string) => void;
  addSectionItem: (sectionId: string) => void;
  removeSectionItem: (sectionId: string, itemIndex: number) => void;
  toggleSectionVisibility: (sectionId: string) => void;
  setTemplate: (template: string) => void;
  setSelectedSection: (id: string | null) => void;
  markDirty: () => void;
  autoSave: () => Promise<void>;
}

// Implementation with nanoid for section IDs, autoSave debounced to 2s
```

**Complexity**: M

### 2.3 — Resume Editor Page

**New file**: `frontend/src/pages/ResumeEditor.tsx`

Layout: **3-panel design**
- Left (25%): Section list with drag handles + add/remove buttons
- Center (40%): Inline editor form for the selected section
- Right (35%): Real-time PDF preview (rendered as scaled iframe or `@react-pdf/renderer`)

**Components**:
- `ResumeEditor.tsx` — page container, 3-panel layout
- `SectionList.tsx` — sortable section list with DnD
- `SectionEditor.tsx` — dynamic form based on section type
- `ResumePreview.tsx` — live preview using CSS that mirrors the PDF layout

**Key features**:
- Drag-and-drop section reordering via `@dnd-kit/sortable`
- Add/remove sections (experience, education, skills, projects, certifications, custom)
- Add/remove bullet points within experience items
- Live preview updates on every keystroke
- Template switcher (Corporate / Modern / Minimalist)
- Color picker for accent color
- Auto-save to backend every 2 seconds when dirty
- "Save" button for manual save
- Profile import: pull existing profile data into resume editor

**Complexity**: L

### 2.4 — Resume Editor Components

**New files**:
- `frontend/src/components/resume/SectionList.tsx`
- `frontend/src/components/resume/SectionEditor.tsx`
- `frontend/src/components/resume/ExperienceEditor.tsx`
- `frontend/src/components/resume/EducationEditor.tsx`
- `frontend/src/components/resume/SkillsEditor.tsx`
- `frontend/src/components/resume/ProjectsEditor.tsx`
- `frontend/src/components/resume/SummaryEditor.tsx`
- `frontend/src/components/resume/ResumePreview.tsx`

**SectionList.tsx** — uses `@dnd-kit/sortable`:
```tsx
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
```

**SectionEditor.tsx** — switches on `section.type`:
- `"experience"` → `ExperienceEditor` (company, title, dates, location, bullet list)
- `"education"` → `EducationEditor` (school, degree, field, year)
- `"skills"` → `SkillsEditor` (tag input with add/remove)
- `"projects"` → `ProjectsEditor` (name, description line)
- `"summary"` → `SummaryEditor` (textarea with word count)
- `"custom"` → generic title + textarea

**ResumePreview.tsx** — renders the resume as styled HTML that visually matches the PDF output. Uses a scaled container (`transform: scale(0.6)` with overflow hidden) to fit A4 in the panel.

**Complexity**: L

### 2.5 — CV Generator Backend

**File**: `src/documents.py`

Add WeasyPrint-based PDF generation for professional templates:

```python
from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
  @page { size: A4; margin: 18mm; }
  body { font-family: {{ font }}; font-size: 10.5pt; color: #1a1a1a; line-height: 1.4; }
  .name { font-size: 22pt; font-weight: bold; color: {{ accent_color }}; margin-bottom: 4pt; }
  .contact { font-size: 9.5pt; color: #555; margin-bottom: 12pt; }
  .section-title { font-size: 11pt; font-weight: bold; text-transform: uppercase;
    color: {{ accent_color }}; border-bottom: 1pt solid {{ accent_color }}; margin: 14pt 0 6pt; }
  .experience-item { margin-bottom: 10pt; }
  .exp-header { font-weight: bold; }
  .exp-meta { font-style: italic; font-size: 9pt; color: #666; }
  .bullets { padding-left: 18pt; margin: 4pt 0; }
  .bullets li { margin-bottom: 2pt; }
  .skills { columns: 2; column-gap: 20pt; }
</style>
</head>
<body>
  <div class="name">{{ name }}</div>
  <div class="contact">{{ contact }}</div>
  {% if summary %}<div class="section-title">Summary</div><p>{{ summary }}</p>{% endif %}
  {% if skills %}<div class="section-title">Skills</div><div class="skills">{{ skills | join(', ') }}</div>{% endif %}
  {% for section in sections %}
    {% if section.type == 'experience' %}
      <div class="section-title">{{ section.title }}</div>
      {% for job in section.items %}
        <div class="experience-item">
          <div class="exp-header">{{ job.title }} — {{ job.company }}</div>
          <div class="exp-meta">{{ job.location }}{% if job.dates %} | {{ job.dates }}{% endif %}</div>
          <ul class="bullets">{% for b in job.bullets %}<li>{{ b }}</li>{% endfor %}</ul>
        </div>
      {% endfor %}
    {% endif %}
    {# education, projects, certifications, custom sections similarly #}
  {% endfor %}
</body>
</html>
"""


def generate_pdf_from_resume(resume_data: dict, output_path: Path, style: dict | None = None) -> Path:
    """Generate professional PDF using WeasyPrint + Jinja2."""
    from weasyprint import HTML
    style = style or {}
    template = Template(HTML_TEMPLATE)
    html_str = template.render(
        font=style.get("font", "Calibri"),
        accent_color=style.get("accent_color", "#1F4E79"),
        name=resume_data.get("name", ""),
        contact=resume_data.get("contact", ""),
        summary=resume_data.get("summary", ""),
        skills=resume_data.get("skills", []),
        sections=resume_data.get("sections", []),
    )
    HTML(string=html_str).write_pdf(str(output_path))
    return output_path
```

Keep existing `save_resume_docx()` and `save_text_pdf()` (fpdf2) as fallback. Add the WeasyPrint path as the primary for "professional" template rendering.

**New API endpoint** in `server.py`:
```python
@app.post("/api/generate")
async def generate_document(payload: GenerateDocPayload):
    resume = db.get_resume(payload.resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    data = resume["data"]
    job = db.get_job(payload.job_id) if payload.job_id else None
    style = {"font": data.get("font", "Calibri"), "accent_color": data.get("accent_color", "#1F4E79")}
    paths = {}
    if payload.format in ("pdf", "both"):
        pdf_path = documents.generate_pdf_from_resume(data, stem.with_suffix(".pdf"), style)
        paths["pdf"] = f"/api/files/download?path={pdf_path}"
    if payload.format in ("docx", "both"):
        docx_path = documents.save_resume_docx(data, stem.with_suffix(".docx"), style)
        paths["docx"] = f"/api/files/download?path={docx_path}"
    return paths
```

**Complexity**: L

### 2.6 — Navigation Update

**File**: `frontend/src/App.tsx`

Add "Resume" to the sidebar menu items:
```typescript
{ id: 'resume', label: 'Resume Editor', icon: FileText, category: 'CORE' }
```

Add `case 'resume': return <ResumeEditor />;` to the switch in `renderContent()`.

Import `FileText` from lucide-react and `ResumeEditor` from `./pages/ResumeEditor`.

**Complexity**: S

---

## PHASE 3: 3D Frontend Experience

**Goal**: Immersive 3D landing/dashboard experience with React Three Fiber.

### 3.1 — New npm Packages

```bash
cd frontend
npm install three @react-three/fiber @react-three/drei @types/three
npm install @splinetool/viewer @splinetool/runtime
```

- `three` — Three.js core
- `@react-three/fiber` (31.1k ★) — React renderer for Three.js
- `@react-three/drei` (9.7k ★) — useful helpers (OrbitControls, Text3D, Float, Environment, ContactShadows)
- `@splinetool/viewer` — for embedding pre-made Spline scenes (optional, quick 3D assets)

### 3.2 — 3D Scene Components

**New directory**: `frontend/src/components/three/`

**Files**:

- `SceneContainer.tsx` — Canvas wrapper with performance settings:
```tsx
import { Canvas } from '@react-three/fiber';
import { AdaptiveDpr, AdaptiveEvents, Preload } from '@react-three/drei';
import { Suspense } from 'react';

interface Props { children: React.ReactNode; className?: string; }

export default function SceneContainer({ children, className }: Props) {
  return (
    <div className={className} style={{ width: '100%', height: '100%' }}>
      <Canvas
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        camera={{ position: [0, 0, 5], fov: 45 }}
      >
        <Suspense fallback={null}>
          <AdaptiveDpr pixelated />
          <AdaptiveEvents />
          {children}
          <Preload all />
        </Suspense>
      </Canvas>
    </div>
  );
}
```

- `FloatingParticles.tsx` — Ambient particle field for hero backgrounds:
```tsx
import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function FloatingParticles({ count = 200, color = '#6366f1' }) {
  const mesh = useRef<THREE.InstancedMesh>(null!);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i++) arr[i] = (Math.random() - 0.5) * 10;
    return arr;
  }, [count]);

  useFrame((state) => {
    mesh.current.rotation.y = state.clock.elapsedTime * 0.02;
    mesh.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.01) * 0.1;
  });

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, count]}>
      <sphereGeometry args={[0.02, 8, 8]} />
      <meshBasicMaterial color={color} transparent opacity={0.6} />
    </instancedMesh>
  );
}
```

- `JobCard3D.tsx` — Tilted 3D card for job listings:
```tsx
import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { RoundedBox, Text } from '@react-three/drei';
import * as THREE from 'three';

interface Props { title: string; company: string; score: number; position: [number, number, number]; }

export default function JobCard3D({ title, company, score, position }: Props) {
  const mesh = useRef<THREE.Group>(null!);
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (!mesh.current) return;
    mesh.current.rotation.y = THREE.MathUtils.lerp(
      mesh.current.rotation.y,
      hovered ? 0.1 : 0,
      0.1
    );
    mesh.current.position.y = position[1] + Math.sin(state.clock.elapsedTime + position[0]) * 0.05;
  });

  return (
    <group ref={mesh} position={position}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}>
      <RoundedBox args={[2.4, 1.4, 0.05]} radius={0.08} smoothness={4}>
        <meshStandardMaterial color={hovered ? '#4f46e5' : '#18181b'} />
      </RoundedBox>
      <Text position={[0, 0.3, 0.03]} fontSize={0.15} color="white" maxWidth={2} textAlign="center">
        {title}
      </Text>
      <Text position={[0, 0, 0.03]} fontSize={0.1} color="#a1a1aa" maxWidth={2} textAlign="center">
        {company}
      </Text>
      <Text position={[0, -0.3, 0.03]} fontSize={0.12} color={score >= 80 ? '#10b981' : '#f59e0b'} textAlign="center">
        {score}% match
      </Text>
    </group>
  );
}
```

- `HeroScene.tsx` — Full hero section with particles + rotating rings:
```tsx
import SceneContainer from './SceneContainer';
import FloatingParticles from './FloatingParticles';
import { OrbitControls, Float, Ring, Torus } from '@react-three/drei';

export default function HeroScene() {
  return (
    <SceneContainer className="absolute inset-0 z-0">
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      <FloatingParticles count={300} color="#6366f1" />
      <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
        <Ring args={[1.2, 1.25, 64]} position={[0, 0, -1]}>
          <meshBasicMaterial color="#6366f1" transparent opacity={0.3} />
        </Ring>
        <Torus args={[0.8, 0.02, 16, 100]} position={[0, 0, -0.5]} rotation={[Math.PI / 3, 0, 0]}>
          <meshBasicMaterial color="#818cf8" transparent opacity={0.4} />
        </Torus>
      </Float>
      <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
    </SceneContainer>
  );
}
```

**Complexity**: L

### 3.3 — Enhanced Dashboard with 3D Elements

**File**: `frontend/src/pages/Dashboard.tsx`

Add an optional 3D hero section at the top of the dashboard. Use a toggle so users can disable it for performance:

```tsx
import { useState, lazy, Suspense } from 'react';
const HeroScene = lazy(() => import('../components/three/HeroScene'));

// In Dashboard component:
const [show3D, setShow3D] = useState(true);

// Add toggle in header
<button onClick={() => setShow3D(!show3D)} className="text-xs text-gray-500">
  {show3D ? '3D: ON' : '3D: OFF'}
</button>

// Conditional render
{show3D && (
  <div className="relative h-48 mb-6 rounded-xl overflow-hidden">
    <Suspense fallback={<div className="h-full bg-black/50" />}>
      <HeroScene />
    </Suspense>
    <div className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
      <h2 className="text-3xl font-bold text-white drop-shadow-lg">AI Job Finder</h2>
    </div>
  </div>
)}
```

### 3.4 — TiltCard Enhancement

**File**: `frontend/src/components/TiltCard.tsx`

Upgrade existing TiltCard (85 lines) to use Framer Motion 3D transforms for smoother performance:
- Add `perspective` and `rotateX`/`rotateY` via `useMotionValue` + `useTransform`
- Add glassmorphism effect (`backdrop-blur-xl bg-white/5`)
- Keep existing tilt logic but modernize with Framer Motion's 3D spring

**Complexity**: M

### 3.5 — 3D Job Explorer Page (Optional/Future)

**New file**: `frontend/src/pages/JobExplorer3D.tsx`

A spatial view where top-matched jobs are displayed as floating 3D cards in a scene. User can orbit around, click a card to open job details. Uses `JobCard3D` component.

This is a stretch goal — stub the page with a placeholder if time is limited.

**Complexity**: XL

---

## PHASE 4: Automatic Job Applier

**Goal**: Full automation pipeline for LinkedIn/Indeed/Glassdoor applications using stealth Playwright.

### 4.1 — New Python Packages

```bash
pip install patchright  # patched Playwright for anti-detection
```

Note: `patchright` provides `playwright_stealth` built-in without separate `playwright-stealth` package. If keeping existing setup, ensure `playwright-stealth` is properly installed.

### 4.2 — Auto-Apply Engine

**New file**: `src/auto_applier.py`

Core orchestrator — reads from `auto_apply_queue` table, dispatches to platform-specific handlers:

```python
"""Full-auto job application engine with anti-detection.

Architecture:
  1. Read queued jobs from auto_apply_queue table
  2. For each job: load resume, detect platform, dispatch to handler
  3. Platform handler: navigate → detect fields → fill → upload → answer questions → review
  4. Log every step, screenshot on failure
  5. Update queue status

Anti-detection:
  - patchright (patched Playwright) for fingerprint consistency
  - Randomized delays: time.sleep(random.uniform(1.5, 4.0))
  - User-Agent rotation matching real Chrome profiles
  - Cookie/session persistence via persistent browser context
"""
import json
import random
import time
import hashlib
from pathlib import Path
from typing import Any
from src import config, db

GATED_DOMAINS = ("linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com")

PLATFORM_HANDLERS = {
    "linkedin": "handle_linkedin",
    "indeed": "handle_indeed",
    "glassdoor": "handle_glassdoor",
    "greenhouse": "handle_greenhouse",
    "lever": "handle_lever",
    "default": "handle_generic",
}


def detect_platform(url: str) -> str:
    url_lower = url.lower()
    for platform in ("linkedin", "indeed", "glassdoor", "greenhouse", "lever"):
        if platform in url_lower:
            return platform
    return "default"


def get_answer(question: str, job: dict, profile: dict, prefs: dict) -> str:
    """Check cache first, then call LLM."""
    q_hash = hashlib.sha256(question.lower().strip().encode()).hexdigest()[:16]
    cached = db.get_cached_answer(q_hash)
    if cached:
        return cached

    # Call LLM (reuse autofill_runner._generate_answer_to_question logic)
    from src.autofill_runner import _generate_answer_to_question
    cfg = {
        "provider": config.provider(),
        "anthropic_api_key": config.anthropic_key(),
        "gemini_api_key": config.gemini_key(),
        "writing_model": prefs.get("writing_model", "claude-sonnet-4-6"),
        "job_title": job.get("title", ""),
        "job_company": job.get("company", ""),
        "job_description": job.get("description", ""),
        "profile": profile,
    }
    answer = _generate_answer_to_question(question, cfg)
    if answer:
        db.cache_answer(q_hash, question, answer, f"{job.get('title')} @ {job.get('company')}")
    return answer


def apply_to_job(queue_id: int, job: dict, resume_data: dict, prefs: dict) -> dict:
    """Attempt to apply to a single job. Returns status dict."""
    url = job.get("apply_url") or job.get("url", "")
    platform = detect_platform(url)

    if any(d in url.lower() for d in GATED_DOMAINS):
        return {"status": "skipped", "reason": "login-gated site"}

    db.log_auto_apply_step(queue_id, "navigate", "success", f"Platform: {platform}")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                str(config.DATA_DIR / "auto_apply_state"),
                headless=False,
                viewport={"width": 1300, "height": 920},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                ],
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            # Apply stealth
            try:
                from playwright_stealth import stealth_sync
                stealth_sync(page)
            except ImportError:
                pass

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(random.uniform(2.0, 4.0))

            filled = _fill_form(page, resume_data, job, prefs, queue_id)
            screenshot_path = str(config.DATA_DIR / "outputs" / f"apply_{queue_id}.png")
            page.screenshot(path=screenshot_path)
            db.log_auto_apply_step(queue_id, "screenshot", "success", screenshot_path)

            ctx.close()

            return {"status": "applied", "filled_fields": filled, "screenshot": screenshot_path}
    except Exception as e:
        db.log_auto_apply_step(queue_id, "error", "failed", str(e))
        return {"status": "failed", "error": str(e)}


def _fill_form(page, resume_data: dict, job: dict, prefs: dict, queue_id: int) -> int:
    """Fill form fields using heuristics + LLM for custom questions."""
    filled = 0
    ident = prefs.get("identity", {}) or {}

    for frame in [page.main_frame] + page.main_frame.child_frames:
        # File uploads
        for inp in frame.query_selector_all("input[type=file]"):
            try:
                resume_path = str(config.DATA_DIR / "outputs" / "latest_resume.pdf")
                inp.set_input_files(resume_path)
                filled += 1
                db.log_auto_apply_step(queue_id, "upload_resume", "success")
                time.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                db.log_auto_apply_step(queue_id, "upload_resume", "failed", str(e))

        # Text fields
        for el in frame.query_selector_all("input, textarea"):
            try:
                itype = (el.get_attribute("type") or "text").lower()
                if itype in ("hidden", "file", "checkbox", "radio", "submit", "button", "password", "search"):
                    continue
                if not el.is_visible():
                    continue

                key = " ".join(filter(None, [
                    el.get_attribute("name"), el.get_attribute("id"),
                    el.get_attribute("placeholder"), el.get_attribute("aria-label"),
                ]))
                value = _match_field(key, ident, resume_data)

                if value:
                    el.fill(value)
                    filled += 1
                    time.sleep(random.uniform(0.3, 0.8))
                else:
                    # LLM for custom questions
                    tag = el.evaluate("el => el.tagName").lower()
                    label = _get_label(frame, el)
                    current = el.input_value()
                    if not current.strip() and label and (tag == "textarea" or len(label) > 15):
                        answer = get_answer(label, job, resume_data, prefs)
                        if answer:
                            el.fill(answer)
                            filled += 1
                            time.sleep(random.uniform(0.5, 1.5))
            except Exception:
                pass
    return filled


def _match_field(key: str, ident: dict, resume: dict) -> str:
    k = key.lower()
    skip = ("company", "search", "coupon", "how did you hear", "password", "salary", "captcha", "referral")
    if any(b in k for b in skip):
        return ""
    if "first" in k and "name" in k:
        return (ident.get("full_name") or "").split()[0:1][0] if ident.get("full_name") else ""
    if ("last" in k or "surname" in k) and "name" in k:
        parts = (ident.get("full_name") or "").split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""
    if "email" in k:
        return ident.get("email", resume.get("email", ""))
    if any(w in k for w in ("phone", "mobile", "tel")):
        return ident.get("phone", resume.get("phone", ""))
    if any(w in k for w in ("city", "location")):
        return ident.get("location", resume.get("location", ""))
    if "linkedin" in k:
        return ident.get("linkedin", "")
    if "github" in k:
        return resume.get("links", {}).get("github", "")
    if "cover" in k or "why do you want" in k or "message" in k:
        return ""  # Will be filled by LLM
    if "name" in k and "user" not in k and "file" not in k:
        return ident.get("full_name", "")
    return ""


def _get_label(frame, el) -> str:
    try:
        eid = el.get_attribute("id")
        if eid:
            lbl = frame.query_selector(f"label[for='{eid}']")
            if lbl:
                return lbl.inner_text().strip()
    except Exception:
        pass
    try:
        parent = el.query_selector("xpath=ancestor::label")
        if parent:
            return parent.inner_text().strip()
    except Exception:
        pass
    return el.get_attribute("placeholder") or el.get_attribute("aria-label") or el.get_attribute("name") or ""


def run_auto_apply(prefs: dict) -> dict:
    """Main entry point — process all queued items."""
    queue = db.get_auto_apply_queue(status="queued")
    results = {"applied": 0, "failed": 0, "skipped": 0}

    for item in queue:
        queue_id = item["id"]
        job = db.get_job(item["job_id"])
        resume = db.get_resume(item["resume_id"])

        if not job or not resume:
            db.update_auto_apply_status(queue_id, "skipped", "Job or resume not found")
            results["skipped"] += 1
            continue

        db.update_auto_apply_status(queue_id, "applying")
        result = apply_to_job(queue_id, job, resume["data"], prefs)
        db.update_auto_apply_status(queue_id, result["status"], result.get("error"))
        results[result["status"]] = results.get(result["status"], 0) + 1

        # Random delay between applications
        time.sleep(random.uniform(5.0, 15.0))

    return results
```

**Complexity**: XL

### 4.3 — Auto-Apply API Endpoints

**File**: `server.py`

Implement the endpoints defined in Phase 1.4:

```python
@app.post("/api/auto-apply/enqueue")
async def enqueue_auto_apply(payload: AutoApplyPayload):
    for job_id in payload.job_ids:
        db.enqueue_auto_apply(job_id, payload.resume_id)
    return {"queued": len(payload.job_ids)}

@app.get("/api/auto-apply/queue")
async def get_auto_apply_queue():
    return db.get_auto_apply_queue()

@app.post("/api/auto-apply/{queue_id}/cancel")
async def cancel_auto_apply(queue_id: int):
    db.update_auto_apply_status(queue_id, "skipped", "Cancelled by user")
    return {"ok": True}

@app.get("/api/auto-apply/{queue_id}/logs")
async def get_auto_apply_logs(queue_id: int):
    return db.get_auto_apply_logs(queue_id)

@app.post("/api/auto-apply/start")
async def start_auto_apply():
    from src.auto_applier import run_auto_apply
    from src import config as cfg
    prefs = db.get_preferences() or {}
    result = run_auto_apply(prefs)
    return result
```

### 4.4 — Auto-Apply React Page

**File**: `frontend/src/pages/Apply.tsx` (modify existing)

Extend the existing Apply page (244 lines) to add auto-apply mode:

**New sections to add**:
1. **Auto-Apply Queue** — table of queued jobs with status badges (queued/applying/applied/failed/skipped)
2. **Batch Enqueue** — select multiple jobs from Inbox → "Add to Auto-Apply Queue" button
3. **Live Log Viewer** — real-time log display during auto-apply run (poll `/api/auto-apply/queue` every 3s)
4. **Answer Cache** — view and edit cached LLM answers for common questions
5. **Session Manager** — manage browser sessions/cookies for each platform

**Key state additions**:
```typescript
const [autoApplyQueue, setAutoApplyQueue] = useState<any[]>([]);
const [isAutoApplying, setIsAutoApplying] = useState(false);
const [selectedJobs, setSelectedJobs] = useState<number[]>([]);
```

**Complexity**: L

### 4.5 — Batch Scoring Integration

**File**: `frontend/src/pages/FindJobs.tsx`

Add multi-select checkbox to job list rows. Add "Enqueue Selected for Auto-Apply" button that calls `POST /api/auto-apply/enqueue` with selected job IDs.

```tsx
const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);

const handleEnqueueAutoApply = async () => {
  if (!selectedJobIds.length || !activeResumeId) return;
  await api.enqueueAutoApply({ job_ids: selectedJobIds, resume_id: activeResumeId });
  toast.success(`${selectedJobIds.length} job(s) queued for auto-apply`);
  setSelectedJobIds([]);
};
```

**Complexity**: M

---

## PHASE 5: Integration, Polish, and Testing

**Goal**: Wire everything together, add tests, and harden the system.

### 5.1 — Deprecate Streamlit UI

**Decision**: Mark Streamlit as legacy. Add a note to `app.py`:

```python
st.sidebar.warning("⚠️ Streamlit UI is deprecated. Use the React frontend at http://localhost:5173")
```

Do NOT delete Streamlit code yet — keep as fallback until React frontend is feature-complete.

### 5.2 — Unified Profile → Resume Import

**New API endpoint**: `POST /api/resumes/import-from-profile`

```python
@app.post("/api/resumes/import-from-profile")
async def import_profile_to_resume():
    profile = db.get_profile()
    if not profile:
        raise HTTPException(404, "No profile found")
    resume_data = {
        "name": profile.get("name", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "location": profile.get("location", ""),
        "linkedin": profile.get("links", {}).get("linkedin", ""),
        "github": profile.get("links", {}).get("github", ""),
        "summary": profile.get("summary", ""),
        "sections": _profile_to_sections(profile),
    }
    resume_id = db.save_resume({"name": f"Profile Import", "data": resume_data, "is_primary": True})
    return {"id": resume_id, "data": resume_data}

def _profile_to_sections(profile: dict) -> list[dict]:
    sections = []
    order = 0
    if profile.get("experience"):
        sections.append({"id": "exp-1", "type": "experience", "title": "Experience",
                         "items": profile["experience"], "visible": True, "order": order})
        order += 1
    if profile.get("education"):
        sections.append({"id": "edu-1", "type": "education", "title": "Education",
                         "items": profile["education"], "visible": True, "order": order})
        order += 1
    if profile.get("skills"):
        sections.append({"id": "sk-1", "type": "skills", "title": "Skills",
                         "items": [{"name": s} for s in profile["skills"]], "visible": True, "order": order})
        order += 1
    if profile.get("projects"):
        sections.append({"id": "proj-1", "type": "projects", "title": "Projects",
                         "items": profile["projects"], "visible": True, "order": order})
    return sections
```

**Complexity**: M

### 5.3 — Python Tests

**New directory**: `tests/`

**New files**:
- `tests/__init__.py`
- `tests/conftest.py` — shared fixtures (mock DB, test profile, test prefs)
- `tests/test_resume_schema.py` — validate schema models
- `tests/test_documents.py` — test DOCX/PDF generation
- `tests/test_auto_applier.py` — test field matching, platform detection, answer caching
- `tests/test_tailor.py` — test fabrication shield
- `tests/test_api.py` — test all FastAPI endpoints with TestClient

**Setup**:
```bash
pip install pytest pytest-asyncio httpx  # httpx for FastAPI TestClient
```

**conftest.py**:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    from server import app
    return TestClient(app)

@pytest.fixture
def sample_resume():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "sections": [
            {"id": "exp-1", "type": "experience", "title": "Experience",
             "items": [{"title": "Engineer", "company": "Acme", "bullets": ["Built things"]}],
             "visible": True, "order": 0}
        ]
    }

@pytest.fixture
def sample_job():
    return {"id": 1, "title": "Backend Engineer", "company": "Acme", "description": "Python, FastAPI"}
```

**Complexity**: M

### 5.4 — React Tests

**New npm packages**:
```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

**New files**:
- `frontend/src/__tests__/ResumeEditor.test.tsx`
- `frontend/src/__tests__/resumeStore.test.ts`
- `frontend/src/__tests__/api.test.ts`

**Test vitest config** (add to `vitest.config.ts`):
```typescript
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
});
```

**Complexity**: M

### 5.5 — Anti-Detection Hardening

**File**: `src/auto_applier.py`

Add stealth improvements:
```python
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--disable-infobars",
    "--disable-extensions",
    "--window-size=1300,920",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]
```

- Use `patchright` instead of vanilla Playwright when available
- Rotate User-Agent per session
- Cookie persistence via `launch_persistent_context`
- Randomized typing speed: `page.keyboard.type(text, delay=random.randint(30, 80))`
- Random scroll before interacting: `page.mouse.wheel(0, random.randint(100, 400))`

**Complexity**: M

### 5.6 — Build & Deploy

**File**: `build.bat` (update)

```bat
@echo off
echo Building React frontend...
cd frontend
call npm run build
cd ..
echo Starting FastAPI server...
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

**File**: `setup.bat` (update)

Add to existing setup:
```bat
REM Install new Python deps
pip install -r requirements.txt
pip install patchright
playwright install chromium

REM Install React deps
cd frontend
call npm install
cd ..

REM Start Docker services
docker-compose up -d

REM Run migrations
python -c "from src.db import init_db; init_db()"
```

**Complexity**: S

---

## Summary: Phase Dependency Graph

```
Phase 0 (Bug Fixes)          ← MUST be first
    ↓
Phase 1 (Foundation)         ← Schema, DB, API stubs, ErrorBoundary
    ↓
    ├─→ Phase 2 (Resume Editor + CV Generator)  ← depends on 1.1-1.4
    ├─→ Phase 3 (3D Frontend)                   ← depends on 1.3, 1.5
    └─→ Phase 4 (Auto Applier)                  ← depends on 1.2, 1.4
    ↓
Phase 5 (Integration + Tests) ← depends on all above
```

## Package Summary

### Python (requirements.txt additions)
```
numpy>=1.24.0
scikit-learn>=1.3.0
beautifulsoup4>=4.12.0
feedparser>=6.0.0
weasyprint>=60.0
jinja2>=3.1.0
patchright>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

### npm (frontend/package.json additions)
```
@dnd-kit/core
@dnd-kit/sortable
@dnd-kit/utilities
zustand
three
@react-three/fiber
@react-three/drei
@types/three
@splinetool/viewer
@splinetool/runtime
vitest (dev)
@jsdom (dev)
@testing-library/react (dev)
@testing-library/jest-dom (dev)
```

## Complexity Summary

| Phase | Task | Complexity |
|-------|------|-----------|
| 0.1 | Fix normalize() calls | S |
| 0.2 | Add import json | S |
| 0.3 | Fix requirements.txt | S |
| 0.4 | Fix auto_miner.py PostgreSQL | M |
| 0.5 | Implement cron_daemon.py | S |
| 0.6 | Fix playwright-stealth import | S |
| 1.1 | Resume JSON schema | S |
| 1.2 | Database schema extension | M |
| 1.3 | ErrorBoundary component | S |
| 1.4 | API routes foundation | M |
| 1.5 | API client module | S |
| 2.1 | npm packages install | S |
| 2.2 | Resume state store (zustand) | M |
| 2.3 | Resume Editor page | L |
| 2.4 | Resume Editor components | L |
| 2.5 | CV Generator (WeasyPrint) | L |
| 2.6 | Navigation update | S |
| 3.1 | npm packages install | S |
| 3.2 | 3D scene components | L |
| 3.3 | Dashboard 3D integration | M |
| 3.4 | TiltCard enhancement | M |
| 3.5 | 3D Job Explorer (stretch) | XL |
| 4.1 | Python packages install | S |
| 4.2 | Auto-Apply engine | XL |
| 4.3 | Auto-Apply API endpoints | M |
| 4.4 | Auto-Apply React page | L |
| 4.5 | Batch scoring integration | M |
| 5.1 | Deprecate Streamlit | S |
| 5.2 | Profile → Resume import | M |
| 5.3 | Python tests | M |
| 5.4 | React tests | M |
| 5.5 | Anti-detection hardening | M |
| 5.6 | Build & deploy scripts | S |
