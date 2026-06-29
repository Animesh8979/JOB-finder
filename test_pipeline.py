import asyncio
from src import job_discovery, auto_network

print("--- Testing Phase 1: Job Discovery ---")
try:
    count = job_discovery.discover_and_ingest("AI Engineer", "Remote", results_wanted=1)
    print(f"Discovered and ingested {count} jobs")
except Exception as e:
    print(f"Discovery Error: {e}")

print("\n--- Testing Phase 4: Auto Network Queue ---")
try:
    count = auto_network.process_outreach_queue()
    print(f"Processed {count} outreach emails")
except Exception as e:
    print(f"Outreach Error: {e}")
