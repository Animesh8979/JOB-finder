# 🎯 Remote Job Application Copilot

A friendly assistant that runs **on your own computer** and does the tedious parts of a
remote job search for you:

1. **Finds** remote jobs from free, official job APIs (no scraping, no risky bots).
2. **Scores** each job against your resume so you only spend time on good matches.
3. **Tailors** your resume and writes a **custom cover letter** for any job.
4. **Pre-fills the application** in a real browser — then *you* review and click **Submit**.
5. **Drafts** personalized, polite emails to recruiters you choose (never auto-sent).
6. **Tracks** everything: where you applied, the status, and follow-up reminders.

> ### 🔒 The one rule that protects you
> This is **review-first**. The tool *prepares* everything, but **you** make the final click
> to submit an application or send an email. That's deliberate — fully automatic
> "apply to everything / email everyone" bots get your **LinkedIn account banned** and your
> **email address blacklisted**. This tool is built so that never happens to you.

---

## ✅ What you need

- A Windows PC.
- One AI key (free options available — see below). Everything else is free.
- Your resume as a **PDF** or **Word (.docx)** file.

---

## 🚀 Setup (two steps)

1. **Double-click `setup.bat`.**
   It installs everything automatically (Python, libraries, a browser). The first run can
   take a few minutes. When it says *"Setup complete"*, you're done.

2. **Double-click `run.bat`.**
   The app opens in your web browser. To stop it later, just close the black window.

That's it. Leave both `.bat` files where they are.

---

## 🔑 Getting your AI key

The app uses AI to read your resume, score jobs, and write documents. Pick one:

- **Claude (recommended).** Go to <https://console.anthropic.com/settings/keys>, create a
  key, and paste it into the app's **Home & Setup** page. Cost is tiny — roughly a few cents
  per job (often less). Add a small amount of credit and it lasts a long time.
- **Gemini (free tier).** Go to <https://aistudio.google.com/apikey>, create a key. On the
  Setup page choose **Gemini**, paste the key, then run this once in the black window:
  `\.venv\Scripts\python -m pip install google-generativeai`

You only ever enter the key once, on the **Home & Setup** page.

---

## 🧭 How to use it (the 6 pages)

| Page | What it does |
|------|--------------|
| **🏠 Home & Setup** | Connect the AI, enter your name/contact, upload your resume, set what jobs you want. |
| **🔎 Find jobs** | Pull fresh remote jobs and let the AI rank them 1–10 against your resume. Save the good ones. |
| **✍️ Tailor** | For a saved job, generate a tailored resume + cover letter. Preview, tweak, download. |
| **📤 Apply** | Opens the application page in a browser and pre-fills it. **You review and submit.** |
| **✉️ Outreach** | Paste a recruiter's email (one you found yourself), get a personalized draft. **Drafts only.** |
| **📊 Tracker** | Every job, its status, and reminders to follow up. |

A normal flow: **Setup → Find jobs → save matches → Tailor → Apply → (optional) Outreach → Tracker.**

---

## 💾 Where your data lives

Everything stays in the `data/` folder on your computer:
- `profile.json` — your resume, parsed into a profile.
- `jobfinder.db` — saved jobs, applications, contacts, tracker.
- `outputs/` — the resumes and cover letters it generates.
- `secrets.json` / `.env` — your API keys (never shared, never committed to git).

Nothing is uploaded anywhere except the AI requests you trigger.

---

## 🆘 Troubleshooting

- **`setup.bat` closed too fast / showed an error.** Right-click it → *Run as administrator*,
  or read the last lines in the window. Most issues are a missing internet connection.
- **"No AI key set."** Open **Home & Setup** and paste your key, then click *Test AI connection*.
- **The browser tab didn't open.** Look in the black window for a line like
  `Local URL: http://localhost:8501` and open that address yourself.
- **Apply page can't fill a site.** Some application forms are unusual. The tool will give you
  a ready-to-paste answer sheet instead so you can fill it in seconds.

---

## ⚖️ What this tool deliberately will *not* do (and why)

- ❌ Auto-submit on LinkedIn/Indeed or scrape them → that gets **your** account banned.
- ❌ Harvest recruiter emails or mass-blast them → that's spam; it kills your email reputation
  and can break the law (CAN-SPAM / GDPR). Outreach here is targeted, capped, and drafts-only.
- ❌ Invent experience to match a job → it only re-words and re-emphasizes **your real** background.

These protections keep your accounts safe and your applications credible.
