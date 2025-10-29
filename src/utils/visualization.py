import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict

def create_status_pie_chart(cases: List[Dict]) -> go.Figure:
    """Create pie chart of case status distribution"""
    if not cases:
        return create_empty_chart("No data available")
    
    status_counts = pd.DataFrame([c.get('status', 'UNKNOWN') for c in cases]).value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    fig = px.pie(status_counts, values='Count', names='Status', 
                 title="Case Status Distribution",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_document_type_bar_chart(cases: List[Dict]) -> go.Figure:
    """Create bar chart of document types"""
    if not cases:
        return create_empty_chart("No data available")
    
    doc_type_counts = pd.DataFrame([c.get('documentType', 'unknown') for c in cases]).value_counts().reset_index()
    doc_type_counts.columns = ['DocumentType', 'Count']
    
    fig = px.bar(doc_type_counts, x='DocumentType', y='Count',
                 title="Document Type Distribution",
                 color='DocumentType', 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(xaxis_title="Document Type", yaxis_title="Count")
    return fig

def create_confidence_gauge(confidence_score: float) -> go.Figure:
    """Create confidence score gauge"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence_score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "AI Confidence Score"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def create_empty_chart(message: str) -> go.Figure:
    """Create an empty chart with message"""
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper",
                      x=0.5, y=0.5, xanchor='center', yanchor='middle',
                      showarrow=False, font=dict(size=16))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig