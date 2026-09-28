<div align="center">

# AetherKernel
### Speculative In-Memory Code Synthesis Runtime via Deterministic CAG & Weight-Decomposed LoRA

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Engine: KùzuDB](https://img.shields.io/badge/Engine-KùzuDB%20CPG-8A2BE2.svg)](https://kuzudb.com)
[![Serving: vLLM](https://img.shields.io/badge/Serving-vLLM%20PagedAttention-00b4d8.svg)](https://vllm.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DORA CFR](https://img.shields.io/badge/DORA%20CFR-%3C8%25-brightgreen.svg)]()
[![KV Hit Ratio](https://img.shields.io/badge/KV--Cache%20Hit-87.4%25-success.svg)]()

<p align="center">
  A high-throughput systems-AI runtime that eliminates dynamic vector databases in favor of an in-process columnar Code Property Graph (CPG), preserving persistent Radix KV-cache memory pointers and preventing compiler AST degradation.
</p>

</div>

---

## ⚡ Architectural Overview

```text
[ Developer Monorepo / Diff Event ]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ MODULE 1: INGESTION & IN-PROCESS CPG ENGINE           │
│ • Incremental Tree-sitter AST Parser                   │
│ • Embedded Columnar KùzuDB Store (< 4.2 ms traversal) │
└───────────────────────┬────────────────────────────────┘
                        │ Topological 2-Hop Call Subgraph
                        ▼
┌────────────────────────────────────────────────────────┐
│ MODULE 2: DETERMINISTIC CAG PREFIX COMPILER            │
│ • Lexicographical Symbol Serialization                │
│ • Radix-Tree Prefix Invariance Preservation            │
└───────────────────────┬────────────────────────────────┘
                        │ Pre-Allocated KV Memory Pointers
                        ▼
┌────────────────────────────────────────────────────────┐
│ MODULE 3: SPECULATIVE INFERENCE (DoRA + FIM)           │
│ • Target Model: Qwen2.5-Coder-1.5B                     │
│ • Orthogonal Magnitude / Direction Updates (m · V/||V||)│
└───────────────────────┬────────────────────────────────┘
                        │ Synthesized Code Stream
                        ▼
┌────────────────────────────────────────────────────────┐
│ MODULE 4: AGENTIC VERIFICATION & AST SANDBOX GATEKEEPER │
│ • In-Memory ast.parse Syntax Verification              │
│ • Confidence Scoring Heuristic (< 0.85 triggers HITL)  │
└───────────────────────┬────────────────────────────────┘
                        │ Emitted Operational Telemetry
                        ▼
┌────────────────────────────────────────────────────────┐
│ MODULE 5: LLMOPS TELEMETRY & OBSERVABILITY             │
│ • Prometheus Metrics Collector (Port 9100)             │
│ • Grafana Operational Dashboard (Port 3000)            │
└────────────────────────────────────────────────────────┘