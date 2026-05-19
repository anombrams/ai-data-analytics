"""
AI Data Processing Portal
A Streamlit application for AI-powered data analysis with Bricks-like features
"""

import streamlit as st
import pandas as pd
import os
from typing import Optional

# Import custom modules
from utils.data_loader import DataLoader
from utils.data_analyzer import DataAnalyzer
from utils.ai_engine import AIEngine
from components.chat_interface import ChatInterface
from components.visualizer import Visualizer
from components.data_table import DataTable
from components.spreadsheet import Spreadsheet, render_spreadsheet_tab
from components.dashboard_builder import DashboardBuilder, render_dashboard_tab
from utils.exporter import render_export_section


# Page configuration
st.set_page_config(
    page_title="AI Data Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished UI
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1E88E5 0%, #7C4DFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0;
    }

    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-top: 0;
    }

    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 4px solid #1E88E5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1E88E5 !important;
        color: white !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e0e0;
    }

    [data-testid="stSidebar"] h2 {
        color: #ffffff;
        font-weight: 600;
    }

    [data-testid="stSidebar"] h3 {
        color: #90caf9;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.3);
    }

    /* Data editor styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Success/Warning/Error styling */
    .stSuccess, .stWarning, .stError, .stInfo {
        border-radius: 8px;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #1E88E5;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #1E88E5 0%, #7C4DFF 100%);
    }

    /* Logo area */
    .logo-container {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    .logo-text {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
    }

    .logo-subtext {
        font-size: 0.8rem;
        color: #90caf9;
        margin-top: 4px;
    }

    /* Card styling for welcome page */
    .feature-card {
        background: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        height: 100%;
    }

    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
    }

    /* Toast notification styling */
    .toast {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: #1E88E5;
        color: white;
        border-radius: 8px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    }

    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'file_name' not in st.session_state:
        st.session_state.file_name = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'ai_engine' not in st.session_state:
        st.session_state.ai_engine = None
    if 'chat_interface' not in st.session_state:
        st.session_state.chat_interface = ChatInterface()
    if 'analysis_done' not in st.session_state:
        st.session_state.analysis_done = False
    # Multi-file support
    if 'datasets' not in st.session_state:
        st.session_state.datasets = {}
    if 'active_dataset' not in st.session_state:
        st.session_state.active_dataset = None
    if 'auto_insights' not in st.session_state:
        st.session_state.auto_insights = {}
    # Dashboard state
    if 'dashboard_config' not in st.session_state:
        st.session_state.dashboard_config = None
    if 'dashboard_builder' not in st.session_state:
        st.session_state.dashboard_builder = None
    # Spreadsheet state
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None


def process_uploaded_files(files: list, auto_process: bool = True):
    """Process multiple uploaded files and optionally auto-generate insights"""
    ai_engine = st.session_state.ai_engine

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_files = len(files)

    for i, uploaded_file in enumerate(files):
        status_text.text(f"Processing {uploaded_file.name}...")
        progress_bar.progress((i) / total_files)

        # Load file
        df, error = DataLoader.load_file(uploaded_file)

        if error:
            st.error(f"Error loading {uploaded_file.name}: {error}")
            continue

        # Analyze data
        analyzer = DataAnalyzer(df)
        analysis = analyzer.analyze()

        # Store in session state
        st.session_state.datasets[uploaded_file.name] = {
            'df': df,
            'analyzer': analyzer,
            'analysis': analysis
        }

        # Auto-generate AI insights if enabled and API configured
        if auto_process and ai_engine and ai_engine.is_configured():
            status_text.text(f"Generating AI insights for {uploaded_file.name}...")

            schema = analyzer.get_schema_for_ai()
            sample_data = analyzer.get_sample_data()
            summary = analyzer.get_summary()

            response = ai_engine.get_insights(schema, sample_data, summary)

            if not response.error:
                st.session_state.auto_insights[uploaded_file.name] = response.explanation

        progress_bar.progress((i + 1) / total_files)

    progress_bar.empty()
    status_text.empty()

    # Set first file as active if no active dataset
    if st.session_state.active_dataset is None and st.session_state.datasets:
        first_file = list(st.session_state.datasets.keys())[0]
        set_active_dataset(first_file)

    st.success(f"Loaded {len(files)} file(s) successfully!")
    st.rerun()


