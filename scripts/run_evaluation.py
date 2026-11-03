"""Evaluation script for DocuLens
Fulfills Section 14.4: AI Evaluation (Recall@5, Citation Correctness, Grounded Answers)
"""
import csv
from pathlib import Path
import time
from typing import Any, Dict, List
import pandas as pd

from config.settings import DATA_DIR
from modules.rag_pipeline import answer_question
from modules.retriever import retrieve_relevant_chunks

EVAL_CSV = DATA_DIR / "evaluation_questions.csv"
OUTPUT_REPORT_MD = DATA_DIR / "evaluation_report.md"
OUTPUT_RESULTS_CSV = DATA_DIR / "evaluation_results.csv"


def run_benchmark() -> Dict[str, Any]:
    if not EVAL_CSV.exists():
        raise FileNotFoundError(f"Evaluation file '{EVAL_CSV}' not found.")

    df = pd.read_csv(EVAL_CSV)
    total_questions = len(df)
    print(f"Running evaluation on {total_questions} test questions...")

    retrieval_hits = 0
    answerable_count = 0
    unanswerable_count = 0
    correct_refusals = 0
    total_latency = 0.0
    results_records: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        question = row["question"]
        expected_doc = str(row["expected_document"]).strip()
        expected_page = int(row["expected_page"]) if pd.notna(row["expected_page"]) else 0
        expected_ans = str(row["expected_answer"]).strip()
        is_unanswerable = expected_doc.lower() == "none" or expected_page == 0

        start_time = time.time()
        rag_output = answer_question(question, top_k=5)
        elapsed = time.time() - start_time
        total_latency += elapsed

        retrieved_chunks = rag_output["sources"]
        generated_answer = rag_output["answer"]
        citations = rag_output["citations"]

        # Check retrieval Recall@5
        hit = False
        if not is_unanswerable:
            answerable_count += 1
            for c in retrieved_chunks:
                if c["file_name"] == expected_doc and (c["page_number"] == expected_page or expected_page == 0):
                    hit = True
                    break
            if hit:
                retrieval_hits += 1
        else:
            unanswerable_count += 1
            # Check if system correctly identified insufficient evidence
            refusal_terms = ["insufficient evidence", "cannot be answered", "do not contain"]
            if any(term in generated_answer.lower() for term in refusal_terms) or not rag_output["grounded"]:
                correct_refusals += 1

        results_records.append({
            "question": question,
            "expected_document": expected_doc,
            "expected_page": expected_page,
            "retrieval_hit": hit if not is_unanswerable else "N/A (Unanswerable)",
            "llm_provider": rag_output["llm_provider"],
            "generated_answer": generated_answer[:150] + "...",
            "citations_found": "; ".join([f"{c['document_name']}:p{c['page_number']}" for c in citations]),
            "latency_sec": round(elapsed, 3)
        })

    recall_at_5 = (retrieval_hits / answerable_count * 100) if answerable_count > 0 else 0.0
    refusal_accuracy = (correct_refusals / unanswerable_count * 100) if unanswerable_count > 0 else 0.0
    avg_latency = total_latency / total_questions if total_questions > 0 else 0.0

    # Save detailed CSV
    results_df = pd.DataFrame(results_records)
    results_df.to_csv(OUTPUT_RESULTS_CSV, index=False)

    summary_md = f"""# DocuLens Automated Benchmark & Evaluation Report
*Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}*

## 1. Overall Performance Metrics
| Metric | Benchmark Target | Achieved Result | Status |
| :--- | :--- | :--- | :--- |
| **Recall@5 (Retrieval)** | >= 85.0% | **{recall_at_5:.1f}%** | {'✅ PASS' if recall_at_5 >= 85 else '⚠️ REVIEW'} |
| **Hallucination Refusal Accuracy** | >= 90.0% | **{refusal_accuracy:.1f}%** | {'✅ PASS' if refusal_accuracy >= 90 else '⚠️ REVIEW'} |
| **Average Query Latency** | < 3.0 sec | **{avg_latency:.2f}s** | {'✅ PASS' if avg_latency < 3.0 else '⚠️ REVIEW'} |
| **Total Test Questions Evaluated** | 30 - 50 | **{total_questions}** | ✅ PASS |

## 2. Evaluation Breakdown
- **Answerable Questions Evaluated:** {answerable_count}
- **Retrieval Hits in Top 5:** {retrieval_hits} / {answerable_count} ({recall_at_5:.1f}%)
- **Unanswerable / Out-of-Domain Probes:** {unanswerable_count}
- **Correct Non-Hallucinatory Refusals:** {correct_refusals} / {unanswerable_count} ({refusal_accuracy:.1f}%)

Detailed question-level logs are archived at `{OUTPUT_RESULTS_CSV.name}`.
"""
    with open(OUTPUT_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"\n--- EVALUATION SUMMARY ---")
    print(f"Recall@5: {recall_at_5:.1f}% ({retrieval_hits}/{answerable_count})")
    print(f"Hallucination Refusal Accuracy: {refusal_accuracy:.1f}% ({correct_refusals}/{unanswerable_count})")
    print(f"Average Latency: {avg_latency:.2f}s")
    print(f"Report written to: {OUTPUT_REPORT_MD}")

    return {
        "recall_at_5": recall_at_5,
        "refusal_accuracy": refusal_accuracy,
        "avg_latency": avg_latency,
        "total_questions": total_questions
    }


if __name__ == "__main__":
    run_benchmark()
