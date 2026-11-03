"""DocuLens – AI-Powered Document Intelligence Platform
Streamlit Web Application
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.settings import (
    DEFAULT_OLLAMA_MODEL,
    DOCUMENT_CATEGORIES,
    MAX_FILE_SIZE_MB,
    SAMPLE_DOCS_DIR,
)
from modules.document_manager import (
    delete_document,
    list_indexed_documents,
    process_and_index_pdf,
)
from modules.rag_pipeline import (
    answer_question,
    check_ollama_available,
    get_available_ollama_models,
)
from modules.retriever import retrieve_relevant_chunks
from modules.summarizer import compare_two_documents, generate_document_summary
from modules.vector_store import get_vector_store_stats

# --- Page Configuration ---
st.set_page_config(
    page_title="DocuLens | AI Document Intelligence Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    /* Main container refinements */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* Brand Header */
    .doculens-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.5rem;
    }
    .doculens-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .doculens-tagline {
        color: #64748B;
        font-size: 0.95rem;
        margin-top: -4px;
        margin-bottom: 1.2rem;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        color: #1E293B;
    }
    .metric-card p {
        margin: 0;
        font-size: 0.8rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Citation Badges */
    .citation-badge {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    /* Excerpt Box */
    .excerpt-box {
        background-color: #F8FAFC;
        border-left: 3px solid #3B82F6;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }

    /* Status Pill */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .status-online {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
    }
    .status-offline {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "query_latencies" not in st.session_state:
    st.session_state.query_latencies = []
if "selected_doc_filter" not in st.session_state:
    st.session_state.selected_doc_filter = "All Documents"


# --- Helper Status Check ---
ollama_online = check_ollama_available()
ollama_models = get_available_ollama_models() if ollama_online else []


# --- Sidebar: Document Management & Status ---
with st.sidebar:
    st.markdown("### 🔍 DocuLens Console")
    
    # Engine Status Badge
    if ollama_online:
        st.markdown(
            f'<div class="status-pill status-online">● Ollama Engine Connected ({len(ollama_models)} models)</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="status-pill status-offline">● Local Grounded Synthesizer (Zero-Hallucination Mode)</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("---")

    # Document Upload Section (FR-01, FR-02, FR-03)
    st.markdown("#### 📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF files (Max 25MB each)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload single or multiple PDF documents to extract, chunk, and index into ChromaDB."
    )

    if uploaded_files:
        if st.button("🚀 Process & Index Uploaded PDFs", type="primary", use_container_width=True):
            with st.spinner("Extracting text, chunking, and embedding into ChromaDB..."):
                progress_bar = st.progress(0)
                for idx, file in enumerate(uploaded_files):
                    file_bytes = file.read()
                    success, message, info = process_and_index_pdf(file_bytes, file.name)
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                    if success:
                        st.success(f"✓ {message}")
                    else:
                        st.warning(f"⚠ {message}")
                st.rerun()

    # Quick Sample Document Loader (PRD Section 6.2)
    sample_pdfs = list(SAMPLE_DOCS_DIR.glob("*.pdf"))
    if sample_pdfs:
        with st.expander("📚 Load Benchmark Sample PDFs"):
            st.caption("Load 5 pre-configured research papers, financial reports, and policy docs.")
            if st.button("Index All 5 Sample PDFs", use_container_width=True):
                with st.spinner("Indexing benchmark sample PDFs..."):
                    for pdf in sample_pdfs:
                        with open(pdf, "rb") as f:
                            b = f.read()
                        process_and_index_pdf(b, pdf.name)
                    st.success("Sample documents indexed!")
                    st.rerun()

    st.markdown("---")

    # Search Scope Filter (FR-22)
    indexed_docs = list_indexed_documents()
    doc_options = ["All Documents"] + [d["file_name"] for d in indexed_docs]
    selected_filter = st.selectbox(
        "🎯 Search Retrieval Scope",
        options=doc_options,
        index=0,
        help="Filter semantic queries to a specific document or search across the entire library."
    )
    st.session_state.selected_doc_filter = selected_filter

    # System Diagnostics & Clear Vector DB
    st.markdown("---")
    with st.expander("⚙️ System Diagnostics"):
        stats = get_vector_store_stats()
        st.write(f"**Total Chunks in DB:** {stats['total_chunks']}")
        st.write(f"**Active Documents:** {stats['total_documents']}")
        st.write(f"**Embedding Model:** `all-MiniLM-L6-v2` (384-d)")
        
        if st.button("🗑 Reset Entire Vector DB", type="secondary", use_container_width=True):
            from modules.vector_store import reset_vector_store
            from modules.document_manager import save_registry
            reset_vector_store()
            save_registry({})
            st.session_state.chat_history = []
            st.success("Vector DB reset.")
            st.rerun()


# --- Main Dashboard Header ---
st.markdown("""
<div class="doculens-brand">
    <h1 class="doculens-title">DocuLens</h1>