def set_active_dataset(name: str):
    """Set the active dataset for analysis"""
    if name in st.session_state.datasets:
        data = st.session_state.datasets[name]
        st.session_state.df = data['df']
        st.session_state.file_name = name
        st.session_state.analyzer = data['analyzer']
        st.session_state.analysis = data['analysis']
        st.session_state.analysis_done = True
        st.session_state.active_dataset = name
        # Reset dashboard when switching datasets
        st.session_state.dashboard_config = None
        st.session_state.dashboard_builder = None


def remove_dataset(name: str):
    """Remove a dataset from the session"""
    if name in st.session_state.datasets:
        del st.session_state.datasets[name]
    if name in st.session_state.auto_insights:
        del st.session_state.auto_insights[name]

    # If removed dataset was active, switch to another
    if st.session_state.active_dataset == name:
        if st.session_state.datasets:
            new_active = list(st.session_state.datasets.keys())[0]
            set_active_dataset(new_active)
        else:
            clear_all_data()


def clear_all_data():
    """Clear all loaded data"""
    st.session_state.df = None
    st.session_state.file_name = None
    st.session_state.analyzer = None
    st.session_state.analysis_done = False
    st.session_state.datasets = {}
    st.session_state.active_dataset = None
    st.session_state.auto_insights = {}
    st.session_state.dashboard_config = None
    st.session_state.dashboard_builder = None
    st.session_state.chat_interface.clear_history()


def render_sidebar():
    """Render sidebar with file upload and settings"""
    with st.sidebar:
        # Logo area
        st.markdown("""
            <div class="logo-container">
                <div class="logo-text">📊 AI Data Portal</div>
                <div class="logo-subtext">Powered by Claude AI</div>
            </div>
        """, unsafe_allow_html=True)

        # API Key configuration
        st.markdown("### AI Configuration")

        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=os.getenv('ANTHROPIC_API_KEY', ''),
            help="Enter your Anthropic API key for AI features"
        )

        if api_key:
            st.session_state.ai_engine = AIEngine(api_key)
            if st.session_state.ai_engine.is_configured():
                st.success("API Connected")
            else:
                st.warning("Invalid API Key")
        else:
            st.session_state.ai_engine = AIEngine()
            if not st.session_state.ai_engine.is_configured():
                st.info("Set API key for AI features")

        st.markdown("---")

        # Data Upload section
        st.markdown("### Data Upload")

        uploaded_files = st.file_uploader(
            "Upload your data files",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="Supported formats: CSV, Excel (.xlsx, .xls)"
        )

        # Auto-process checkbox
        auto_process = st.checkbox(
            "Auto-generate AI insights",
            value=True,
            help="Automatically generate AI insights for uploaded files"
        )

        if uploaded_files:
            new_files = []
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.datasets:
                    new_files.append(uploaded_file)

            if new_files:
                process_uploaded_files(new_files, auto_process)

        # Show loaded datasets
        if st.session_state.datasets:
            st.markdown("---")
            st.markdown("### Active Datasets")

            dataset_names = list(st.session_state.datasets.keys())

            if st.session_state.active_dataset is None and dataset_names:
                st.session_state.active_dataset = dataset_names[0]
                set_active_dataset(dataset_names[0])

            selected = st.radio(
                "Select dataset:",
                dataset_names,
                index=dataset_names.index(st.session_state.active_dataset) if st.session_state.active_dataset in dataset_names else 0,
                key="dataset_selector"
            )

            if selected != st.session_state.active_dataset:
                set_active_dataset(selected)
                st.rerun()

            # Dataset info
            for name, data in st.session_state.datasets.items():
                with st.expander(f"{'✓ ' if name == st.session_state.active_dataset else ''}{name}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{len(data['df']):,}")
                    with col2:
                        st.metric("Cols", len(data['df'].columns))

                    if name in st.session_state.auto_insights:
                        st.caption("AI insights available")

                    if st.button(f"Remove", key=f"remove_{name}", use_container_width=True):
                        remove_dataset(name)
                        st.rerun()

            # Clear all button
            if st.button("Clear All Data", type="secondary", use_container_width=True):
                clear_all_data()
                st.rerun()

        # About section
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        **AI Data Portal** - Your intelligent data analysis companion.

        Features:
        - Multi-file data upload
        - Editable spreadsheet
        - Auto-generated dashboards
        - Export to PDF/PowerPoint
        - AI-powered insights
        """)


def render_welcome():
    """Render welcome screen when no data is loaded"""
    st.markdown('<p class="main-header">AI Data Processing Portal</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform your data into insights with AI-powered analysis</p>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        ### 📤 Upload
        Upload CSV or Excel files to get started. Support for multiple files simultaneously.
        """)

    with col2:
        st.markdown("""
        ### 📝 Edit
        Edit your data in a spreadsheet-like interface with formula support.
        """)

    with col3:
        st.markdown("""
        ### 📊 Dashboard
        Auto-generate beautiful dashboards with AI-selected visualizations.
        """)

    with col4:
        st.markdown("""
        ### 📥 Export
        Export your dashboards to PDF or PowerPoint for presentations.
        """)

    st.markdown("---")

    # Quick start guide
    st.subheader("Quick Start")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("""
        1. **Enter API Key** in the sidebar
        2. **Upload your data** (CSV or Excel)
        3. **Explore** the auto-generated insights
        4. **Edit** data in the spreadsheet
        5. **Generate** a dashboard
        6. **Export** to PDF or PowerPoint
        """)

    with col2:
        st.info("""
        **Pro Tips:**
        - Use the AI Chat tab to ask questions about your data in natural language
        - The Dashboard auto-selects the best charts for your data
        - Formulas like =SUM(A1:A10) work in the spreadsheet
        - Export maintains all your charts and insights
        """)


