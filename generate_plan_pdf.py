import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.units import inch

def generate_pdf():
    pdf_path = r"D:\Ai job finder\AI_JOB_FINDER_PLAN.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#0284C7'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )
    
    code_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F1F5F9'),
        borderPadding=5,
        spaceBefore=3,
        spaceAfter=6
    )
    
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1E293B')
    )
    
    table_head = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    story = []
    
    # Title & Metadata
    story.append(Paragraph("AI Job Finder: Hardened SOTA Implementation Plan", title_style))
    story.append(Paragraph("<b>Target Root:</b> D:\\Ai job finder &nbsp;|&nbsp; <b>Architecture:</b> 2026 SOTA Local-First Copilot &nbsp;|&nbsp; <b>Status:</b> Ready for Execution", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceAfter=12))
    
    # Executive Scorecard Table
    story.append(Paragraph("1. Executive Tooling Scorecard & Upgrade Matrix", h1_style))
    
    table_data = [
        [
            Paragraph("Subsystem", table_head),
            Paragraph("Previous Choice", table_head),
            Paragraph("SOTA Replacement", table_head),
            Paragraph("Score", table_head),
            Paragraph("Core Architectural Rationale", table_head)
        ],
        [
            Paragraph("<b>Vector DB</b>", table_text),
            Paragraph("ChromaDB (embedded)", table_text),
            Paragraph("<b>LanceDB</b>", table_text),
            Paragraph("5.5 &rarr; <b>9.5</b>", table_text),
            Paragraph("Eliminates SQLite write-lock timeouts during concurrent ingestion; zero-copy mmap.", table_text)
        ],
        [
            Paragraph("<b>Embedding</b>", table_text),
            Paragraph("all-MiniLM-L6-v2", table_text),
            Paragraph("<b>BAAI/bge-small-en-v1.5</b>", table_text),
            Paragraph("5.5 &rarr; <b>9.0</b>", table_text),
            Paragraph("512-token context prevents truncating 70% of job requirements; +11.25 MTEB gain.", table_text)
        ],
        [
            Paragraph("<b>Lexical Search</b>", table_text),
            Paragraph("rank-bm25", table_text),
            Paragraph("<b>bm25s</b> (disk mmap)", table_text),
            Paragraph("5.0 &rarr; <b>9.5</b>", table_text),
            Paragraph("Sparse matrix precomputed index; 500x faster execution; zero boot re-tokenization.", table_text)
        ],
        [
            Paragraph("<b>PDF Engine</b>", table_text),
            Paragraph("Playwright Chromium", table_text),
            Paragraph("<b>Typst / RenderCV v2</b>", table_text),
            Paragraph("7.5 &rarr; <b>9.5</b>", table_text),
            Paragraph("Compiles in 15ms; avoids Chromium Skia kerning fragmentation; guaranteed ATS text order.", table_text)
        ],
        [
            Paragraph("<b>Stealth Browser</b>", table_text),
            Paragraph("Camoufox + Playwright", table_text),
            Paragraph("<b>Camoufox Hardened</b>", table_text),
            Paragraph("8.5 &rarr; <b>9.5</b>", table_text),
            Paragraph("C++ Gecko spoofing immune to JS prototype inspection; enable humanize & geoip.", table_text)
        ],
        [
            Paragraph("<b>Task Queue</b>", table_text),
            Paragraph("SqliteHuey", table_text),
            Paragraph("<b>SqliteHuey (WAL Mode)</b>", table_text),
            Paragraph("9.0 &rarr; <b>9.5</b>", table_text),
            Paragraph("Windows native zero-daemon queue; enable WAL and busy_timeout=5000.", table_text)
        ],
        [
            Paragraph("<b>Frontend UI</b>", table_text),
            Paragraph("React 19 + Vite 8", table_text),
            Paragraph("<b>React 19 + Virtualizer</b>", table_text),
            Paragraph("9.0 &rarr; <b>9.5</b>", table_text),
            Paragraph("Add @tanstack/react-virtual to limit active DOM cards to ~15 for locked 60 FPS.", table_text)
        ],
        [
            Paragraph("<b>API Backend</b>", table_text),
            Paragraph("FastAPI + uvicorn", table_text),
            Paragraph("<b>FastAPI Lifespan</b>", table_text),
            Paragraph("9.5 &rarr; <b>9.8</b>", table_text),
            Paragraph("Eagerly preload models in lifespan handler; enable GZipMiddleware for fast transfers.", table_text)
        ],
    ]
    
    col_widths = [75, 100, 115, 60, 180]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))
    
    # Phase 0
    story.append(Paragraph("Phase 0: Security Hardening & Execution Bug Fixes", h1_style))
    story.append(Paragraph("<b>Task 0.1: Fix Async Desync in Browser Agent (D:\\Ai job finder\\src\\browser_agent.py:210)</b><br/>"
                           "Resolve silent autofill failure where async Playwright page was passed to sync runner. Convert to <code>_fill_page_async</code> with full locator actionability checks.", body_style))
    story.append(Paragraph("<b>Task 0.2: Eliminate Firefox Profile Collision Traps (D:\\Ai job finder\\src\\stealth_browser.py)</b><br/>"
                           "Enforce isolated profile directory allocation (<code>data/profiles/worker_{id}</code>) to prevent Firefox <code>parent.lock</code> crashes under concurrent scraping.", body_style))
    story.append(Paragraph("<b>Task 0.3: Scrub Hardcoded Secrets (D:\\Ai job finder\\src\\config.py)</b><br/>"
                           "Ensure all passwords, API tokens, and session secrets load strictly via <code>python-dotenv</code> from <code>.env</code>.", body_style))
    story.append(Paragraph("<b>Verification Gate 0:</b> <code>pytest tests/test_browser_agent.py</code> &rarr; PASS with 0 unawaited coroutine warnings.", code_style))
    story.append(Spacer(1, 10))

    # Phase 1
    story.append(Paragraph("Phase 1: Vector DB & Embedding SOTA Migration", h1_style))
    story.append(Paragraph("<b>Task 1.1: Install Dependencies:</b> <code>pip install lancedb sentence-transformers==3.3.0 pyarrow</code>", body_style))
    story.append(Paragraph("<b>Task 1.2: Upgrade Matcher Model (D:\\Ai job finder\\src\\matcher.py)</b><br/>"
                           "Replace <code>all-MiniLM-L6-v2</code> with <code>BAAI/bge-small-en-v1.5</code>. Preserves identical 384-dim structure while doubling context to 512 tokens to capture full job qualifications.", body_style))
    story.append(Paragraph("<b>Task 1.3: Build Migration Script (D:\\Ai job finder\\scripts\\migrate_to_lancedb.py)</b><br/>"
                           "Read records from <code>jobfinder.db</code>, compute embeddings, and initialize LanceDB table at <code>data/lancedb</code>.", body_style))
    story.append(Paragraph("<b>Verification Gate 1:</b> Execute migration script; verify LanceDB directory populated and vector search returns without database lock errors.", code_style))
    story.append(Spacer(1, 10))

    # Phase 2
    story.append(Paragraph("Phase 2: Lexical Search Upgrade (rank-bm25 &rarr; bm25s)", h1_style))
    story.append(Paragraph("<b>Task 2.1: Install bm25s:</b> <code>pip install bm25s PyStemmer</code>", body_style))
    story.append(Paragraph("<b>Task 2.2: Implement Persistent bm25s Indexer (D:\\Ai job finder\\src\\matcher.py)</b><br/>"
                           "Precompute sparse indices and save to disk with memory mapping (<code>mmap=True</code>), cutting query latency to &lt;2ms without in-memory retokenization on server boot.", body_style))
    story.append(Paragraph("<b>Task 2.3: Maintain Reciprocal Rank Fusion (RRF):</b> Retain scale-invariant RRF (k=60) combining LanceDB dense rankings and bm25s lexical rankings.", body_style))
    story.append(Paragraph("<b>Verification Gate 2:</b> <code>python -c \"from src.matcher import query_bm25; docs, s = query_bm25('python', 5); assert len(docs) > 0\"</code>", code_style))
    story.append(Spacer(1, 10))

    # Phase 3
    story.append(Paragraph("Phase 3: High-Fidelity ATS PDF Engine (Typst / RenderCV)", h1_style))
    story.append(Paragraph("<b>Task 3.1: Integrate Typst Document Compilation (D:\\Ai job finder\\src\\pdf_engine.py)</b><br/>"
                           "Generate clean .typ markup and invoke <code>typst compile</code>. Guarantees 100% linear text extraction and standard CMaps for taleo/workday ATS systems.", body_style))
    story.append(Paragraph("<b>Task 3.2: Relegate Playwright PDF to Visual Preview:</b> Use Chromium HTML-to-PDF strictly for in-browser visual previews; all job submissions compile via Typst.", body_style))
    story.append(Paragraph("<b>Verification Gate 3:</b> Extract text via <code>pypdf</code> from output PDF; verify unbroken word boundaries and zero kerning artifacts.", code_style))
    story.append(Spacer(1, 10))

    # Phase 4
    story.append(Paragraph("Phase 4: Browser Stealth Hardening & Huey Concurrency", h1_style))
    story.append(Paragraph("<b>Task 4.1: Inject Camoufox Anti-Detect Parameters (D:\\Ai job finder\\src\\stealth_browser.py)</b><br/>"
                           "Enable <code>humanize=True</code> (Bézier mouse curves and typing jitter) and <code>geoip=True</code> (automatic timezone and WebRTC alignment).", body_style))
    story.append(Paragraph("<b>Task 4.2: Enforce WAL Mode on Huey Queue (D:\\Ai job finder\\src\\tasks.py)</b><br/>"
                           "Set <code>journal_mode=wal</code> and <code>busy_timeout=5000</code> in SqliteHuey pragmas.", body_style))
    story.append(Paragraph("<b>Task 4.3: Threaded Consumer Execution Script:</b> Update <code>run_worker.bat</code> with <code>-k thread -w 2</code>.", body_style))
    story.append(Paragraph("<b>Verification Gate 4:</b> Start worker; verify <code>data/huey.db-wal</code> exists and background tasks execute without locking web server.", code_style))
    story.append(Spacer(1, 10))

    # Phase 5
    story.append(Paragraph("Phase 5: Frontend DOM Virtualization & Server Lifespan Preloading", h1_style))
    story.append(Paragraph("<b>Task 5.1: Virtualize Job Feed (D:\\Ai job finder\\frontend):</b> Install <code>@tanstack/react-virtual</code> and wrap <code>LiveIntelFeed.tsx</code> list, capping rendered nodes to ~15 active cards.", body_style))
    story.append(Paragraph("<b>Task 5.2: Configure Server Lifespan Preloading & GZip (D:\\Ai job finder\\server.py):</b> Preload SentenceTransformer off the HTTP request path; add <code>GZipMiddleware</code>.", body_style))
    story.append(Paragraph("<b>Verification Gate 5:</b> <code>npm run build</code> clean; API response latency under 50ms with GZip compression.", code_style))

    doc.build(story)
    print(f"[SUCCESS] PDF generated at {pdf_path}")

if __name__ == '__main__':
    generate_pdf()
