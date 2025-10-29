import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import tempfile
from decimal import Decimal

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aws_client import aws_client
from utils.case_utils import CaseManager
from utils.visualization import *

# Helper functions for safe data access
def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 != 0 else int(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(v) for v in obj]
    elif isinstance(obj, set):
        return [convert_decimals(v) for v in obj]
    else:
        return obj

def format_timestamp(timestamp):
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    else:
        return str(timestamp)

def safe_get(data, key, default=None):
    if not isinstance(data, dict):
        return default
        
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return convert_decimals(current) if current is not None else default

# Initialize case manager
case_manager = CaseManager(aws_client)

# Page configuration
st.set_page_config(
    page_title="Healthcare Case Manager",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS for full-screen case view
# Professional CSS for table layout
# Professional CSS with proper document viewer height
# Professional CSS with compact buttons
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    .action-buttons-compact {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 0.5rem;  /* Reduced padding */
        margin-bottom: 0.8rem;
    }
    
    /* Compact button styling */
    .compact-button {
        font-size: 0.9rem !important;  /* Same as case info headings */
        padding: 0.3rem 0.6rem !important;  /* Smaller padding */
        height: 32px !important;  /* Reduced height */
        margin: 0.1rem !important;
    }
    
    /* Consistent badge styling */
    .status-badge {
        font-size: 0.7rem;
        padding: 0.15rem 0.4rem;
        border-radius: 3px;
        font-weight: 500;
        display: inline-block;
    }
    .status-pending { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    .status-approved { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .status-denied { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .status-in_progress { background: #cce7ff; color: #004085; border: 1px solid #b3d9ff; }
    .priority-high { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .priority-medium { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    .priority-low { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    
    /* FIXED HEIGHT for document viewer - enough for one PDF page */
    .document-viewer-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background: #fafafa;
        height: 800px;  /* Fixed pixel height for one PDF page */
        overflow: hidden;
        padding: 1rem;
    }
    .case-details-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background: white;
        height: 800px;  /* Match the height */
        overflow-y: auto;
        padding: 1rem;
    }
    
    /* Table Styles - Consistent with case details */
    .table-header {
        background-color: #f8f9fa;
        border-bottom: 2px solid #e9ecef;
        font-weight: 600;
        font-size: 0.8rem;
        color: #495057;
        padding: 0.75rem;
        text-align: left;
    }
    .table-cell {
        padding: 0.75rem;
        font-size: 0.8rem;
        color: #333;
        vertical-align: middle;
    }
    .status-badge-table, .priority-badge-table {
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
        display: inline-block;
    }
    
    /* Remove extra margins for compact layout */
    .stMarkdown {
        margin-bottom: 0.1rem !important;
    }
    /* Make the main area wider when sidebar is hidden */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize session state
    if 'selected_case' not in st.session_state:
        st.session_state.selected_case = None
    if 'action_taken' not in st.session_state:
        st.session_state.action_taken = False

    # If a case is selected, show full-screen case view without sidebar
    if st.session_state.selected_case:
        show_fullscreen_case_view(st.session_state.selected_case)
        return

    # Normal view with sidebar
    show_dashboard_with_sidebar()

def show_fullscreen_case_view(case):
    """Full-screen case view without sidebar"""
    
    # Header with back button and case title
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.selected_case = None
            st.rerun()
    
    with col2:
        patient_name = safe_get(case, 'patientName', 'Unknown Patient')
        st.markdown(f"<div style='text-align: center; font-size: 1.5rem; font-weight: 600; color: #2c3e50;'>Case Review: {patient_name}</div>", unsafe_allow_html=True)
    
    with col3:
        # Empty column for balance
        pass
    
    # Action buttons
    display_action_buttons_compact(case)
    
    # Main content - two equal columns
    left_col, right_col = st.columns([1, 1], gap="large")
    
    with left_col:
        st.markdown('<div class="case-details-container">', unsafe_allow_html=True)
        display_case_details_compact(case)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        st.markdown('<div class="document-viewer-container">', unsafe_allow_html=True)
        display_document_viewer_compact(case)
        st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard_with_sidebar():
    """Normal dashboard view with sidebar"""
    
    # Header
    st.markdown('<div class="main-header">🏥 Healthcare Case Management</div>', unsafe_allow_html=True)
    
    # Handle case actions
    if st.session_state.action_taken:
        st.session_state.action_taken = False
        st.session_state.selected_case = None
        st.rerun()

    # Sidebar
    with st.sidebar:
        st.markdown("**Navigation**")
        menu_option = st.radio("Go to:", ["📊 Dashboard", "📋 Case List", "📈 Analytics", "⚙️ Settings"], label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("**Filters**")
        
        status_filter = st.multiselect("Status", ["PENDING_REVIEW", "APPROVED", "DENIED", "IN_PROGRESS"], default=["PENDING_REVIEW"])
        doc_type_filter = st.multiselect("Document Type", ["pre-auth", "clinical-note", "lab-report", "insurance-claim", "referral", "prescription"])
        priority_filter = st.multiselect("Priority", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])

    # Main content based on menu selection
    if menu_option == "📊 Dashboard":
        show_dashboard_content(status_filter, doc_type_filter, priority_filter)
    elif menu_option == "📋 Case List":
        show_case_list(status_filter, doc_type_filter, priority_filter)
    elif menu_option == "📈 Analytics":
        show_analytics()
    elif menu_option == "⚙️ Settings":
        show_settings()

def show_dashboard_content(status_filter, doc_type_filter, priority_filter):
    """Dashboard content with professional table layout"""
    st.markdown("### 📊 Dashboard Overview")
    
    dashboard_filters = {
        'status': ["PENDING_REVIEW"],
        'document_type': doc_type_filter,
        'priority': priority_filter
    }
    
    cases = case_manager.get_all_cases()
    filtered_cases = case_manager.filter_cases(cases, dashboard_filters)
    all_cases = case_manager.get_all_cases()
    metrics = case_manager.get_case_metrics(all_cases)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Cases", metrics['total_cases'])
    with col2:
        st.metric("Pending Review", metrics['pending_cases'])
    with col3:
        st.metric("High Priority", metrics['high_priority'])
    with col4:
        st.metric("Approved", metrics['approved_cases'])
    
    st.markdown("---")
    
    # Pending Cases with professional table
    st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #2c3e50; margin-bottom: 1rem;">Pending Cases</div>', unsafe_allow_html=True)
    
    if not filtered_cases:
        st.info("No pending cases requiring attention")
        return
    
    # Display cases in a professional table format
    display_cases_table(filtered_cases)

def display_cases_table(cases):
    """Display cases in a professional table format"""
    
    # Table header
    st.markdown("""
    <style>
    .cases-table {
        width: 100%;
        border-collapse: collapse;
    }
    .table-header {
        background-color: #f8f9fa;
        border-bottom: 2px solid #e9ecef;
        font-weight: 600;
        font-size: 0.85rem;
        color: #495057;
    }
    .table-row {
        border-bottom: 1px solid #e9ecef;
    }
    .table-row:hover {
        background-color: #f8f9fa;
    }
    .table-cell {
        padding: 0.75rem;
        font-size: 0.8rem;
    }
    .caseid-link {
        color: #007bff;
        text-decoration: none;
        cursor: pointer;
        font-weight: 500;
    }
    .caseid-link:hover {
        text-decoration: underline;
    }
    .status-badge-table {
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }
    .priority-badge-table {
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create table header
    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 1.5, 1.5, 1, 1])
    
    with col1:
        st.markdown('<div class="table-header">Case ID</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="table-header">Member Name</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="table-header">Document Type</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="table-header">Received Date</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="table-header">Priority</div>', unsafe_allow_html=True)
    with col6:
        st.markdown('<div class="table-header">Status</div>', unsafe_allow_html=True)
    
    # Display each case as a table row
    for case in cases:
        display_case_table_row(case)

def display_case_table_row(case):
    """Display a single case as a table row"""
    case_id = safe_get(case, 'caseID', 'N/A')
    patient_name = safe_get(case, 'patientName', 'Unknown')
    document_type = safe_get(case, 'documentType', 'N/A')
    upload_date = safe_get(case, 'uploadDate', '')
    priority = safe_get(case, 'priority', 'MEDIUM')
    status = safe_get(case, 'status', 'UNKNOWN')
    
    # Format date
    if upload_date:
        formatted_date = format_timestamp(upload_date)
        display_date = formatted_date.split(' ')[0]  # Show only date part
    else:
        display_date = 'N/A'
    
    # Create columns for the table row
    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 1.5, 1.5, 1, 1])
    
    with col1:
        # Make Case ID clickable
        if st.button(case_id, key=f"case_{case_id}", use_container_width=True):
            st.session_state.selected_case = case
            st.rerun()
    
    with col2:
        st.markdown(f'<div class="table-cell">{patient_name}</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="table-cell">{document_type}</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'<div class="table-cell">{display_date}</div>', unsafe_allow_html=True)
    
    with col5:
        priority_badge_class = f"priority-{priority.lower()}"
        st.markdown(f'<div class="table-cell"><span class="priority-badge-table {priority_badge_class}">{priority}</span></div>', unsafe_allow_html=True)
    
    with col6:
        status_badge_class = f"status-{status.lower().replace('_', '-')}"
        st.markdown(f'<div class="table-cell"><span class="status-badge-table {status_badge_class}">{status}</span></div>', unsafe_allow_html=True)
    
    # Add subtle separator
    st.markdown('<hr style="margin: 0.2rem 0; border: none; border-top: 1px solid #f0f0f0;">', unsafe_allow_html=True)

def display_action_buttons_compact(case):
    """Compact action buttons with same font size as case info headings"""
    case_id = safe_get(case, 'caseID', '')
    current_status = safe_get(case, 'status', 'UNKNOWN')
    priority = safe_get(case, 'priority', 'MEDIUM')
    
    st.markdown('<div class="action-buttons-compact">', unsafe_allow_html=True)
    
    # Use more columns for better spacing with smaller buttons
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 1, 1, 1, 1.2])
    
    with col1:
        status_badge_class = f"status-{current_status.lower().replace('_', '-')}"
        st.markdown(f'<span class="status-badge {status_badge_class}">{current_status}</span>', unsafe_allow_html=True)
    
    with col2:
        if st.button("✅ Approve", use_container_width=True, type="primary", key="btn_approve"):
            if case_manager.update_case_status(case_id, 'APPROVED'):
                st.session_state.action_taken = True
                st.rerun()
    
    with col3:
        if st.button("❌ Deny", use_container_width=True, key="btn_deny"):
            if case_manager.update_case_status(case_id, 'DENIED'):
                st.session_state.action_taken = True
                st.rerun()
    
    with col4:
        if st.button("⏸️ Hold", use_container_width=True, key="btn_hold"):
            if case_manager.update_case_status(case_id, 'IN_PROGRESS'):
                st.session_state.action_taken = True
                st.rerun()
    
    with col5:
        priority_badge_class = f"priority-{priority.lower()}"
        st.markdown(f'<span class="status-badge {priority_badge_class}">{priority}</span>', unsafe_allow_html=True)
    
    with col6:
        confidence = safe_get(case, 'confidenceScore', 0) * 100
        st.markdown(f'<div style="font-size: 0.8rem;"><span style="font-weight: 600; color: #495057;">Confidence:</span> <span style="color: #333;">{confidence:.1f}%</span></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_case_details_compact(case):
    """Compact case details using dashboard table styling"""
    
    # Case Information
    st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #495057; margin-bottom: 0.5rem; border-bottom: 1px solid #e9ecef; padding-bottom: 0.3rem;">📋 Case Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Case ID:</span> <span style="color: #333;">{safe_get(case, "caseID", "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Document Type:</span> <span style="color: #333;">{safe_get(case, "documentType", "N/A")}</span></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">File Name:</span> <span style="color: #333;">{safe_get(case, "fileName", "N/A")}</span></div>', unsafe_allow_html=True)
        upload_date = safe_get(case, 'uploadDate')
        if upload_date:
            formatted_date = format_timestamp(upload_date)
            st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Upload Date:</span> <span style="color: #333;">{formatted_date}</span></div>', unsafe_allow_html=True)
    
    # Patient Information
    st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #495057; margin: 0.8rem 0 0.5rem 0; border-bottom: 1px solid #e9ecef; padding-bottom: 0.3rem;">👤 Patient Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Patient Name:</span> <span style="color: #333;">{safe_get(case, "patientName", "Not specified")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Date of Birth:</span> <span style="color: #333;">{safe_get(case, "patientDOB", "Not specified")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Member ID:</span> <span style="color: #333;">{safe_get(case, "memberId", "Not specified")}</span></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Insurance Plan:</span> <span style="color: #333;">{safe_get(case, "insurancePlan", "Not specified")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Policy Number:</span> <span style="color: #333;">{safe_get(case, "policyNumber", "Not specified")}</span></div>', unsafe_allow_html=True)
    
    # Clinical Information
    st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #495057; margin: 0.8rem 0 0.5rem 0; border-bottom: 1px solid #e9ecef; padding-bottom: 0.3rem;">🏥 Clinical Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Referring Provider:</span> <span style="color: #333;">{safe_get(case, "referringProvider", "Not specified")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Provider NPI:</span> <span style="color: #333;">{safe_get(case, "providerNPI", "Not specified")}</span></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Facility:</span> <span style="color: #333;">{safe_get(case, "facility", "Not specified")}</span></div>', unsafe_allow_html=True)
    
    # Medical Codes
    cpt_codes = safe_get(case, 'cptCodes', [])
    icd_codes = safe_get(case, 'icd10Codes', [])
    if cpt_codes or icd_codes:
        st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #495057; margin: 0.8rem 0 0.5rem 0; border-bottom: 1px solid #e9ecef; padding-bottom: 0.3rem;">📋 Medical Codes</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if cpt_codes:
                codes_text = ", ".join(cpt_codes)
                st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">CPT Codes:</span> <span style="color: #333;">{codes_text}</span></div>', unsafe_allow_html=True)
        
        with col2:
            if icd_codes:
                codes_text = ", ".join(icd_codes)
                st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">ICD-10 Codes:</span> <span style="color: #333;">{codes_text}</span></div>', unsafe_allow_html=True)
    
    # Diagnosis
    diagnosis = safe_get(case, 'diagnosisDescription', '')
    if diagnosis:
        st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #495057; margin: 0.8rem 0 0.5rem 0; border-bottom: 1px solid #e9ecef; padding-bottom: 0.3rem;">🩺 Diagnosis</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Description:</span> <span style="color: #333;">{diagnosis}</span></div>', unsafe_allow_html=True)
    
    # AI Analysis
    st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #495057; margin: 0.8rem 0 0.5rem 0; border-bottom: 1px solid #e9ecef; padding-bottom: 0.3rem;">🔍 AI Analysis</div>', unsafe_allow_html=True)
    
    confidence = safe_get(case, 'confidenceScore', 0) * 100
    st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.5rem;"><span style="font-weight: 600; color: #495057;">Confidence Score:</span> <span style="color: #333;">{confidence:.1f}%</span></div>', unsafe_allow_html=True)
    
    summary = safe_get(case, 'caseSummary', '')
    if summary:
        st.markdown('<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Summary:</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.8rem; color: #333; line-height: 1.4; padding: 0.5rem; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #007bff;">{summary}</div>', unsafe_allow_html=True)
    
    # Key findings
    extraction_metadata = safe_get(case, 'extractionMetadata', {})
    key_findings = safe_get(extraction_metadata, 'keyFindings', [])
    if key_findings:
        st.markdown('<div style="font-size: 0.8rem; margin-bottom: 0.3rem;"><span style="font-weight: 600; color: #495057;">Key Findings:</span></div>', unsafe_allow_html=True)
        for finding in key_findings:
            st.markdown(f'<div style="font-size: 0.8rem; color: #333; margin: 0.1rem 0 0.1rem 0.5rem;">• {finding}</div>', unsafe_allow_html=True)

def display_document_viewer_compact(case):
    """Document viewer using full container height for PDF display"""
    
    s3_location = safe_get(case, 's3Location')
    if not s3_location:
        st.warning("No document available")
        return
    
    try:
        document_url = aws_client.get_document_url(s3_location)
        file_extension = s3_location.split('.')[-1].lower()
        
        # Very compact file info at the top
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f'<div style="font-size: 0.8rem; margin-bottom: 0.5rem;"><span style="font-weight: 600; color: #495057;">File Type:</span> <span style="color: #333;">{file_extension.upper()}</span></div>', unsafe_allow_html=True)
        with col2:
            st.download_button(
                label="📥 Download",
                data=document_url,
                file_name=safe_get(case, 'fileName', 'document'),
                mime="application/octet-stream",
                use_container_width=True
            )
        
        # Document preview - USE FULL CONTAINER HEIGHT
        if file_extension in ['pdf']:
            # Use almost the entire container height for PDF (700px for 800px container)
            st.markdown(f'<iframe src="{document_url}" width="100%" height="700px" style="border: 1px solid #e0e0e0; border-radius: 4px;"></iframe>', unsafe_allow_html=True)
        elif file_extension in ['jpg', 'jpeg', 'png', 'gif']:
            st.image(document_url, use_column_width=True)
        elif file_extension in ['txt', 'text']:
            local_file = aws_client.download_document(s3_location)
            if local_file:
                with open(local_file, 'r') as f:
                    content = f.read()
                # Full height for text
                st.text_area("", content, height=650, label_visibility="collapsed")
        else:
            st.markdown(f"[Download Document]({document_url})")
        
    except Exception as e:
        st.error(f"Error loading document: {str(e)}")

def display_dashboard_case_card(case):
    """Compact case card for dashboard"""
    status = safe_get(case, 'status', 'UNKNOWN')
    priority = safe_get(case, 'priority', 'MEDIUM')
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{safe_get(case, 'patientName', 'Unknown')}**")
            st.markdown(f"*{safe_get(case, 'documentType', 'N/A')}*")
            st.markdown(f"📅 {format_timestamp(safe_get(case, 'uploadDate', ''))}")
        
        with col2:
            if st.button("Review Case", key=f"view_{safe_get(case, 'caseID')}", use_container_width=True):
                st.session_state.selected_case = case
                st.rerun()
            
            status_badge_class = f"status-{status.lower().replace('_', '-')}"
            priority_badge_class = f"priority-{priority.lower()}"
            st.markdown(f'<span class="status-badge {status_badge_class}">{status}</span>', unsafe_allow_html=True)
            st.markdown(f'<span class="status-badge {priority_badge_class}">{priority}</span>', unsafe_allow_html=True)

def show_case_list(status_filter, doc_type_filter, priority_filter):
    st.markdown("### 📋 Case List")
    cases = case_manager.get_all_cases()
    filters = {'status': status_filter, 'document_type': doc_type_filter, 'priority': priority_filter}
    filtered_cases = case_manager.filter_cases(cases, filters)
    st.write(f"Showing {len(filtered_cases)} cases")
    for case in filtered_cases:
        display_dashboard_case_card(case)

def show_analytics():
    st.markdown("### 📈 Analytics")
    st.info("Analytics dashboard coming soon")

def show_settings():
    st.markdown("### ⚙️ Settings")
    st.info("Settings panel coming soon")

if __name__ == "__main__":
    main()