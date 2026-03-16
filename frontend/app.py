import streamlit as st
import httpx
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8001")

st.set_page_config(
    page_title="DRIPE — Drug Repurposing Intelligence Engine",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark background */
.stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f1629 50%, #0a0e1a 100%); }

/* Disclaimer banner */
.disclaimer-banner {
    background: rgba(255, 180, 0, 0.08);
    border: 1px solid rgba(255, 180, 0, 0.3);
    border-radius: 10px;
    padding: 12px 20px;
    font-size: 0.82rem;
    color: #f0c040;
    margin-bottom: 1.5rem;
    line-height: 1.6;
}

/* Hero title */
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #6ee7f7, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-size: 1.05rem;
    color: #8892a4;
    margin-bottom: 2rem;
}

/* Coverage badge */
.coverage-box {
    background: rgba(110, 231, 247, 0.06);
    border: 1px solid rgba(110, 231, 247, 0.2);
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 1.5rem;
}
.coverage-tier-high   { color: #4ade80; font-weight: 600; }
.coverage-tier-medium { color: #facc15; font-weight: 600; }
.coverage-tier-low    { color: #f87171; font-weight: 600; }

/* Stats row */
.stat-card {
    background: rgba(167, 139, 250, 0.07);
    border: 1px solid rgba(167, 139, 250, 0.18);
    border-radius: 10px;
    padding: 14px 20px;
    text-align: center;
}
.stat-value { font-size: 1.7rem; font-weight: 700; color: #a78bfa; font-family: 'JetBrains Mono'; }
.stat-label { font-size: 0.78rem; color: #8892a4; margin-top: 4px; }

/* Hypothesis card */
.hyp-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 22px 28px;
    margin-bottom: 14px;
    transition: border 0.2s;
}
.hyp-card:hover { border-color: rgba(110, 231, 247, 0.35); }

.tier-strong     { background:#166534; color:#86efac; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.tier-moderate   { background:#854d0e; color:#fde68a; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.tier-exploratory{ background:#7c3aed; color:#ddd6fe; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }

/* Sidebar */
section[data-testid="stSidebar"] > div:first-child {
    background: rgba(15, 22, 41, 0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* Button */
.stButton > button {
    background: linear-gradient(90deg, #6ee7f7, #a78bfa) !important;
    color: #0a0e1a !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 2rem !important;
    width: 100%;
    font-size: 1rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Empty state */
.empty-state {
    text-align: center;
    color: #4b5563;
    padding: 60px 20px;
    font-size: 1rem;
}
.empty-state .icon { font-size: 3rem; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def tier_badge(tier: str) -> str:
    mapping = {
        "STRONG_EVIDENCE": '<span class="tier-strong">● Strong Evidence</span>',
        "MODERATE":        '<span class="tier-moderate">● Moderate</span>',
        "EXPLORATORY":     '<span class="tier-exploratory">● Exploratory</span>',
    }
    return mapping.get(tier, f'<span>{tier}</span>')

def tier_css(tier: str) -> str:
    return {"HIGH": "coverage-tier-high", "MEDIUM": "coverage-tier-medium", "LOW": "coverage-tier-low"}.get(tier, "")

def run_query(disease: str, confidence: float, exploratory: bool):
    try:
        with st.spinner("🔬 Traversing knowledge graph and retrieving literature..."):
            response = httpx.post(
                f"{API_URL}/query",
                json={"disease": disease, "min_confidence": confidence, "include_exploratory": exploratory},
                timeout=70.0
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code in (400, 403, 408):
                st.error(f"⚠️ {response.json().get('detail', 'Request blocked.')}")
            else:
                st.error(f"API Error {response.status_code}: {response.text[:300]}")
    except httpx.ConnectError:
        st.error("❌ Cannot connect to API. Is the backend running on port 8001?")
    except Exception as e:
        st.error(f"Error: {e}")
    return None


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧬 DRIPE")
    st.markdown("<small style='color:#8892a4'>Drug Repurposing Intelligence Engine</small>", unsafe_allow_html=True)
    st.divider()
    st.markdown("#### Search Parameters")
    disease_input = st.text_input(
        "Disease / Gene / Pathway",
        placeholder="e.g. Alzheimer's Disease",
        label_visibility="collapsed"
    )
    st.caption("Enter a disease name, gene symbol, or biological pathway.")
    st.markdown("")
    min_conf = st.slider("Min Confidence Threshold", 0.30, 0.99, 0.50, 0.01,
                         help="Filter out edges below this confidence level")
    exploratory = st.checkbox("Include Exploratory Results",
                               help="Show low-confidence candidates tagged EXPLORATORY")
    st.markdown("")
    submit = st.button("🔭 Generate Hypothesis")
    st.divider()
    # Health Status
    try:
        health = httpx.get(f"{API_URL}/health", timeout=3).json()
        services = health.get("services", {})
        st.markdown("**Service Status**")
        for svc, status in services.items():
            dot = "🟢" if status == "up" else "🔴"
            st.caption(f"{dot} {svc.title()}")
    except Exception:
        st.caption("🔴 API unreachable")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">DRIPE</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Drug Repurposing Intelligence Engine — agentic knowledge graph reasoning pipeline</div>',
            unsafe_allow_html=True)

# Mandatory disclaimer
st.markdown("""
<div class="disclaimer-banner">
⚠️ <strong>RESEARCH USE ONLY.</strong> This output is a computational hypothesis. It has not been validated
through in vitro experiments, animal studies, or clinical trials. It does not constitute medical advice and
must not be used to inform treatment decisions for any patient.
</div>
""", unsafe_allow_html=True)

if submit and disease_input:
    results = run_query(disease_input, min_conf, exploratory)

    if results:
        cov = results.get("coverage_report", {})
        tier = cov.get("completeness_tier", "N/A")

        # ── Coverage Banner ────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="coverage-box">
            <strong>📊 Data Coverage:</strong>
            <span class="{tier_css(tier)}">{tier}</span>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            Genes: <strong>{cov.get("gene_association_count", 0)}</strong>
            &nbsp;·&nbsp;
            Proteins: <strong>{cov.get("protein_interaction_count", 0)}</strong>
            &nbsp;·&nbsp;
            Papers: <strong>{cov.get("pubmed_paper_count", 0)}</strong>
            &nbsp;·&nbsp;
            Trials: <strong>{cov.get("trial_count", 0)}</strong>
        </div>
        """, unsafe_allow_html=True)

        candidates = results.get("candidates", [])

        # ── Stats Row ──────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-card"><div class="stat-value">{len(candidates)}</div><div class="stat-label">Candidates Found</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card"><div class="stat-value">{cov.get("pubmed_paper_count", 0)}</div><div class="stat-label">PubMed Papers</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-card"><div class="stat-value">{cov.get("trial_count", 0)}</div><div class="stat-label">Clinical Trials</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="stat-card"><div class="stat-value">{results.get("graph_version", "—")}</div><div class="stat-label">Graph Version</div></div>', unsafe_allow_html=True)

        st.markdown("")
        st.markdown(f"### Hypothesis Results for `{results.get('query_disease')}`")

        if not candidates:
            st.markdown("""
            <div class="empty-state">
                <div class="icon">🔬</div>
                <strong>No candidates yet</strong><br/>
                The knowledge graph and GNN pipeline are still being populated.<br/>
                Data ingestion from RTX-KG2, ChEMBL, and PubMed OA is the next step.
            </div>
            """, unsafe_allow_html=True)
        else:
            for cand in candidates:
                with st.expander(f"#{cand['rank']}  {cand['drug_name']}  —  {cand['confidence_tier']}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(tier_badge(cand["confidence_tier"]), unsafe_allow_html=True)
                        st.markdown(f"**Drug ID:** `{cand.get('drug_id', 'N/A')}`  |  **Status:** {cand.get('approval_status', 'N/A')}")
                        st.markdown("**Reasoning Chain:**")
                        for step in cand.get("reasoning_chain", []):
                            st.markdown(f"> **Step {step['step_number']}** — {step['claim']}  *(Source: {step['source_database_or_pmid']})*")
                    with col2:
                        st.metric("GNN Score", f"{cand.get('gnn_similarity_score', 0):.2f}")
                        st.metric("Graph Confidence", f"{cand.get('graph_path_confidence', 0):.2f}")
                        st.metric("Equity Weight", f"{cand.get('equity_weight', 0):.3f}")
                    if cand.get("safety_flags"):
                        st.warning(f"⚠️ Safety Flags: {', '.join(cand['safety_flags'])}")
                    if cand.get("next_steps"):
                        st.info(f"🔬 **Next Steps:** {cand['next_steps']}")

        # Footer disclaimer
        st.divider()
        st.caption(results.get("disclaimer", ""))

elif not submit:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🧬</div>
        <strong>Enter a disease name in the sidebar to begin</strong><br/>
        <small>e.g. Alzheimer's Disease &nbsp;·&nbsp; Parkinson's Disease &nbsp;·&nbsp; Glioblastoma</small>
    </div>
    """, unsafe_allow_html=True)
