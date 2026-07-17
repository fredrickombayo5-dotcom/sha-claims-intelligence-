import sys
import os
import json
import pandas as pd
import streamlit as st

# Dynamically add the skill scripts directory to sys.path to import rule_engine
sys.path.append(os.path.join(os.path.dirname(__file__),  "scripts"))
try:
    import rule_engine
except ImportError:
    st.error("Error: Could not import scripts/rule_engine.py. Please verify project structure.")

# Configure Streamlit page
st.set_page_config(
    page_title="SHA Claims Pre-Submission Check",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* App layout & font styling */
    .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Sleek header gradient */
    .header-container {
        padding: 1.5rem 0rem;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(167, 139, 250, 0.05) 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        text-align: center;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #a78bfa, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #64748b;
    }
    
    /* Premium glassmorphic metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.05);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-align: center;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.1);
    }
    
    .dark .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .metric-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e1b4b;
    }
    
    .dark .metric-value {
        color: #f8fafc;
    }
    
    /* Quick guidelines styling */
    .sidebar-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #4f46e5;
        margin-bottom: 1rem;
    }
    
    .rule-box {
        border-left: 4px solid #6366f1;
        background-color: rgba(99, 102, 241, 0.05);
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        border-radius: 0 8px 8px 0;
    }
    
    .rule-title {
        font-weight: 600;
        font-size: 0.95rem;
        color: #1e1b4b;
    }
    
    .dark .rule-title {
        color: #f8fafc;
    }
    
    .rule-desc {
        font-size: 0.85rem;
        color: #475569;
    }
    
    .dark .rule-desc {
        color: #94a3b8;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Section
st.markdown(
    """
    <div class="header-container">
        <div class="main-title">SHA Claims Rejection Intelligence</div>
        <div class="subtitle">Evaluate health facility claims for rejection risks prior to submitting to the Social Health Authority</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar - Instructions & Ground Rules
with st.sidebar:
    st.markdown('<div class="sidebar-header">SHA Verification Rules</div>', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div class="rule-box">
            <div class="rule-title">Rule 1: Pre-authorization Check</div>
            <div class="rule-desc">Flags if pre-auth is required but status is not 'approved' or pre-auth number is missing.</div>
        </div>
        <div class="rule-box">
            <div class="rule-title">Rule 2: Patient Bio-data Check</div>
            <div class="rule-desc">Flags if name, DOB, SHA number, or phone is blank.</div>
        </div>
        <div class="rule-box">
            <div class="rule-title">Rule 3: Coding Mismatch Check</div>
            <div class="rule-desc">Flags if the combination of ICD-10 Diagnosis and SHA Procedure codes is invalid.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    st.subheader("Reference Schema & Template")
    st.markdown(
        """
        Input CSV should include columns:
        - `claim_id`
        - `patient_full_name`, `patient_dob`, `patient_sha_number`, `patient_phone`
        - `preauth_required`, `preauth_number`, `preauth_status`
        - `diagnosis_code`, `procedure_code`
        - `claim_amount`
        """
    )
    
    # Provide sample claims data download link
    sample_claims_path = os.path.join(os.path.dirname(__file__), "reference", "sample_claims.csv")
    if os.path.exists(sample_claims_path):
        with open(sample_claims_path, "r") as f:
            sample_csv_data = f.read()
        st.download_button(
            label="Download Template CSV",
            data=sample_csv_data,
            file_name="sha_claims_template.csv",
            mime="text/csv"
        )

# Main Body - File Upload
uploaded_file = st.file_uploader("Upload Claims CSV Export", type=["csv"], help="Upload CSV exported from KenyaEMR or billing system.")

if uploaded_file is not None:
    try:
        # Load claims dataframe
        df = pd.read_csv(uploaded_file, dtype=str)
        
        # Check required columns exist
        missing_cols = []
        required_cols = ["claim_id", "patient_full_name", "patient_dob", "patient_sha_number", "patient_phone", 
                         "preauth_required", "preauth_number", "preauth_status", "diagnosis_code", "procedure_code", "claim_amount"]
        for col in required_cols:
            if col not in df.columns:
                missing_cols.append(col)
                
        if missing_cols:
            st.error(f"Missing required columns in CSV: {', '.join(missing_cols)}")
        else:
            # Cast preauth_required back to bool-like for evaluation
            df["preauth_required"] = df["preauth_required"].apply(lambda x: str(x).strip().lower() == "true")
            
            # Run evaluation on each row
            results = df.apply(rule_engine.evaluate_claim, axis=1, result_type="expand")
            results.columns = ["risk_status", "flag_reasons", "flagged_rule_ids"]
            out_df = pd.concat([df, results], axis=1)
            
            # Cast claim_amount to numeric for calculations
            out_df["claim_amount_num"] = pd.to_numeric(out_df["claim_amount"], errors="coerce").fillna(0.0)
            
            # Drop the synthetic fail mode column if present to clean output
            if "_synthetic_failure_mode" in out_df.columns:
                out_df = out_df.drop(columns=["_synthetic_failure_mode"])
                
            # Perform calculations
            total_claims = len(out_df)
            at_risk_count = len(out_df[out_df["risk_status"] == "At Risk"])
            high_risk_count = len(out_df[out_df["risk_status"] == "High Risk"])
            
            pct_at_risk = (at_risk_count / total_claims) * 100 if total_claims > 0 else 0
            pct_high_risk = (high_risk_count / total_claims) * 100 if total_claims > 0 else 0
            
            # Amount at risk is any claim that has At Risk or High Risk
            amount_at_risk = out_df[out_df["risk_status"] != "Clean"]["claim_amount_num"].sum()
            
            # Display metrics cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Claims Ingested</div>
                        <div class="metric-value">{total_claims}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            with col2:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">% Claims At Risk</div>
                        <div class="metric-value" style="color: #f59e0b;">{pct_at_risk:.1f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            with col3:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">% Claims High Risk</div>
                        <div class="metric-value" style="color: #ef4444;">{pct_high_risk:.1f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            with col4:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">KES Amount At Risk</div>
                        <div class="metric-value" style="color: #4f46e5;">{amount_at_risk:,.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Rule breakdown visualization
            st.subheader("Flagged Reasons Breakdown")
            # Explode flagged_rule_ids to count occurrences
            all_rule_ids = []
            for item in out_df["flagged_rule_ids"].dropna():
                if str(item).strip() != "":
                    all_rule_ids.extend(str(item).split(","))
            
            if all_rule_ids:
                rule_counts = pd.Series(all_rule_ids).value_counts().reset_index()
                rule_counts.columns = ["Rule Type", "Count"]
                # Map to human names
                rule_map = {
                    "preauth": "Pre-auth Missing/Unapproved",
                    "biodata": "Incomplete Patient Bio-data",
                    "coding": "Diagnosis-Procedure Coding Mismatch"
                }
                rule_counts["Rejection Rule"] = rule_counts["Rule Type"].map(rule_map)
                
                # Plot bar chart using Streamlit bar_chart or altair
                st.bar_chart(rule_counts.set_index("Rejection Rule")["Count"], color="#6366f1")
            else:
                st.info("No rejection flags were detected in the uploaded batch.")
            
            # Interactive results table
            st.subheader("Evaluated Claims Ledger")
            
            # Let users filter by status
            filter_status = st.multiselect(
                "Filter by Risk Status",
                options=["Clean", "At Risk", "High Risk"],
                default=["Clean", "At Risk", "High Risk"]
            )
            
            filtered_df = out_df[out_df["risk_status"].isin(filter_status)]
            
            # Present data editor or dataframe
            display_cols = ["claim_id", "risk_status", "flag_reasons", "patient_full_name", 
                            "visit_date", "service_type", "claim_amount", "diagnosis_code", "procedure_code"]
            
            # Color code row styles in st.dataframe is possible using style mapper
            def style_risk(val):
                if val == "High Risk":
                    return "background-color: rgba(239, 68, 68, 0.1); color: #ef4444;"
                elif val == "At Risk":
                    return "background-color: rgba(245, 158, 11, 0.1); color: #d97706;"
                elif val == "Clean":
                    return "background-color: rgba(16, 185, 129, 0.1); color: #059669;"
                return ""
            
            styled_df = filtered_df[display_cols].style.map(style_risk, subset=["risk_status"])
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Enable exporting output
            output_csv_data = out_df.drop(columns=["claim_amount_num"]).to_csv(index=False)
            st.download_button(
                label="📥 Export Risk-Scored Claims Output",
                data=output_csv_data,
                file_name="evaluated_claims_output.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"Error parsing claims file: {str(e)}")
else:
    st.info("Please upload a claims CSV file to begin verification.")