def render_overview_tab():
    """Render data overview tab"""
    df = st.session_state.df
    analyzer = st.session_state.analyzer
    file_name = st.session_state.file_name

    if not st.session_state.analysis_done:
        with st.spinner("Analyzing data..."):
            analysis = analyzer.analyze()
            st.session_state.analysis = analysis
            st.session_state.analysis_done = True

    analysis = st.session_state.analysis

    # Show AI Auto-Insights if available
    if file_name in st.session_state.auto_insights:
        st.subheader("AI Auto-Generated Insights")
        with st.container():
            st.markdown(st.session_state.auto_insights[file_name])
        st.markdown("---")

    # Summary metrics
    st.subheader("Data Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Rows", f"{analysis['summary']['total_rows']:,}")
    with col2:
        st.metric("Total Columns", analysis['summary']['total_columns'])
    with col3:
        st.metric("Missing Values", f"{analysis['summary']['missing_values']:,}")
    with col4:
        st.metric("Quality Score", f"{analysis['quality'].score:.1f}%")

    # Data quality details
    st.subheader("Data Quality Assessment")

    quality = analysis['quality']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Quality Metrics**")
        metrics_df = pd.DataFrame({
            'Metric': ['Completeness', 'Uniqueness', 'Consistency'],
            'Score': [f"{quality.completeness:.1f}%", f"{quality.uniqueness:.1f}%", f"{quality.consistency:.1f}%"]
        })
        st.dataframe(metrics_df, hide_index=True, use_container_width=True)

    with col2:
        if quality.issues:
            st.markdown("**Issues Found**")
            for issue in quality.issues:
                st.warning(issue)
        else:
            st.success("No significant issues found!")

    if quality.recommendations:
        st.markdown("**Recommendations**")
        for rec in quality.recommendations:
            st.info(rec)

    # Column information
    st.subheader("Column Details")

    col_data = []
    for col, info in analysis['columns'].items():
        col_data.append({
            'Column': col,
            'Type': info.inferred_type.value,
            'Data Type': info.dtype,
            'Unique': info.unique_count,
            'Missing': f"{info.missing_pct}%",
            'Sample Values': str(info.sample_values[:3])[:50]
        })

    col_df = pd.DataFrame(col_data)
    st.dataframe(col_df, hide_index=True, use_container_width=True)


