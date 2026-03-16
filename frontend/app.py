import streamlit as st
import httpx
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="DRIPE - Drug Repurposing Engine", layout="wide")

# Persistent Disclaimer
st.warning("⚠️ RESEARCH USE ONLY. This system is for research purposes and does not provide medical advice.")

def run_query(disease: str, confidence: float):
    try:
        with st.spinner("Analyzing Knowledge Graph and Literature..."):
            response = httpx.post(
                f"{API_URL}/query", 
                json={"disease": disease, "min_confidence": confidence},
                timeout=70.0
            )
            return response.json()
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

def main():
    st.title("🧬 DRIPE: Drug Repurposing Intelligence Engine")
    st.write("Cross-domain agentic pipeline for hypothesis generation.")
    
    with st.sidebar:
        st.header("Search Parameters")
        disease_input = st.text_input("Disease / Pathway Name", placeholder="e.g. Alzheimer's Disease")
        min_conf = st.slider("Min Confidence Threshold", 0.30, 0.99, 0.50)
        exploratory = st.checkbox("Include Exploratory Results")
        submit = st.button("Generate Hypothesis")

    if submit and disease_input:
        results = run_query(disease_input, min_conf)
        if results:
            if "detail" in results:
                st.error(results["detail"])
            else:
                st.header(f"Results for: {results['query_disease']}")
                # Render coverage badge
                cov = results['coverage_report']
                st.info(f"Data Coverage: {cov['completeness_tier']} (Papers: {cov['pubmed_paper_count']})")
                
                # Render candidates
                for cand in results.get('candidates', []):
                    with st.expander(f"{cand['drug_name']} - Confidence: {cand['confidence_tier']}"):
                        st.write(cand['next_steps'])

if __name__ == "__main__":
    main()
