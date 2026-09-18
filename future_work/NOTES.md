# Future Work & Deliberate Scope Cuts

This document records architectural extensions and deliberate scope reductions set aside during the 1-week build sprint for **SIH PS 26122: Intelligent Data Capture & Schedule-Linking Layer (Oil India Limited)**. These items are documented to ensure clear post-hackathon continuation without cluttering the critical path.

## 1. Offline Fallback Mechanisms
- **Heuristic / Regex Extractor**: A high-fidelity regex/keyword offline extraction layer for field environments experiencing zero internet connectivity.
- **TF-IDF Embedding Fallback**: A local term-frequency / cosine similarity backup engine if downloading or executing `sentence-transformers` models (`all-MiniLM-L6-v2`) is restricted by air-gapped security policies.

## 2. Audio & Vision Ingestion
- **Full Voice / ASR Time Agent**: Production-grade speech-to-text integration capable of handling regional dialects, noisy site acoustics, and offline voice caching for site supervisors.
- **OCR Pipeline for Scanned Site Diaries**: Optical character recognition with table extraction specifically trained on handwritten and physical carbon-copy site logbooks.

## 3. Advanced UI Visualizations
- **Interactive Gantt Chart View**: Dynamic SVG / WebGL interactive cascading Gantt chart with drag-and-drop baseline re-alignment, replacing the current tabular planned-vs-actual view.

## 4. Advanced Project Analytics & Machine Learning
- **Reporter Trust Scoring**: Per-contractor and per-supervisor reliability weighting based on historical dispute and planner-correction frequency.
- **Independent Operational Data Cross-Check**: Automated validation against SAP/ERP material issue records, weighbridge slips, and equipment telemetry logs.
- **Active Institutional Memory Retrieval**: Vectorized similarity search over closed project archives to recommend realistic activity durations and warn planners of recurring bottlenecks during new schedule design.
- **Bidirectional Primavera P6 / MS Project API Connectors**: Live enterprise synchronization via Oracle Primavera P6 REST APIs instead of batch schedule imports.
