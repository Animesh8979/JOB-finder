# 🎯 AI Job Finder Command Center

A high-performance, local-first AI assistant that automates the tedious parts of a remote job search while keeping you in complete control.

With the newly completely overhauled **React Command Center**, the system provides a cinematic, single-page application experience to manage your entire job hunt.

1. **Finds** remote jobs from free, official job APIs (no scraping, no risky bots).
2. **Scores** each job against your resume so you only spend time on the best matches.
3. **Tailors** your resume and writes a custom cover letter for any job.
4. **Pre-fills the application** in a real browser — then *you* review and click **Submit**.
5. **Drafts** personalized outreach emails to recruiters (never auto-sent).
6. **Tracks** everything in a unified dashboard.

> ### 🔒 The Review-First Principle
> This tool is **review-first**. The AI prepares everything, but **you** make the final click to submit an application or send an email. Fully automatic bots can get your LinkedIn account banned and email blacklisted. This tool ensures you remain safe, credible, and in control.

---

## ✅ Prerequisites

- A Windows PC.
- An AI API key (Gemini or Anthropic Claude).
- Your resume in a standard format (PDF or DOCX).

---

## 🚀 Quick Start

1. **Run `run.bat`**
   Double-click `run.bat` in the root folder. This script will automatically:
   - Start the FastAPI backend server (port 8000).
   - Start the Huey background workers for asynchronous tasks.
   - Start the Vite React frontend (port 5173).
   - Open your browser to the Command Center.

2. **Setup Your Profile**
   In the Command Center, click the **Profile** button in the command bar (user icon). 
   - Add your API key.
   - Upload your resume (the AI will parse it automatically).
   - Save your settings.

---

## 🧭 The Command Center Experience

Everything happens in a single, unified view:

- **Live Intel Feed**: See new jobs flow in real-time. Use the **Command Bar** to filter by minimum score, remote-only status, or specific keywords.
- **Slide-Over Drawers**: 
  - **Job Detail**: Click any job to view deep insights, missing skills, and the AI recruiter's score breakdown.
  - **Tailor Drawer**: Generate a custom, hyper-optimized resume and cover letter.
  - **Prepare Apply**: Let the local browser automation fill out the ATS forms for you securely.
  - **Settings/Profile**: Manage your identity and API keys.
- **Pipeline Status Panel**: Monitor active background tasks (searches, tailoring, audits) running asynchronously in the background.

---

## 💾 Data Privacy & Storage

Everything stays in the `data/` folder on your computer:
- `data/profiles/default.json` — your resume, parsed into an AI-readable profile.
- `data/jobs.db` — local SQLite database storing all jobs and applications.
- `data/huey.db` — local SQLite database managing background task queues.
- `data/bot_profile/` — local isolated browser profile for secure automation.

**Nothing is uploaded anywhere except the explicit AI requests you trigger.**

---

## ⚖️ What this tool deliberately will *not* do (and why)

- ❌ Auto-submit on LinkedIn/Indeed or scrape gated domains → that gets **your** account banned.
- ❌ Mass-blast recruiter emails → that's spam and destroys your email reputation. Outreach is targeted and drafts-only.
- ❌ Invent fake experience → the AI strictly re-words and re-emphasizes **your real** background to match the job description.

These protections keep your accounts safe, your applications credible, and your data local.
