"""
Visualizer Component
Auto-generate charts based on data types and user requests
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List, Dict, Any, Tuple
import streamlit as st


class Visualizer:
    """Handles chart generation and recommendations"""

    # Color schemes
    DEFAULT_COLORS = px.colors.qualitative.Set2
    SEQUENTIAL_COLORS = px.colors.sequential.Blues

    def __init__(self, df: pd.DataFrame):
        """Initialize visualizer with DataFrame"""
        self.df = df

    def recommend_charts(self) -> List[Dict[str, Any]]:
        """
        Recommend chart types based on data

        Returns:
            List of chart recommendations with type, columns, and description
        """
        recommendations = []

        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()

        # Distribution charts for numeric columns
        for col in numeric_cols[:3]:  # Limit to first 3
            recommendations.append({
                'type': 'histogram',
                'columns': [col],
                'title': f'Distribution of {col}',
                'description': f'Shows the frequency distribution of {col}'
            })

        # Bar charts for categorical columns
        for col in categorical_cols[:2]:  # Limit to first 2
            if self.df[col].nunique() <= 20:  # Only if reasonable number of categories
                recommendations.append({
                    'type': 'bar',
                    'columns': [col],
                    'title': f'Count by {col}',
                    'description': f'Shows the count of records for each {col}'
                })

        # Time series if datetime column exists
        if datetime_cols and numeric_cols:
            recommendations.append({
                'type': 'line',
                'columns': [datetime_cols[0], numeric_cols[0]],
                'title': f'{numeric_cols[0]} over Time',
                'description': f'Shows how {numeric_cols[0]} changes over {datetime_cols[0]}'
            })

        # Scatter plot for numeric pairs
        if len(numeric_cols) >= 2:
            recommendations.append({
                'type': 'scatter',
                'columns': [numeric_cols[0], numeric_cols[1]],
                'title': f'{numeric_cols[0]} vs {numeric_cols[1]}',
                'description': f'Shows relationship between {numeric_cols[0]} and {numeric_cols[1]}'
            })

        # Correlation heatmap if multiple numeric columns
        if len(numeric_cols) >= 3:
            recommendations.append({
                'type': 'heatmap',
                'columns': numeric_cols[:10],  # Limit columns
                'title': 'Correlation Matrix',
                'description': 'Shows correlations between numeric variables'
            })

        # Box plot for numeric by categorical
        if numeric_cols and categorical_cols:
            cat_col = categorical_cols[0]
            if self.df[cat_col].nunique() <= 10:
                recommendations.append({
                    'type': 'box',
                    'columns': [numeric_cols[0], cat_col],
                    'title': f'{numeric_cols[0]} by {cat_col}',
                    'description': f'Shows distribution of {numeric_cols[0]} across {cat_col} categories'
                })

        return recommendations

    def create_histogram(self, column: str, nbins: int = 30,
                         title: Optional[str] = None) -> go.Figure:
        """Create histogram for numeric column"""
        fig = px.histogram(
            self.df,
            x=column,
            nbins=nbins,
            title=title or f'Distribution of {column}',
            color_discrete_sequence=self.DEFAULT_COLORS
        )
        fig.update_layout(
            xaxis_title=column,
            yaxis_title='Count',
            showlegend=False
        )
        return fig

    def create_bar_chart(self, column: str, top_n: int = 20,
                         title: Optional[str] = None,
                         horizontal: bool = False) -> go.Figure:
        """Create bar chart for categorical column"""
        value_counts = self.df[column].value_counts().head(top_n)

        if horizontal:
            fig = px.bar(
                x=value_counts.values,
                y=value_counts.index,
                orientation='h',
                title=title or f'Count by {column}',
                color_discrete_sequence=self.DEFAULT_COLORS
            )
            fig.update_layout(xaxis_title='Count', yaxis_title=column)
        else:
            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=title or f'Count by {column}',
                color_discrete_sequence=self.DEFAULT_COLORS
            )
            fig.update_layout(xaxis_title=column, yaxis_title='Count')

        return fig

    def create_pie_chart(self, column: str, top_n: int = 10,
                         title: Optional[str] = None) -> go.Figure:
        """Create pie chart for categorical column"""
        value_counts = self.df[column].value_counts().head(top_n)

        # Group small categories as 'Other'
        if len(self.df[column].value_counts()) > top_n:
            other_count = self.df[column].value_counts().iloc[top_n:].sum()
            value_counts['Other'] = other_count

        fig = px.pie(
            values=value_counts.values,
            names=value_counts.index,
            title=title or f'Distribution of {column}',
            color_discrete_sequence=self.DEFAULT_COLORS
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')

        return fig

    def create_line_chart(self, x_column: str, y_column: str,
                          title: Optional[str] = None,
                          group_by: Optional[str] = None) -> go.Figure:
        """Create line chart"""
        if group_by and group_by in self.df.columns:
            fig = px.line(
                self.df.sort_values(x_column),
                x=x_column,
                y=y_column,
                color=group_by,
                title=title or f'{y_column} over {x_column}',
                color_discrete_sequence=self.DEFAULT_COLORS
            )
        else:
            fig = px.line(
                self.df.sort_values(x_column),
                x=x_column,
                y=y_column,
                title=title or f'{y_column} over {x_column}',
                color_discrete_sequence=self.DEFAULT_COLORS
            )

        fig.update_layout(xaxis_title=x_column, yaxis_title=y_column)
        return fig

    def create_scatter_plot(self, x_column: str, y_column: str,
                            color_column: Optional[str] = None,
                            size_column: Optional[str] = None,
                            title: Optional[str] = None,
                            trendline: bool = False) -> go.Figure:
        """Create scatter plot"""
        fig = px.scatter(
            self.df,
            x=x_column,
            y=y_column,
            color=color_column,
            size=size_column,
            title=title or f'{y_column} vs {x_column}',
            color_discrete_sequence=self.DEFAULT_COLORS,
            trendline='ols' if trendline else None
        )

        fig.update_layout(xaxis_title=x_column, yaxis_title=y_column)
        return fig

    def create_box_plot(self, y_column: str, x_column: Optional[str] = None,
                        title: Optional[str] = None) -> go.Figure:
        """Create box plot"""
        fig = px.box(
            self.df,
            x=x_column,
            y=y_column,
            title=title or f'Box Plot of {y_column}' + (f' by {x_column}' if x_column else ''),
            color=x_column,
            color_discrete_sequence=self.DEFAULT_COLORS
        )

        return fig

    def create_heatmap(self, columns: Optional[List[str]] = None,
                       title: Optional[str] = None) -> go.Figure:
        """Create correlation heatmap"""
        if columns:
            numeric_df = self.df[columns].select_dtypes(include=['number'])
        else:
            numeric_df = self.df.select_dtypes(include=['number'])

        corr_matrix = numeric_df.corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))

        fig.update_layout(
            title=title or 'Correlation Heatmap',
            xaxis_title='',
            yaxis_title='',
            height=max(400, len(corr_matrix) * 40)
        )

        return fig

    def create_chart_by_type(self, chart_type: str, columns: List[str],
                             **kwargs) -> Optional[go.Figure]:
        """
        Create chart by type string

        Args:
            chart_type: Type of chart (histogram, bar, pie, line, scatter, box, heatmap)
            columns: List of column names to use
            **kwargs: Additional arguments for specific chart types
        """
        chart_type = chart_type.lower()

        try:
            if chart_type == 'histogram':
                return self.create_histogram(columns[0], **kwargs)

            elif chart_type == 'bar':
                return self.create_bar_chart(columns[0], **kwargs)

            elif chart_type == 'pie':
                return self.create_pie_chart(columns[0], **kwargs)

            elif chart_type == 'line':
                if len(columns) >= 2:
                    return self.create_line_chart(columns[0], columns[1], **kwargs)
                else:
                    return self.create_line_chart(self.df.index.name or 'index', columns[0], **kwargs)

            elif chart_type == 'scatter':
                if len(columns) >= 2:
                    return self.create_scatter_plot(columns[0], columns[1], **kwargs)

            elif chart_type == 'box':
                if len(columns) >= 2:
                    return self.create_box_plot(columns[0], columns[1], **kwargs)
                else:
                    return self.create_box_plot(columns[0], **kwargs)

            elif chart_type == 'heatmap':
                return self.create_heatmap(columns if columns else None, **kwargs)

            else:
                return None

        except Exception as e:
            st.error(f"Error creating {chart_type} chart: {str(e)}")
            return None

    def create_overview_dashboard(self) -> List[go.Figure]:
        """Create a set of overview charts"""
        figures = []

        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Add histogram for first numeric column
        if numeric_cols:
            figures.append(self.create_histogram(numeric_cols[0]))

        # Add bar chart for first categorical column
        if categorical_cols:
            col = categorical_cols[0]
            if self.df[col].nunique() <= 20:
                figures.append(self.create_bar_chart(col))

        # Add correlation heatmap if multiple numeric columns
        if len(numeric_cols) >= 3:
            figures.append(self.create_heatmap(numeric_cols[:8]))

        return figures

    def render_chart_selector(self) -> Tuple[Optional[str], Optional[List[str]]]:
        """Render chart type selector UI"""
        st.subheader("Create Visualization")

        chart_types = ['histogram', 'bar', 'pie', 'line', 'scatter', 'box', 'heatmap']
        selected_type = st.selectbox("Chart Type", chart_types)

        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        all_cols = self.df.columns.tolist()

        selected_columns = []

        if selected_type == 'histogram':
            col = st.selectbox("Select numeric column", numeric_cols)
            selected_columns = [col] if col else []

        elif selected_type == 'bar':
            col = st.selectbox("Select categorical column", categorical_cols + numeric_cols)
            selected_columns = [col] if col else []

        elif selected_type == 'pie':
            col = st.selectbox("Select categorical column", categorical_cols)
            selected_columns = [col] if col else []

        elif selected_type == 'line':
            x_col = st.selectbox("X-axis (typically date/time)", all_cols)
            y_col = st.selectbox("Y-axis (numeric)", numeric_cols)
            selected_columns = [x_col, y_col] if x_col and y_col else []

        elif selected_type == 'scatter':
            x_col = st.selectbox("X-axis", numeric_cols, key='scatter_x')
            y_col = st.selectbox("Y-axis", numeric_cols, key='scatter_y')
            selected_columns = [x_col, y_col] if x_col and y_col else []

        elif selected_type == 'box':
            y_col = st.selectbox("Numeric column", numeric_cols)
            x_col = st.selectbox("Group by (optional)", ['None'] + categorical_cols)
            selected_columns = [y_col, x_col] if y_col and x_col != 'None' else [y_col] if y_col else []

        elif selected_type == 'heatmap':
            selected_columns = st.multiselect("Select numeric columns", numeric_cols, default=numeric_cols[:5])

        return selected_type, selected_columns

    def chart_to_image(self, fig: go.Figure, width: int = 800, height: int = 500, scale: float = 2.0) -> Optional[bytes]:
        """
        Convert Plotly figure to PNG image bytes for export

        Args:
            fig: Plotly figure to convert
            width: Image width in pixels
            height: Image height in pixels
            scale: Scale factor for higher resolution

        Returns:
            PNG image as bytes, or None if conversion fails
        """
        try:
            # Update layout for clean export
            fig.update_layout(
                paper_bgcolor='white',
                plot_bgcolor='white',
                margin=dict(l=40, r=40, t=60, b=40)
            )

            # Convert to image bytes using kaleido
            img_bytes = fig.to_image(
                format='png',
                width=width,
                height=height,
                scale=scale
            )
            return img_bytes

        except Exception as e:
            st.error(f"Error converting chart to image: {e}")
            return None

    def save_chart_to_file(self, fig: go.Figure, filepath: str, width: int = 800, height: int = 500) -> bool:
        """
        Save Plotly figure to image file

        Args:
            fig: Plotly figure
            filepath: Output file path
            width: Image width
            height: Image height

        Returns:
            True if successful, False otherwise
        """
        try:
            fig.write_image(filepath, width=width, height=height, scale=2)
            return True
        except Exception as e:
            st.error(f"Error saving chart: {e}")
            return False

    def create_dashboard_charts(self, chart_configs: list) -> List[go.Figure]:
        """
        Create multiple charts from configuration list

        Args:
            chart_configs: List of chart configuration dictionaries

        Returns:
            List of Plotly figures
        """
        figures = []

        for config in chart_configs:
            chart_type = config.get('type', 'bar')
            columns = config.get('columns', [])
            title = config.get('title', 'Chart')

            fig = self.create_chart_by_type(chart_type, columns, title=title)
            if fig:
                figures.append(fig)

        return figures
