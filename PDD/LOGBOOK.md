[STEP] v0.1 skeleton created with /health, /files/upload, /files/{job_id}/status (port 5055) - 2025-11-12T09:03:41.341Z
[STEP] v0.1.clean removed dev scripts; added self-run @ 2025-11-12T09:15:32.000Z
[STEP] v0.2 added /process/{job_id}/parse for PDF→clauses.json @ 2025-11-12T09:25:28.000Z
[STEP] v0.3 added TF-IDF cosine RAG (/rag/index, /rag/search) + docs/TEAM_GUIDE.md @ 2025-11-15T01:40:16.000Z
[STEP] v0.4 added weighted severity engine (services/severity.py) + /analyze/{job_id}/clauses @ 2025-11-15T04:08:25.000Z
[STEP] v0.5 added unified /query/{job_id} endpoint (RAG + severity) @ 2025-11-15T04:25:55.000Z
[STEP] v0.6 Added legal_kb.json + KB-driven severity engine + /knowledge/kb + UNKNOWN fallback @ 2025-11-15T09:56:48.000Z
[STEP] v0.6 Added human-readable answers to /query and improved TEAM_GUIDE for frontend/DB teammates. @ 2025-11-15T17:50:00.000Z
[STEP] v0.7 Updated TEAM_GUIDE + README with tech stack and added .gitignore for clean GitHub deployment. @ 2025-11-15T18:56:00.000Z
[STEP] v0.8 Added "Getting Started for Teammates" guide to README.md @ 2025-11-17T05:10:16.000Z
[STEP] v0.8 Improved build_answer_for_query for richer explanations (no LLM). - 2025-11-27T15:10:24.246Z
[STEP] v0.9 Added severity evaluation script + labeled sample set. - 2025-11-27T15:48:07.110Z
[STEP] v1.0 Tuned severity rules & thresholds using labeled test set (evaluate_severity.py). - 2025-11-27T16:05:11.073Z
[STEP] v1.1 Added test_full_flow.py for end-to-end pipeline sanity checking. - 2025-11-27T16:11:24.531Z
[STEP] v2.0 Added Gemini-powered /query_llm endpoint (LLM explanations on top of RAG + severity).