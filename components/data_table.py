"""
Data Table Component
Interactive data table with filtering and sorting
"""

import pandas as pd
import streamlit as st
from typing import Optional, List, Dict, Any, Tuple


class DataTable:
    """Interactive data table component"""

    def __init__(self, df: pd.DataFrame):
        """Initialize with DataFrame"""
        self.df = df
        self._filtered_df = df.copy()

    def render(self, key: str = "main_table") -> pd.DataFrame:
        """
        Render interactive data table with controls

        Args:
            key: Unique key for Streamlit widgets

        Returns:
            Filtered DataFrame
        """
        # Controls row
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            # Column selector
            all_columns = self.df.columns.tolist()
            selected_columns = st.multiselect(
                "Select columns to display",
                all_columns,
                default=all_columns[:min(10, len(all_columns))],
                key=f"{key}_columns"
            )

        with col2:
            # Search box
            search_term = st.text_input(
                "Search in data",
                key=f"{key}_search",
                placeholder="Type to search..."
            )

        with col3:
            # Row limit
            row_limit = st.selectbox(
                "Show rows",
                [10, 25, 50, 100, 500, "All"],
                key=f"{key}_limit"
            )

        # Apply column selection
        if selected_columns:
            display_df = self.df[selected_columns].copy()
        else:
            display_df = self.df.copy()

        # Apply search filter
        if search_term:
            mask = pd.Series([False] * len(display_df))
            for col in display_df.columns:
                try:
                    mask |= display_df[col].astype(str).str.contains(
                        search_term, case=False, na=False
                    )
                except:
                    pass
            display_df = display_df[mask]

        # Apply row limit
        if row_limit != "All":
            display_df = display_df.head(int(row_limit))

        # Store filtered df
        self._filtered_df = display_df

        # Display info
        st.caption(f"Showing {len(display_df)} of {len(self.df)} rows")

        # Render table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=False
        )

        return display_df

    def render_with_filters(self, key: str = "filtered_table") -> pd.DataFrame:
        """
        Render data table with advanced column filters

        Args:
            key: Unique key for widgets

        Returns:
            Filtered DataFrame
        """
        st.subheader("Data Filters")

        filtered_df = self.df.copy()

        # Get column types
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()

        # Create filter UI
        with st.expander("Configure Filters", expanded=False):
            filter_cols = st.multiselect(
                "Select columns to filter",
                self.df.columns.tolist(),
                key=f"{key}_filter_cols"
            )

            filters = {}

            for col in filter_cols:
                st.markdown(f"**{col}**")

                if col in numeric_cols:
                    # Numeric range filter
                    min_val = float(self.df[col].min())
                    max_val = float(self.df[col].max())

                    if min_val != max_val:
                        range_val = st.slider(
                            f"Range for {col}",
                            min_val, max_val,
                            (min_val, max_val),
                            key=f"{key}_{col}_range"
                        )
                        filters[col] = ('range', range_val)

                elif col in categorical_cols:
                    # Categorical multi-select filter
                    unique_vals = self.df[col].dropna().unique().tolist()

                    if len(unique_vals) <= 50:
                        selected_vals = st.multiselect(
                            f"Select values for {col}",
                            unique_vals,
                            default=unique_vals,
                            key=f"{key}_{col}_select"
                        )
                        filters[col] = ('categorical', selected_vals)
                    else:
                        # Too many values, use text search
                        search_val = st.text_input(
                            f"Search in {col}",
                            key=f"{key}_{col}_search"
                        )
                        if search_val:
                            filters[col] = ('search', search_val)

                elif col in datetime_cols:
                    # Date range filter
                    min_date = self.df[col].min()
                    max_date = self.df[col].max()

                    date_range = st.date_input(
                        f"Date range for {col}",
                        value=(min_date, max_date),
                        key=f"{key}_{col}_date"
                    )
                    if len(date_range) == 2:
                        filters[col] = ('date_range', date_range)

            # Apply filters
            for col, (filter_type, filter_val) in filters.items():
                if filter_type == 'range':
                    filtered_df = filtered_df[
                        (filtered_df[col] >= filter_val[0]) &
                        (filtered_df[col] <= filter_val[1])
                    ]
                elif filter_type == 'categorical':
                    filtered_df = filtered_df[filtered_df[col].isin(filter_val)]
                elif filter_type == 'search':
                    filtered_df = filtered_df[
                        filtered_df[col].astype(str).str.contains(
                            filter_val, case=False, na=False
                        )
                    ]
                elif filter_type == 'date_range':
                    filtered_df = filtered_df[
                        (filtered_df[col] >= pd.Timestamp(filter_val[0])) &
                        (filtered_df[col] <= pd.Timestamp(filter_val[1]))
                    ]

        # Display filtered data
        st.caption(f"Showing {len(filtered_df)} of {len(self.df)} rows after filtering")

        st.dataframe(filtered_df, use_container_width=True)

        self._filtered_df = filtered_df
        return filtered_df

    def render_column_stats(self, column: str):
        """Render statistics for a specific column"""
        if column not in self.df.columns:
            st.error(f"Column '{column}' not found")
            return

        series = self.df[column]

        st.subheader(f"Statistics for '{column}'")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Values", len(series))
            st.metric("Unique Values", series.nunique())
            st.metric("Missing Values", series.isna().sum())

        with col2:
            if pd.api.types.is_numeric_dtype(series):
                st.metric("Mean", f"{series.mean():.2f}")
                st.metric("Median", f"{series.median():.2f}")
                st.metric("Std Dev", f"{series.std():.2f}")
            else:
                mode = series.mode()
                st.metric("Mode", str(mode.iloc[0]) if len(mode) > 0 else "N/A")
                st.metric("Mode Frequency", series.value_counts().iloc[0] if len(series.value_counts()) > 0 else 0)

    def get_filtered_data(self) -> pd.DataFrame:
        """Get the currently filtered DataFrame"""
        return self._filtered_df

    def render_summary_stats(self):
        """Render summary statistics table"""
        st.subheader("Summary Statistics")

        # Numeric summary
        numeric_df = self.df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            st.markdown("**Numeric Columns**")
            st.dataframe(
                numeric_df.describe().T.round(2),
                use_container_width=True
            )

        # Categorical summary
        categorical_df = self.df.select_dtypes(include=['object', 'category'])
        if not categorical_df.empty:
            st.markdown("**Categorical Columns**")
            cat_summary = pd.DataFrame({
                'Unique': categorical_df.nunique(),
                'Top Value': categorical_df.apply(lambda x: x.value_counts().index[0] if len(x.value_counts()) > 0 else 'N/A'),
                'Top Frequency': categorical_df.apply(lambda x: x.value_counts().iloc[0] if len(x.value_counts()) > 0 else 0),
                'Missing': categorical_df.isna().sum()
            })
            st.dataframe(cat_summary, use_container_width=True)

    def export_data(self, format: str = 'csv') -> bytes:
        """Export filtered data to bytes"""
        if format == 'csv':
            return self._filtered_df.to_csv(index=False).encode('utf-8')
        elif format == 'excel':
            import io
            buffer = io.BytesIO()
            self._filtered_df.to_excel(buffer, index=False, engine='openpyxl')
            return buffer.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
