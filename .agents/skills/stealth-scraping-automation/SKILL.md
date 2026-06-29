---
name: stealth-scraping-automation
description: "Architectural rules for building robust web automation pipelines. Enforces stealth mechanics to prevent IP bans."
---

# Stealth Scraping Laws

You are connected to the `Ai job finder` project. Your automation code must be virtually indistinguishable from organic human traffic. 

## 1. Zero-Detection Headless Execution
- When using Playwright or Puppeteer, you MUST use the respective stealth plugins (e.g., `playwright-stealth`).
- Never run standard headless browsers without obfuscating the `navigator.webdriver` property.

## 2. Organic Timing and Jitter
- Never use fixed `time.sleep(2)`.
- You MUST implement randomized jitter between every interaction: `time.sleep(random.uniform(1.2, 3.8))`.
- Fast, programmatic clicking will trigger Cloudflare and DataDome immediately.

## 3. Header Obfuscation
- Always rotate standard browser User-Agents.
- Include complete Header profiles (`Accept-Language`, `Sec-Fetch-Dest`, etc.) matching modern Chrome or Firefox builds.
- Do not rely on requests/httpx default headers.
