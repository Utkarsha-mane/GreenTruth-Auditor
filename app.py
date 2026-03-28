import streamlit as st
from engine import GreenAuditorEngine
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Green-Truth Auditor", layout="wide", page_icon="🌱")

@st.cache_resource
def load_engine(): return GreenAuditorEngine()
engine = load_engine()


st.markdown("""
<style>
    .fact-box { border-left: 5px solid #28a745; background-color: #f8fff9; padding: 10px; margin: 5px 0; border-radius: 5px; }
    .unverified-box { border-left: 5px solid #ffc107; background-color: #fffdf2; padding: 10px; margin: 5px 0; border-radius: 5px; }
    .vague-box { border-left: 5px solid #dc3545; background-color: #fff9f9; padding: 10px; margin: 5px 0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Session State for persistency
if "audit_data" not in st.session_state: st.session_state.audit_data = None

# Sidebar Navigation
with st.sidebar:
    st.title("🌱 G-T Intelligence")
    tab = st.radio("Navigation", ["Auditor Workspace", "Risk Analysis", "Brand Deep-Dive"])
    st.divider()
    st.image("https://cdn-icons-png.flaticon.com/512/2950/2950143.png", width=80)

# --- TAB 1: WORKSPACE ---
if tab == "Auditor Workspace":
    st.title("🛡️ Claim Audit Workspace")
    source = st.selectbox("Source Type", ["Website Scraper", "PDF Document", "Manual Text"])
    
    user_input = ""
    if source == "Website Scraper":
        url = st.text_input("Product/Report URL:")
        if url: user_input = engine.scrape_url(url)
    elif source == "PDF Document":
        uploaded = st.file_uploader("Upload Sustainability Report", type="pdf")
        if uploaded: user_input = engine.process_pdf(uploaded)
    else:
        user_input = st.text_area("Paste text here:", height=200)

    if st.button("🚀 INITIATE ANALYSIS", type="primary"):
        if user_input:
            with st.spinner("Executing Intelligence Layers..."):
                st.session_state.audit_data = engine.run_audit(user_input)
        else: st.error("No input found.")

    if st.session_state.audit_data:
        res = st.session_state.audit_data
        if res.get('status') == "success":
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Green-Wash Index", f"{res['gwi']}%", "High Risk" if res['gwi'] > 50 else "Trusted", delta_color="inverse")
            c2.metric("Verified Status", "B-CORP" if res['has_cert'] else "UNVERIFIED")
            c3.metric("Significant Claims", len(res['audit_ledger']))

            st.subheader("📝 Sentence-Level Audit Ledger")
            for s in res['audit_ledger']:
                if s['category'] == "Fact": st.markdown(f'<div class="fact-box"><b>[FACT]</b> {s["text"]}</div>', unsafe_allow_html=True)
                elif s['category'] == "Unverified": st.markdown(f'<div class="unverified-box"><b>[UNVERIFIED]</b> {s["text"]}</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="vague-box"><b>[VAGUE]</b> {s["text"]}</div>', unsafe_allow_html=True)

# --- TAB 2: RISK ANALYSIS ---
elif tab == "Risk Analysis":
    st.title("🔬 Linguistic & Semantic Risk Breakdown")
    if st.session_state.audit_data:
        res = st.session_state.audit_data
        col_l, col_r = st.columns(2)
        with col_l:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = res['gwi'],
                title = {'text': "Green-Wash Index Risk Level"},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#e74c3c" if res['gwi'] > 50 else "#2ecc71"}}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
        with col_r:
            categories = [s['category'] for s in res['audit_ledger']]
            fig_pie = px.pie(names=categories, title="Distribution of Climate Claims", hole=.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            st.write(f"Identified **{res['buzz_count']}** flagged buzzwords.")
    else: st.info("Run an audit first.")

# --- TAB 3: DEEP-DIVE ---
elif tab == "Brand Deep-Dive":
    st.title("📊 Verified Performance Radar")
    
    if st.session_state.audit_data:
        res = st.session_state.audit_data
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Industry Benchmark Analysis")
            # Logic for Benchmarking
            industry = res['brand_data']['industry'] if res['has_cert'] else "Technology"
            bench = engine.get_industry_averages(industry)
            
            fig = go.Figure()
            # Industry Baseline
            fig.add_trace(go.Scatterpolar(
                r=[bench['avg_env'], bench['avg_prac'], bench['avg_out'], bench['avg_in'], bench['avg_overall']],
                theta=['Env Score','Practices','Outputs','Inputs','Overall Avg'],
                fill='toself', name=f"Industry Standard ({industry})", line=dict(color='gray', dash='dash')
            ))
            
            # Brand Performance 
            if res['has_cert']:
                d = res['brand_data']
                def v(x): 
                    try: return float(x) if str(x).replace('.','').isdigit() else 0
                    except: return 0
                fig.add_trace(go.Scatterpolar(
                    r=[v(d['environment_score']), v(d['environment_practices']), v(d['environment_outputs']), v(d['environment_inputs']), v(d['overall_score'])/2],
                    theta=['Env Score','Practices','Outputs','Inputs','Overall'],
                    fill='toself', name=res['brand_name'], line=dict(color='#1abc9c')
                ))
            else:
                est = 100 - res['gwi']
                fig.add_trace(go.Scatterpolar(
                    r=[est]*5, theta=['Env Score','Practices','Outputs','Inputs','Overall'],
                    fill='toself', name="Claim-Based Trust Estimate", line=dict(color='#e74c3c')
                ))
                
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Audit Intelligence")
            
            if res['has_cert']:
                st.success(f"**Verification Confirmed:** {res['brand_name']} matches B-Corp data.")
                st.write(f"**Verified Industry:** {res['brand_data']['industry']}")
            else:
                st.warning("⚠️ **Non-Certified Brand Detected.**")
                st.write("This brand is not in the certified B-Corp database. We are comparing their claims against the verified 'Sustainability Standard' for their industry.")
            st.info("The Radar Chart visualizes the 'Proof Gap'. If the claims in the report (Audit Ledger) are high but the verified scores (Radar) are low, the brand is flagged for high-risk reporting.")