def render_data_tab():
    """Render data exploration tab"""
    df = st.session_state.df
    data_table = DataTable(df)

    view_tab1, view_tab2 = st.tabs(["Data Table", "Statistics"])

    with view_tab1:
        filtered_df = data_table.render_with_filters()

        col1, col2 = st.columns([3, 1])
        with col2:
            csv_data = data_table.export_data('csv')
            st.download_button(
                "Download Filtered Data (CSV)",
                csv_data,
                "filtered_data.csv",
                "text/csv",
                use_container_width=True
            )

    with view_tab2:
        data_table.render_summary_stats()


def render_spreadsheet_tab_wrapper():
    """Wrapper for spreadsheet tab"""
    df = st.session_state.df
    edited_df = render_spreadsheet_tab(df)

    # Store edited dataframe
    if edited_df is not None:
        st.session_state.edited_df = edited_df


def render_dashboard_tab_wrapper():
    """Wrapper for dashboard tab"""
    df = st.session_state.edited_df if st.session_state.edited_df is not None else st.session_state.df
    ai_engine = st.session_state.ai_engine

    builder = render_dashboard_tab(df, ai_engine)

    if builder:
        st.session_state.dashboard_builder = builder


def render_export_tab():
    """Render export tab"""
    df = st.session_state.edited_df if st.session_state.edited_df is not None else st.session_state.df
    builder = st.session_state.get('dashboard_builder')

    render_export_section(builder, df)


def render_chat_tab():
    """Render AI chat tab"""
    df = st.session_state.df
    analyzer = st.session_state.analyzer
    ai_engine = st.session_state.ai_engine
    chat = st.session_state.chat_interface

    if not ai_engine or not ai_engine.is_configured():
        st.warning("Please configure your Anthropic API key in the sidebar to use AI features.")
        return

    schema = analyzer.get_schema_for_ai()
    sample_data = analyzer.get_sample_data()

    # Render chat history
    chat.render_chat_history()

    # Suggested queries
    if len(chat.get_history()) == 0:
        selected_suggestion = chat.render_suggested_queries(df)
        if selected_suggestion:
            process_query(selected_suggestion, schema, sample_data, df)
            st.rerun()

    # Quick actions
    quick_action = chat.render_quick_actions(df)
    if quick_action:
        process_query(quick_action, schema, sample_data, df)
        st.rerun()

    # Chat input
    user_query = chat.render_input()

    if user_query:
        process_query(user_query, schema, sample_data, df)
        st.rerun()

    # Clear chat button
    if len(chat.get_history()) > 0:
        if st.button("Clear Chat History"):
            chat.clear_history()
            st.rerun()


def process_query(query: str, schema: str, sample_data: str, df: pd.DataFrame):
    """Process user query and get AI response"""
    chat = st.session_state.chat_interface
    ai_engine = st.session_state.ai_engine

    chat.add_message('user', query)

    with st.spinner("Analyzing..."):
        response = ai_engine.analyze_query(query, schema, sample_data, df)

    chat.add_message(
        'assistant',
        response.explanation,
        code=response.code,
        result=response.execution_result,
        chart_type=response.chart_type
    )


