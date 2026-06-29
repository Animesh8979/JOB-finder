---
name: streamlit-ux-patterns
description: "Architectural rules for building Python Streamlit interfaces. Prevents rendering loops and state-leaks."
---

# Streamlit UX Architecture Laws

You are connected to the `Ai job finder` project which utilizes a Python Streamlit frontend.

## 1. Strict Session State Management
- Streamlit reruns the entire Python script top-to-bottom on every user interaction.
- You MUST store all persistent variables (API keys, scraped datasets, auth tokens) in `st.session_state`.
- Never execute heavy scrape/API calls directly in the main thread without caching them using `@st.cache_data` or `@st.cache_resource`.

## 2. Blocking Operation Callbacks
- If a UI button triggers a scraping pipeline, it must use the `on_click` callback pattern rather than procedural `if st.button():` checks to prevent the UI from deadlocking during execution.

## 3. UX Feedback
- Always implement `st.spinner()` or `st.progress()` when executing long-running extraction tasks so the user understands the system is working, not frozen.
