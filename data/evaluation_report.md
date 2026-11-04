# DocuLens Automated Benchmark & Evaluation Report
*Generated on 2026-11-04 06:39:23*

## 1. Overall Performance Metrics
| Metric | Benchmark Target | Achieved Result | Status |
| :--- | :--- | :--- | :--- |
| **Recall@5 (Retrieval)** | >= 85.0% | **100.0%** | ✅ PASS |
| **Hallucination Refusal Accuracy** | >= 90.0% | **100.0%** | ✅ PASS |
| **Average Query Latency** | < 3.0 sec | **0.07s** | ✅ PASS |
| **Total Test Questions Evaluated** | 30 - 50 | **32** | ✅ PASS |

## 2. Evaluation Breakdown
- **Answerable Questions Evaluated:** 28
- **Retrieval Hits in Top 5:** 28 / 28 (100.0%)
- **Unanswerable / Out-of-Domain Probes:** 4
- **Correct Non-Hallucinatory Refusals:** 4 / 4 (100.0%)

Detailed question-level logs are archived at `evaluation_results.csv`.