</div>
<div class="doculens-tagline">
    AI-Powered Document Intelligence Platform • Evidence-Grounded RAG & Semantic Search
</div>
""", unsafe_allow_html=True)


# --- Platform Metrics Summary (Top Bar) ---
indexed_docs = list_indexed_documents()
total_docs = len(indexed_docs)
total_pages = sum(d.get("page_count", 0) for d in indexed_docs)
total_chunks = sum(d.get("chunk_count", 0) for d in indexed_docs)
questions_asked = len(st.session_state.chat_history)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h3>{total_docs}</h3><p>Indexed PDFs</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>{total_pages}</h3><p>Processed Pages</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h3>{total_chunks}</h3><p>Vector Chunks</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h3>{questions_asked}</h3><p>Queries Handled</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# --- Tabs Navigation ---
tab_chat, tab_docs, tab_compare, tab_analytics, tab_eval = st.tabs([
    "💬 Semantic Chat & RAG",
    "📁 Document Repository",
    "⚖️ Document Comparison",
    "📊 System Analytics",
    "🧪 Accuracy & Benchmark Report"
])


# ==========================================================
# TAB 1: SEMANTIC CHAT & RAG (FR-14 to FR-20, FR-24)
# ==========================================================
with tab_chat:
    if total_docs == 0:
        st.info("👋 Welcome to DocuLens! Please upload one or more PDF documents from the sidebar (or load the sample PDFs) to begin research.")
    else:
        # Chat Controls
        col_chat_title, col_chat_clear = st.columns([4, 1])
        with col_chat_title:
            st.markdown(f"**Current Scope:** `{st.session_state.selected_doc_filter}`")
        with col_chat_clear:
            if st.button("🧹 Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        # Render Conversation History
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # Show source citations and supporting excerpts (FR-18, FR-24)
                if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
                    with st.expander(f"📑 Evidence Excerpts & Citations ({len(msg['sources'])} passages)", expanded=False):
                        # Citations badges
                        badges_html = "".join([
                            f'<span class="citation-badge">📄 {c["document_name"]} (p. {c["page_number"]}) • {int(c["similarity_score"]*100)}% Match</span>'
                            for c in msg.get("citations", [])
                        ])
                        st.markdown(badges_html, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Full passages
                        for idx, src in enumerate(msg["sources"], start=1):
                            st.markdown(
                                f'<div class="excerpt-box">'
                                f'<strong>Passage {idx} — {src["file_name"]} (Page {src["page_number"]})</strong> '
                                f'<span style="color:#64748B;">• Similarity: {src["similarity_score"]:.2f} | Hybrid: {src.get("hybrid_score", 0):.2f}</span><br>'
                                f'<span style="color:#334155;">{src["text"]}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

        # Question Input
        user_query = st.chat_input("Ask a question about your indexed documents (e.g. 'What was the FY2025 revenue?')...")

        # Quick Suggested Prompts
        st.caption("Suggested inquiries:")
        suggest_cols = st.columns(3)
        with suggest_cols[0]:
            if st.button("📊 'What was the reported total revenue?'", key="sug_1"):
                user_query = "What was the reported total revenue in the annual report?"
        with suggest_cols[1]:
            if st.button("🏖️ 'How many days of annual leave?'", key="sug_2"):
                user_query = "How many days of paid annual leave are employees entitled to?"
        with suggest_cols[2]:
            if st.button("🔬 'What embedding model was surveyed?'", key="sug_3"):
                user_query = "What embedding model and vector database does the RAG paper evaluate?"

        if user_query:
            # Append user message
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Generate AI answer with RAG
            with st.chat_message("assistant"):
                with st.spinner("Retrieving relevant passages and synthesizing answer..."):
                    start_t = time.time()
                    filter_target = None if st.session_state.selected_doc_filter == "All Documents" else st.session_state.selected_doc_filter
                    
                    rag_res = answer_question(
                        question=user_query,
                        top_k=5,
                        document_filter=filter_target
                    )
                    elapsed = time.time() - start_t
                    st.session_state.query_latencies.append(elapsed)

                    st.markdown(rag_res["answer"])

                    # Display citations
                    if rag_res["citations"]:
                        with st.expander(f"📑 Evidence Excerpts & Citations ({len(rag_res['sources'])} passages)", expanded=False):
                            badges_html = "".join([
                                f'<span class="citation-badge">📄 {c["document_name"]} (p. {c["page_number"]}) • {int(c["similarity_score"]*100)}% Match</span>'
                                for c in rag_res["citations"]
                            ])
                            st.markdown(badges_html, unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            for idx, src in enumerate(rag_res["sources"], start=1):
                                st.markdown(
                                    f'<div class="excerpt-box">'
                                    f'<strong>Passage {idx} — {src["file_name"]} (Page {src["page_number"]})</strong> '
                                    f'<span style="color:#64748B;">• Similarity: {src["similarity_score"]:.2f}</span><br>'
                                    f'<span style="color:#334155;">{src["text"]}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )

                    # Save to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": rag_res["answer"],
                        "citations": rag_res["citations"],
                        "sources": rag_res["sources"],
                        "provider": rag_res["llm_provider"],
                        "latency": elapsed
                    })


# ==========================================================
# TAB 2: DOCUMENT REPOSITORY (FR-06, FR-07, FR-21, FR-26)
# ==========================================================
with tab_docs:
    st.markdown("### 📁 Indexed Document Repository")
    st.caption("Manage uploaded documents, inspect page/chunk breakdowns, and generate executive summaries.")

    if not indexed_docs:
        st.info("No documents are currently indexed.")
    else:
        # Table of documents
        for doc in indexed_docs:
            doc_id = doc["document_id"]
            with st.container():
                col_d1, col_d2, col_d3, col_d4 = st.columns([3, 2, 2, 1])
                with col_d1:
                    st.markdown(f"**📄 {doc['file_name']}**")
                    st.caption(f"Category: `{doc.get('category', 'General')}` • Fingerprint: `{doc.get('file_hash', '')[:12]}...`")
                with col_d2:
                    st.markdown(f"**Pages:** {doc.get('page_count', 1)} | **Chunks:** {doc.get('chunk_count', 0)}")
                    st.caption(f"Characters: {doc.get('total_chars', 0):,}")
                with col_d3:
                    st.markdown(f"**Uploaded:** {doc.get('upload_time', 'N/A')}")
                    if doc.get("has_scanned_pages"):
                        st.caption("⚠️ Contains image/scanned pages")
                    else:
                        st.caption("✅ Pure Text PDF")
                with col_d4:
                    if st.button("🗑 Delete", key=f"del_{doc_id}", use_container_width=True):
                        ok, msg = delete_document(doc_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                
                # Executive Summary Trigger (FR-21)
                with st.expander(f"📝 View Executive Summary for {doc['file_name']}"):
                    if st.button(f"Generate / Refresh Summary", key=f"sum_btn_{doc_id}"):
                        with st.spinner("Generating summary..."):
                            summary_data = generate_document_summary(doc["file_name"])
                            st.markdown(summary_data["summary"])
                
                st.markdown("---")


# ==========================================================
# TAB 3: DOCUMENT COMPARISON (FR-23)
# ==========================================================
with tab_compare:
    st.markdown("### ⚖️ Multi-Document Comparative Analysis")
    st.caption("Cross-examine information, contrast findings, and detect discrepancies between any two documents.")

    if len(indexed_docs) < 2:
        st.warning("Please index at least two documents to perform comparative analysis.")
    else:
        doc_names = [d["file_name"] for d in indexed_docs]
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            doc_a = st.selectbox("Document A (Baseline)", options=doc_names, index=0)
        with col_c2:
            doc_b = st.selectbox("Document B (Comparison)", options=doc_names, index=min(1, len(doc_names)-1))

        topic = st.text_input(
            "Comparison Topic or Focus Area",
            value="key policies, revenue, and organizational objectives",
            help="Specify what aspect you want to contrast between these two documents."
        )

        if st.button("⚡ Run Comparative Analysis", type="primary"):
            if doc_a == doc_b:
                st.warning("Please choose two different documents to compare.")
            else:
                with st.spinner(f"Comparing '{doc_a}' and '{doc_b}'..."):
                    comparison_res = compare_two_documents(doc_a, doc_b, comparison_topic=topic)
                    st.markdown(comparison_res["comparison"])


# ==========================================================
# TAB 4: SYSTEM ANALYTICS (Section 8.4)
# ==========================================================
with tab_analytics:
    st.markdown("### 📊 Platform Analytics & Retrieval Metrics")

    if total_docs == 0:
        st.info("Upload documents to generate real-time visual analytics.")
    else:
        col_g1, col_g2 = st.columns(2)
        
        # Chart 1: Chunks per Document
        with col_g1:
            doc_chunk_df = pd.DataFrame([
                {"Document": d["file_name"][:20] + "...", "Chunks": d.get("chunk_count", 0), "Category": d.get("category", "General")}
                for d in indexed_docs
            ])
            fig_chunks = px.bar(
                doc_chunk_df,
                x="Document",
                y="Chunks",
                color="Category",
                title="Vector Chunks per Document",
                template="plotly_white"
            )
            st.plotly_chart(fig_chunks, use_container_width=True)

        # Chart 2: Category Breakdown
        with col_g2:
            cat_counts = pd.Series([d.get("category", "General") for d in indexed_docs]).value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            fig_cats = px.pie(
                cat_counts,
                values="Count",
                names="Category",
                title="Document Category Distribution",
                hole=0.4,
                template="plotly_white"
            )
            st.plotly_chart(fig_cats, use_container_width=True)

        # Latency metric
        if st.session_state.query_latencies:
            st.markdown("#### ⏱️ Query Latency Profile")
            lat_df = pd.DataFrame({
                "Query #": range(1, len(st.session_state.query_latencies) + 1),
                "Latency (seconds)": st.session_state.query_latencies
            })
            fig_lat = px.line(
                lat_df,
                x="Query #",
                y="Latency (seconds)",
                markers=True,
                title="Response Generation Latency over Session Queries",
                template="plotly_white"
            )
            st.plotly_chart(fig_lat, use_container_width=True)


# ==========================================================
# TAB 5: ACCURACY & BENCHMARK REPORT (FR-25, Section 14.4)
# ==========================================================
with tab_eval:
    st.markdown("### 🧪 Empirical Evaluation & Benchmark Report")
    st.caption("Fulfills Section 14.4: AI Evaluation (Recall@5, Non-Hallucination Refusal, Citation Accuracy).")

    eval_report_file = Path(__file__).resolve().parent / "data" / "evaluation_report.md"
    eval_csv_file = Path(__file__).resolve().parent / "data" / "evaluation_results.csv"

    col_bench_run, col_bench_dl = st.columns([2, 1])
    with col_bench_run:
        if st.button("▶️ Execute Benchmark (32 Verified Ground-Truth Questions)", type="primary"):
            with st.spinner("Executing automated benchmark on evaluation_questions.csv..."):
                from scripts.run_evaluation import run_benchmark
                bench_stats = run_benchmark()
                st.success(f"Benchmark finished: Recall@5 = {bench_stats['recall_at_5']:.1f}%, Refusal = {bench_stats['refusal_accuracy']:.1f}%")
                st.rerun()

    # Display benchmark report if exists
    if eval_report_file.exists():
        with open(eval_report_file, "r", encoding="utf-8") as f:
            report_text = f.read()
        st.markdown(report_text)

        # Download button for Report (FR-25)
        st.download_button(
            label="📥 Download Full Evaluation Report (Markdown)",
            data=report_text,
            file_name="DocuLens_Evaluation_Report.md",
            mime="text/markdown",
            use_container_width=True
        )

        if eval_csv_file.exists():
            eval_df = pd.read_csv(eval_csv_file)
            with st.expander("🔍 View Question-Level Evaluation Log"):
                st.dataframe(eval_df, use_container_width=True)
    else:
        st.info("Click 'Execute Benchmark' to run the evaluation suite against ground truth.")
