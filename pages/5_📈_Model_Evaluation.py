"""
Model Evaluation Page - Streamlit Interface for checking model accuracy
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from core.model_evaluator import ModelEvaluator
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Login.py")

render_navbar()

st.header("📈 Model Accuracy Evaluation")

evaluator = ModelEvaluator()

# Tab layout
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Metrics", 
    "🏷️ Label Data", 
    "🔍 Error Analysis", 
    "📉 Threshold Analysis"
])

# Tab 1: Metrics
with tab1:
    st.subheader("Model Performance Metrics")
    
    if "results" not in st.session_state or not st.session_state.get("results"):
        st.warning("⚠️ No screening results available. Please process resumes first.")
        if st.button("📄 Go to Processing"):
            st.switch_page("pages/2_⚙️_Processing.py")
    else:
        results = st.session_state["results"]
        
        # Check coverage
        coverage = evaluator.get_coverage(results)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Resumes", coverage['total_resumes'])
        with col2:
            st.metric("Labeled Resumes", coverage['labeled_resumes'])
        with col3:
            st.metric("Coverage", f"{coverage['coverage_percentage']:.1f}%")
        
        if coverage['labeled_resumes'] == 0:
            st.warning("🏷️ No ground truth labels found. Please add labels in the 'Label Data' tab.")
        else:
            # Calculate metrics
            metrics = evaluator.evaluate(results)
            
            st.markdown("---")
            st.subheader("Performance Metrics")
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Accuracy", f"{metrics.accuracy:.2%}")
            with col2:
                st.metric("Precision", f"{metrics.precision:.2%}")
            with col3:
                st.metric("Recall", f"{metrics.recall:.2%}")
            with col4:
                st.metric("F1 Score", f"{metrics.f1_score:.2%}")
            
            st.markdown("---")
            st.subheader("Confusion Matrix")
            
            # Confusion matrix
            col1, col2 = st.columns(2)
            with col1:
                st.metric("✅ True Positives", metrics.true_positives, 
                         help="Correctly predicted as shortlist")
                st.metric("❌ False Positives", metrics.false_positives,
                         help="Incorrectly predicted as shortlist")
            with col2:
                st.metric("✅ True Negatives", metrics.true_negatives,
                         help="Correctly predicted as reject")
                st.metric("❌ False Negatives", metrics.false_negatives,
                         help="Incorrectly predicted as reject")
            
            # Visualization
            fig = go.Figure(data=go.Heatmap(
                z=[[metrics.true_positives, metrics.false_negatives],
                   [metrics.false_positives, metrics.true_negatives]],
                x=['Predicted Shortlist', 'Predicted Reject'],
                y=['Actual Shortlist', 'Actual Reject'],
                text=[[metrics.true_positives, metrics.false_negatives],
                      [metrics.false_positives, metrics.true_negatives]],
                texttemplate='%{text}',
                colorscale='Blues'
            ))
            fig.update_layout(title="Confusion Matrix", height=400)
            st.plotly_chart(fig, use_container_width=True)

# Tab 2: Label Data
with tab2:
    st.subheader("Add Ground Truth Labels")
    st.markdown("""
    To evaluate model accuracy, you need to provide ground truth labels for your resumes.
    Label each resume as **Shortlist** (candidate should be selected) or **Reject** (should not be selected).
    """)
    
    if "results" not in st.session_state or not st.session_state.get("results"):
        st.warning("⚠️ No screening results available.")
    else:
        results = st.session_state["results"]
        
        # Method 1: Manual labeling
        st.markdown("### Method 1: Label Interactively")
        
        for i, result in enumerate(results):
            resume_name = result.get('resume_name', f'Resume {i+1}')
            current_label = evaluator.ground_truth.get(resume_name)
            
            with st.expander(f"📄 {resume_name} {'✅' if current_label is True else '❌' if current_label is False else '⚪'}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    scores = result.get('scores', {})
                    st.write(f"**Final Score:** {scores.get('final_score', 0):.3f}")
                    st.write(f"**Skills Matched:** {len(scores.get('matched_skills', []))}")
                    st.write(f"**Experience:** {result.get('experience', 'N/A')} years")
                
                with col2:
                    st.write("**Label:**")
                    if st.button("✅ Shortlist", key=f"shortlist_{i}"):
                        evaluator.add_label(resume_name, True)
                        st.success("Labeled as Shortlist")
                        st.rerun()
                    if st.button("❌ Reject", key=f"reject_{i}"):
                        evaluator.add_label(resume_name, False)
                        st.success("Labeled as Reject")
                        st.rerun()
        
        # Method 2: Batch upload
        st.markdown("---")
        st.markdown("### Method 2: Upload Ground Truth File")
        st.markdown("""
        Upload a JSON file with the following format:
        ```json
        {
            "john_doe_resume.pdf": true,
            "jane_smith_resume.pdf": false
        }
        ```
        """)
        
        uploaded_file = st.file_uploader("Upload Ground Truth JSON", type=['json'])
        if uploaded_file is not None:
            try:
                import json
                labels = json.load(uploaded_file)
                evaluator.add_batch_labels(labels)
                st.success(f"✅ Loaded {len(labels)} labels successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {e}")

# Tab 3: Error Analysis
with tab3:
    st.subheader("Error Analysis")
    
    if "results" not in st.session_state or not st.session_state.get("results"):
        st.warning("⚠️ No screening results available.")
    else:
        results = st.session_state["results"]
        coverage = evaluator.get_coverage(results)
        
        if coverage['labeled_resumes'] == 0:
            st.warning("🏷️ No ground truth labels found. Please add labels first.")
        else:
            fp, fn = evaluator.get_misclassified(results)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("❌ False Positives", len(fp))
            with col2:
                st.metric("❌ False Negatives", len(fn))
            
            # False Positives
            if fp:
                st.markdown("### False Positives (Should Reject, but Predicted Shortlist)")
                for i, result in enumerate(fp):
                    with st.expander(f"📄 {result.get('resume_name', f'Resume {i+1}')}"):
                        scores = result.get('scores', {})
                        st.write(f"**Final Score:** {scores.get('final_score', 0):.3f} (Above threshold)")
                        st.write(f"**Semantic Score:** {scores.get('semantic_score', 0):.3f}")
                        st.write(f"**Skill Score:** {scores.get('skill_score', 0):.3f}")
                        st.write(f"**Experience Score:** {scores.get('experience_score', 0):.3f}")
                        st.write(f"**Matched Skills:** {', '.join(scores.get('matched_skills', []))}")
            
            # False Negatives
            if fn:
                st.markdown("### False Negatives (Should Shortlist, but Predicted Reject)")
                for i, result in enumerate(fn):
                    with st.expander(f"📄 {result.get('resume_name', f'Resume {i+1}')}"):
                        scores = result.get('scores', {})
                        st.write(f"**Final Score:** {scores.get('final_score', 0):.3f} (Below threshold)")
                        st.write(f"**Semantic Score:** {scores.get('semantic_score', 0):.3f}")
                        st.write(f"**Skill Score:** {scores.get('skill_score', 0):.3f}")
                        st.write(f"**Experience Score:** {scores.get('experience_score', 0):.3f}")
                        st.write(f"**Missing Skills:** {', '.join(scores.get('missing_skills', []))}")

# Tab 4: Threshold Analysis
with tab4:
    st.subheader("Threshold Analysis")
    st.markdown("Analyze how different threshold values affect model performance.")
    
    if "results" not in st.session_state or not st.session_state.get("results"):
        st.warning("⚠️ No screening results available.")
    else:
        results = st.session_state["results"]
        coverage = evaluator.get_coverage(results)
        
        if coverage['labeled_resumes'] == 0:
            st.warning("🏷️ No ground truth labels found. Please add labels first.")
        else:
            # Threshold analysis
            df = evaluator.threshold_analysis(results)
            
            # Plot metrics vs threshold
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['threshold'], y=df['accuracy'], 
                                    name='Accuracy', mode='lines+markers'))
            fig.add_trace(go.Scatter(x=df['threshold'], y=df['precision'], 
                                    name='Precision', mode='lines+markers'))
            fig.add_trace(go.Scatter(x=df['threshold'], y=df['recall'], 
                                    name='Recall', mode='lines+markers'))
            fig.add_trace(go.Scatter(x=df['threshold'], y=df['f1_score'], 
                                    name='F1 Score', mode='lines+markers'))
            
            fig.update_layout(
                title="Metrics vs Threshold",
                xaxis_title="Threshold",
                yaxis_title="Score",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show table
            st.dataframe(df, use_container_width=True)
            
            # Recommendation
            best_f1_idx = df['f1_score'].idxmax()
            best_threshold = df.loc[best_f1_idx, 'threshold']
            best_f1 = df.loc[best_f1_idx, 'f1_score']
            
            st.info(f"💡 **Recommended Threshold:** {best_threshold:.2f} (F1 Score: {best_f1:.2%})")