def render_visualize_tab():
    """Render visualization tab"""
    df = st.session_state.df
    visualizer = Visualizer(df)

    col1, col2 = st.columns([1, 2])

    with col1:
        chart_type, columns = visualizer.render_chart_selector()
        create_chart = st.button("Create Chart", type="primary", use_container_width=True)

    with col2:
        if create_chart and chart_type and columns:
            with st.spinner("Creating chart..."):
                fig = visualizer.create_chart_by_type(chart_type, columns)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Could not create chart with selected options")

    st.markdown("---")
    st.subheader("Recommended Visualizations")

    recommendations = visualizer.recommend_charts()

    if recommendations:
        cols = st.columns(min(len(recommendations), 3))

        for i, rec in enumerate(recommendations[:3]):
            with cols[i]:
                st.markdown(f"**{rec['title']}**")
                st.caption(rec['description'])

                if st.button(f"Create", key=f"rec_chart_{i}"):
                    fig = visualizer.create_chart_by_type(rec['type'], rec['columns'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)


def render_insights_tab():
    """Render AI insights tab"""
    df = st.session_state.df
    analyzer = st.session_state.analyzer
    ai_engine = st.session_state.ai_engine
    file_name = st.session_state.file_name

    if not ai_engine or not ai_engine.is_configured():
        st.warning("Please configure your Anthropic API key in the sidebar to use AI features.")
        return

    # Show all datasets insights summary
    if len(st.session_state.datasets) > 1:
        st.subheader("All Datasets Overview")
        tabs = st.tabs(list(st.session_state.datasets.keys()))

        for i, (name, data) in enumerate(st.session_state.datasets.items()):
            with tabs[i]:
                if name in st.session_state.auto_insights:
                    st.markdown(st.session_state.auto_insights[name])
                else:
                    st.info("No AI insights generated for this dataset yet.")
                    if st.button(f"Generate Insights", key=f"gen_insight_{name}"):
                        with st.spinner(f"Generating insights for {name}..."):
                            schema = data['analyzer'].get_schema_for_ai()
                            sample_data = data['analyzer'].get_sample_data()
                            summary = data['analyzer'].get_summary()
                            response = ai_engine.get_insights(schema, sample_data, summary)
                            if not response.error:
                                st.session_state.auto_insights[name] = response.explanation
                                st.rerun()
                            else:
                                st.error(f"Error: {response.error}")

        st.markdown("---")

    # Current dataset insights
    st.subheader(f"Insights for: {file_name}")

    schema = analyzer.get_schema_for_ai()
    sample_data = analyzer.get_sample_data()
    summary = analyzer.get_summary()

    if file_name in st.session_state.auto_insights:
        st.markdown(st.session_state.auto_insights[file_name])

        if st.button("Regenerate Insights", type="secondary"):
            with st.spinner("Regenerating insights..."):
                response = ai_engine.get_insights(schema, sample_data, summary)
                if not response.error:
                    st.session_state.auto_insights[file_name] = response.explanation
                    st.rerun()
                else:
                    st.error(f"Error: {response.error}")
    else:
        if st.button("Generate AI Insights", type="primary"):
            with st.spinner("Generating insights..."):
                response = ai_engine.get_insights(schema, sample_data, summary)

                if response.error:
                    st.error(f"Error: {response.error}")
                else:
                    st.session_state.auto_insights[file_name] = response.explanation
                    st.markdown(response.explanation)

    # Visualization suggestions
    st.markdown("---")
    st.subheader("Visualization Recommendations")

    if st.button("Get Chart Suggestions"):
        with st.spinner("Analyzing data for visualization ideas..."):
            column_types = {col: str(info.inferred_type.value)
                           for col, info in analyzer.get_column_info().items()}
            response = ai_engine.suggest_visualizations(schema, column_types)

            if response.error:
                st.error(f"Error: {response.error}")
            else:
                st.markdown(response.explanation)


def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Main content
    if st.session_state.df is None:
        render_welcome()
    else:
        # Header
        st.markdown(f"## Analyzing: {st.session_state.file_name}")

        # Main tabs - New flow: Overview, Spreadsheet, Dashboard, Export, Chat, Visualize, Insights
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📋 Overview",
            "📝 Spreadsheet",
            "📊 Dashboard",
            "📥 Export",
            "💬 AI Chat",
            "📈 Visualize",
            "💡 Insights"
        ])

        with tab1:
            render_overview_tab()

        with tab2:
            render_spreadsheet_tab_wrapper()

        with tab3:
            render_dashboard_tab_wrapper()

        with tab4:
            render_export_tab()

        with tab5:
            render_chat_tab()

        with tab6:
            render_visualize_tab()

        with tab7:
            render_insights_tab()


if __name__ == "__main__":
    main()
