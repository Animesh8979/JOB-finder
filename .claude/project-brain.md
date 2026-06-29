## BEGIN MANAGED BLOCK: shared-project-brain
# Shared Project Brain

> [!CAUTION]
> **GLOBAL PERSONA DIRECTIVE**
> Before executing ANY command, you MUST read and strictly adhere to D:\AgentBrains\MASTER_PROMPT.md. You act as the Autonomous Staff Systems Architect. Do not deviate.

Project: AI Job Finder
Source: D:\Ai job finder
Brain: D:\AgentBrains\projects\ai-job-finder
Registry: D:\AgentBrains\agent-brain-registry.json
Graph: D:\AgentBrains\projects\ai-job-finder\graphify-out\graph.json

Rules:
1. Query this project's graph before broad file reads or searches.
2. Keep this project brain separate from the other two project brains.
3. Do not ingest secrets, credentials, databases, binary media, browser caches, or generated dependencies.
4. After meaningful work, append a short entry to D:\AgentBrains\projects\ai-job-finder\logs\activity.md.

Commands:
- Build/update: D:\AgentBrains\tools\agent-brain.ps1 -Action build -Project ai-job-finder
- Query: D:\AgentBrains\tools\agent-brain.ps1 -Action query -Project ai-job-finder -Question "your question"
- Status: D:\AgentBrains\tools\agent-brain.ps1 -Action status -Project ai-job-finder
## END MANAGED BLOCK: shared-project-brain


