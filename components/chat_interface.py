"""
Chat Interface Component
Natural language query UI for data analysis
"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    code: Optional[str] = None
    result: Optional[Any] = None
    chart_type: Optional[str] = None


class ChatInterface:
    """Manages chat UI and message history"""

    def __init__(self):
        """Initialize chat interface"""
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state for chat history"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'suggested_queries' not in st.session_state:
            st.session_state.suggested_queries = []

    def add_message(self, role: str, content: str, code: Optional[str] = None,
                    result: Optional[Any] = None, chart_type: Optional[str] = None):
        """Add a message to chat history"""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            code=code,
            result=result,
            chart_type=chart_type
        )
        st.session_state.chat_history.append(message)

    def clear_history(self):
        """Clear chat history"""
        st.session_state.chat_history = []

    def get_history(self) -> List[ChatMessage]:
        """Get chat history"""
        return st.session_state.chat_history

    def render_chat_history(self):
        """Render chat history in Streamlit"""
        for message in st.session_state.chat_history:
            with st.chat_message(message.role):
                st.markdown(message.content)

                # Show code if present
                if message.code:
                    with st.expander("View Code", expanded=False):
                        st.code(message.code, language='python')

                # Show result if present (and not a plotly figure)
                if message.result is not None:
                    if isinstance(message.result, pd.DataFrame):
                        st.dataframe(message.result, use_container_width=True)
                    elif hasattr(message.result, 'show'):  # Plotly figure
                        st.plotly_chart(message.result, use_container_width=True)
                    elif isinstance(message.result, (str, int, float)):
                        st.info(f"Result: {message.result}")

    def render_input(self) -> Optional[str]:
        """Render chat input and return user query"""
        return st.chat_input("Ask a question about your data...")

    def render_suggested_queries(self, df: Optional[pd.DataFrame] = None) -> Optional[str]:
        """Render suggested query buttons based on data"""
        if df is None:
            return None

        # Generate suggestions based on data
        suggestions = self._generate_suggestions(df)

        if not suggestions:
            return None

        st.markdown("**Suggested queries:**")
        cols = st.columns(min(len(suggestions), 4))

        selected = None
        for i, suggestion in enumerate(suggestions[:4]):
            with cols[i]:
                if st.button(suggestion['label'], key=f"suggest_{i}", use_container_width=True):
                    selected = suggestion['query']

        return selected

    def _generate_suggestions(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Generate query suggestions based on DataFrame"""
        suggestions = []

        # Basic suggestions
        suggestions.append({
            'label': '📊 Show overview',
            'query': 'Give me an overview of this dataset'
        })

        # Get column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Suggest visualizations based on column types
        if numeric_cols:
            col = numeric_cols[0]
            suggestions.append({
                'label': f'📈 Distribution of {col[:15]}',
                'query': f'Show the distribution of {col}'
            })

        if categorical_cols:
            col = categorical_cols[0]
            suggestions.append({
                'label': f'📊 Count by {col[:15]}',
                'query': f'Show a bar chart of counts by {col}'
            })

        if len(numeric_cols) >= 2:
            suggestions.append({
                'label': '🔗 Correlation analysis',
                'query': 'Show correlation between numeric columns'
            })

        # Add insights suggestion
        suggestions.append({
            'label': '💡 Key insights',
            'query': 'What are the key insights from this data?'
        })

        return suggestions

    def render_quick_actions(self, df: Optional[pd.DataFrame] = None) -> Optional[str]:
        """Render quick action buttons"""
        if df is None:
            return None

        st.markdown("**Quick Actions:**")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📋 First 10 rows", use_container_width=True):
                return "Show the first 10 rows"

        with col2:
            if st.button("📊 Statistics", use_container_width=True):
                return "Show descriptive statistics for all numeric columns"

        with col3:
            if st.button("❓ Missing values", use_container_width=True):
                return "Show missing values count for each column"

        with col4:
            if st.button("🔄 Duplicates", use_container_width=True):
                return "How many duplicate rows are there?"

        return None

    def export_chat_history(self) -> str:
        """Export chat history as markdown"""
        lines = ["# Chat History\n"]

        for message in st.session_state.chat_history:
            role = "User" if message.role == "user" else "Assistant"
            lines.append(f"## {role} ({message.timestamp.strftime('%H:%M:%S')})\n")
            lines.append(f"{message.content}\n")

            if message.code:
                lines.append("\n```python\n")
                lines.append(message.code)
                lines.append("\n```\n")

            lines.append("\n---\n")

        return "\n".join(lines)
