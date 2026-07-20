import json

with open('data/profiles/default.json', encoding='utf-8') as f:
    profile = json.load(f)

# Ground the Summary
profile["summary"] = (
    "Recent BBA (AI & ML) graduate from IILM University with hands-on internship experience in machine learning and digital marketing. "
    "Passionate about applying Python, SQL, and data analytics to solve real-world business problems. "
    "Independently developed multiple automation projects including a multi-agent trading bot and an AI-driven video content creator. "
    "Seeking an entry-level Business Analyst or Data Analyst role to leverage my technical skills and business background."
)

# Ground Experience
profile["experience"] = [
    {
      "title": "Machine Learning Intern",
      "company": "Elevate Labs",
      "location": "Remote, India",
      "dates": "Jun 2025 - Jul 2025",
      "details": [
        "Developed a machine learning pipeline using Python, automating data ingestion, exploratory data analysis (EDA), and feature engineering.",
        "Trained and evaluated regression and classification models, comparing performance metrics to improve predictive accuracy.",
        "Compiled a comprehensive data science report detailing model benchmarking and feature selection for senior mentors.",
        "Conducted EDA using Matplotlib and Seaborn to visualize data distributions and identify key business trends.",
        "Received the Best Performer Award for consistent delivery and high-quality code contributions throughout the internship."
      ]
    },
    {
      "title": "Digital Marketing Intern",
      "company": "Acmegrade",
      "location": "Remote, India",
      "dates": "Jul 2024 - Sep 2024",
      "details": [
        "Created and executed an SEO-focused content strategy using Ubersuggest, contributing to increased organic reach on Instagram and LinkedIn.",
        "Set up Google Analytics tracking to monitor user sessions, click-through rates (CTR), and overall campaign performance.",
        "Analyzed weekly KPIs to identify engagement bottlenecks and recommended adjustments to improve audience retention."
      ]
    }
]

# Ground Projects
profile["projects"] = [
    {
      "name": "RagnarShortsAI \u2014 AI Video Content Automation",
      "role": "Personal Project",
      "details": [
        "Built a Python-based automation script that generates short-form video content and schedules posts across multiple social platforms.",
        "Integrated LLMs for script generation and used FFmpeg for automated video assembly and rendering.",
        "Implemented error handling and logging to ensure reliable daily execution of the content pipeline."
      ]
    },
    {
      "name": "AI Trader Bot \u2014 Automated Trading System",
      "role": "Personal Project",
      "details": [
        "Developed a simulated trading bot integrating multiple LLMs for market sentiment analysis and decision routing.",
        "Built a Python risk management module to enforce stop-loss and position sizing rules during paper trading on NautilusTrader."
      ]
    },
    {
      "name": "AI Job Finder \u2014 Job Matching Aggregator",
      "role": "Personal Project",
      "details": [
        "Created a web scraping tool using Playwright and Firecrawl to aggregate job listings from multiple platforms into a centralized database.",
        "Implemented semantic search using ChromaDB and SentenceTransformers to match job descriptions against user resumes."
      ]
    },
    {
      "name": "SpiceRoute \u2014 E-commerce Analytics",
      "role": "Academic Project",
      "details": [
        "Collaborated in a team of 3 to design a D2C e-commerce platform concept featuring an AI-driven product recommendation quiz.",
        "Utilized Akkio for predictive modeling to estimate Customer Lifetime Value (CLV) and perform RFM segmentation."
      ]
    },
    {
      "name": "Customer Churn Prediction",
      "role": "Academic Project",
      "details": [
        "Trained a binary classifier on a telecom dataset to predict customer churn, evaluating performance using F1-score and AUC-ROC metrics.",
        "Authored a stakeholder-friendly report highlighting the top 3 drivers of churn based on exploratory data analysis."
      ]
    },
    {
      "name": "Sales Performance Dashboard",
      "role": "Academic Project",
      "details": [
        "Analyzed an FMCG business case to create a regional KPI dashboard mapping period-over-period sales trends and competitive metrics."
      ]
    }
]

# Write back
with open('data/profiles/default.json', 'w', encoding='utf-8') as f:
    json.dump(profile, f, indent=2)
