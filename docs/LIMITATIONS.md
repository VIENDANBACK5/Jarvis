# JARVIS SYSTEM LIMITATIONS & KNOWN DEBT (v1.0)

This document records the empirical limitations identified during Sprint 23.9 Final (JARV) audit.

---

## 1. Memory Subsystem Limitations
* **Keyword Matching**: Retrieval uses Jaccard keyword overlap. Querying with technical synonyms (e.g. `JWT token expired` vs `authentication failure`) fails to retrieve past trajectories.
* **Lack of Temporal Decay**: Older principles retain equal weight to newer principles unless manually evicted.

## 2. Agent Topology Limitations
* **Monolithic Coordinator**: All planning, execution, and critiquing pass through a single LangGraph coordinator node rather than decoupled, concurrent sub-agent roles.

## 3. World Model Limitations
* **Static AST Only**: AST parsing cannot resolve dynamic dynamic Python dispatch (`getattr()`, factory patterns, DI containers) or runtime memory leaks.

## 4. Research Agent Limitations
* **Simulated Paper DB**: Queries static local `papers.json` instead of live arXiv/Semantic Scholar RAG endpoints.
