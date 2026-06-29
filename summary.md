# 🚀 Remote Job Application Copilot - Updates Summary

Welcome! Six major updates have been implemented to make your Job Copilot even more powerful, flexible, and automated. Here is a summary of the new features:

---

## 1. ✏️ Edit Parsed Resume Profile
*   **What it does:** You can now inspect and manually edit your parsed resume fields.
*   **How to use it:** Go to the **🏠 Home & Setup** page, open the **`✏️ Edit parsed profile`** expander, make your modifications (including directly editing lists like Experience or Education in simple JSON format), and click **`Save Profile Edits`**.

## 2. 🔗 Paste Custom Job URL
*   **What it does:** Found a job on LinkedIn, a company careers page, or another board? You can paste its link directly to parse and score it.
*   **How to use it:** Go to the **🔎 Find jobs** page, select the **`🔗 Paste custom job URL`** tab, paste the link, and click **`Parse, Score & Save Job`**. The tool scrapes the text (using Playwright for complex JavaScript-rendered sites), parses it using AI, rates it 1-10, and adds it to your database.

## 3. 📋 Visual Kanban Tracking Board
*   **What it does:** Manage your active job hunt visually using a card-based Kanban board.
*   **How to use it:** Go to the **📊 Tracker** page. You can toggle between the **Kanban Board** and the **Spreadsheet Table**. On the Kanban board, you'll see cards with scores, companies, and titles sorted by columns. Use the selectbox on any card to move it to a different column.

## 4. 🎨 Design Templates (Minimalist, Corporate, Modern)
*   **What it does:** Customize the look and feel of your generated resumes and cover letters.
*   **How to use it:** On the **✍️ Tailor** page, a new sidebar is available on the left. You can choose a **Template Style** (`Minimalist`, `Corporate`, `Modern`), choose a **Font Face** (`Calibri`, `Arial`, `Georgia`, `Times New Roman`), pick an **Accent Color** for headers, and customize the **Page Margins**. Document exports (.docx and .pdf) will dynamically format using these selections.

## 5. 🤖 AI-Powered Custom Application Questions
*   **What it does:** Autofill now handles complex qualitative questions (e.g., *"Why do you want to join?"* or *"Tell us about a time you solved a hard problem"*).
*   **How to use it:** When you click **`Open & pre-fill in browser`** on the **📤 Apply** page, the browser script detects textareas and long custom question fields. It queries the LLM in the background to draft a concise, truthful answer based on your work history and types it directly into the form.

## 6. ⏰ Daily Background Auto-Fetching
*   **What it does:** Fetch and score new remote jobs automatically every morning.
*   **How to use it:** Double-click the new **`schedule_task.bat`** file in your project folder. It registers a silent daily background task at 9:00 AM. You can inspect logs and history directly on the **🏠 Home & Setup** page under **`Optional: Enable daily background auto-fetch`**.

---

*All data continues to be stored locally under the `data/` folder in your workspace.*
