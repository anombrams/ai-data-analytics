"""
Advanced Dashboard Builder
Comprehensive Data Analytics like Senior Data Engineer & Data Scientist
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class MetricBox:
    """Configuration for a metric box"""
    title: str
    value: Any
    subtitle: str = ""
    icon: str = ""
    color: str = "#667eea"
    trend: str = ""  # "up", "down", "neutral"
    trend_value: str = ""


@dataclass
class InsightSection:
    """A chart with its insights"""
    title: str
    chart_type: str
    columns: List[str]
    insights: List[str]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableSection:
    """A table with its insights"""
    title: str
    data: pd.DataFrame
    insights: List[str]


@dataclass
class ComprehensiveDashboard:
    """Full comprehensive dashboard"""
    title: str
    subtitle: str
    overview: str
    overall_insights: List[str]
    primary_metrics: List[MetricBox]  # First row of metrics
    secondary_metrics: List[MetricBox]  # Second row of metrics
    sections: List[InsightSection]  # Chart sections
    tables: List[TableSection]  # Table sections
    data_quality: Dict[str, Any]
    recommendations: List[str]


class AdvancedDataAnalyzer:
    """Advanced data analysis engine"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        self._clean_columns()

    def _clean_columns(self):
        """Remove technical columns"""
        exclude = ['id', 'uuid', 'created_at', 'updated_at', 'deleted_at', '_id', 'auth', 'token', 'hash']
        self.numeric_cols = [c for c in self.numeric_cols if not any(ex in c.lower() for ex in exclude)]
        self.categorical_cols = [c for c in self.categorical_cols if not any(ex in c.lower() for ex in exclude)]

    def get_data_quality_report(self) -> Dict[str, Any]:
        """Comprehensive data quality analysis"""
        total_cells = self.df.size
        missing_cells = self.df.isna().sum().sum()
        duplicate_rows = self.df.duplicated().sum()

        # Column-wise analysis
        col_quality = []
        for col in self.df.columns:
            missing = self.df[col].isna().sum()
            missing_pct = (missing / len(self.df)) * 100
            unique = self.df[col].nunique()
            unique_pct = (unique / len(self.df)) * 100

            col_quality.append({
                'column': col,
                'missing': missing,
                'missing_pct': missing_pct,
                'unique': unique,
                'unique_pct': unique_pct,
                'dtype': str(self.df[col].dtype)
            })

        return {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'total_cells': total_cells,
            'missing_cells': missing_cells,
            'missing_pct': (missing_cells / total_cells) * 100 if total_cells > 0 else 0,
            'duplicate_rows': duplicate_rows,
            'duplicate_pct': (duplicate_rows / len(self.df)) * 100 if len(self.df) > 0 else 0,
            'completeness': 100 - ((missing_cells / total_cells) * 100) if total_cells > 0 else 100,
            'column_quality': col_quality,
            'numeric_columns': len(self.numeric_cols),
            'categorical_columns': len(self.categorical_cols),
            'datetime_columns': len(self.datetime_cols)
        }

    def get_statistical_summary(self) -> Dict[str, Any]:
        """Comprehensive statistical summary"""
        stats = {}

        for col in self.numeric_cols:
            series = self.df[col].dropna()
            if len(series) == 0:
                continue

            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = series[(series < lower_bound) | (series > upper_bound)]

            stats[col] = {
                'count': len(series),
                'mean': series.mean(),
                'median': series.median(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'range': series.max() - series.min(),
                'q1': q1,
                'q3': q3,
                'iqr': iqr,
                'skewness': series.skew(),
                'kurtosis': series.kurtosis(),
                'outliers_count': len(outliers),
                'outliers_pct': (len(outliers) / len(series)) * 100,
                'zero_count': (series == 0).sum(),
                'zero_pct': ((series == 0).sum() / len(series)) * 100,
                'negative_count': (series < 0).sum(),
                'positive_count': (series > 0).sum()
            }

        return stats

    def get_categorical_summary(self) -> Dict[str, Any]:
        """Comprehensive categorical summary"""
        summary = {}

        for col in self.categorical_cols:
            series = self.df[col].dropna()
            if len(series) == 0:
                continue

            value_counts = series.value_counts()
            top_n = value_counts.head(10)

            summary[col] = {
                'unique_count': series.nunique(),
                'mode': value_counts.index[0] if len(value_counts) > 0 else None,
                'mode_count': value_counts.iloc[0] if len(value_counts) > 0 else 0,
                'mode_pct': (value_counts.iloc[0] / len(series)) * 100 if len(value_counts) > 0 else 0,
                'top_values': top_n.to_dict(),
                'entropy': -sum((value_counts / len(series)) * np.log2(value_counts / len(series) + 1e-10)),
                'concentration': (value_counts.iloc[0] / len(series)) if len(value_counts) > 0 else 0
            }

        return summary

    def get_correlation_analysis(self) -> Dict[str, Any]:
        """Correlation analysis for numeric columns"""
        if len(self.numeric_cols) < 2:
            return {}

        corr_matrix = self.df[self.numeric_cols].corr()

        # Find strong correlations
        strong_positive = []
        strong_negative = []

        for i, col1 in enumerate(self.numeric_cols):
            for j, col2 in enumerate(self.numeric_cols):
                if i < j:
                    corr = corr_matrix.loc[col1, col2]
                    if corr > 0.7:
                        strong_positive.append((col1, col2, corr))
                    elif corr < -0.7:
                        strong_negative.append((col1, col2, corr))

        return {
            'matrix': corr_matrix,
            'strong_positive': strong_positive,
            'strong_negative': strong_negative
        }

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in data"""
        anomalies = []

        for col in self.numeric_cols:
            series = self.df[col].dropna()
            if len(series) < 10:
                continue

            mean, std = series.mean(), series.std()
            if std == 0:
                continue

            z_scores = np.abs((series - mean) / std)
            extreme = series[z_scores > 3]

            if len(extreme) > 0:
                anomalies.append({
                    'column': col,
                    'type': 'extreme_values',
                    'count': len(extreme),
                    'examples': extreme.head(3).tolist()
                })

        return anomalies


class ComprehensiveDashboardBuilder:
    """Builds comprehensive dashboards like a senior data analyst"""

    COLORS = {
        'primary': '#667eea',
        'secondary': '#764ba2',
        'success': '#48bb78',
        'warning': '#ed8936',
        'danger': '#f56565',
        'info': '#4299e1',
        'chart': ['#667eea', '#48bb78', '#ed8936', '#f56565', '#9f7aea', '#38b2ac', '#ed64a6', '#4299e1']
    }

    def __init__(self, df: pd.DataFrame, ai_engine=None):
        self.df = df
        self.ai_engine = ai_engine
        self.analyzer = AdvancedDataAnalyzer(df)
        self.config: Optional[ComprehensiveDashboard] = None
        self.domain = self._detect_domain()

    def _detect_domain(self) -> str:
        """Detect business domain"""
        cols = ' '.join(self.df.columns.str.lower())
        if any(x in cols for x in ['kamar', 'room', 'bed', 'tersedia', 'available']):
            return 'healthcare_rooms'
        elif any(x in cols for x in ['sales', 'revenue', 'order']):
            return 'sales'
        elif any(x in cols for x in ['patient', 'pasien', 'diagnosis']):
            return 'healthcare_patients'
        return 'general'

    def generate(self) -> ComprehensiveDashboard:
        """Generate comprehensive dashboard"""
        quality = self.analyzer.get_data_quality_report()
        stats = self.analyzer.get_statistical_summary()
        cat_summary = self.analyzer.get_categorical_summary()
        correlations = self.analyzer.get_correlation_analysis()
        anomalies = self.analyzer.detect_anomalies()

        if self.domain == 'healthcare_rooms':
            config = self._build_healthcare_room_dashboard(quality, stats, cat_summary, correlations, anomalies)
        else:
            config = self._build_general_dashboard(quality, stats, cat_summary, correlations, anomalies)

        self.config = config
        return config

    def _find_col(self, keywords: List[str]) -> Optional[str]:
        """Find column by keywords"""
        for col in self.df.columns:
            if any(kw in col.lower() for kw in keywords):
                return col
        return None

    def _build_healthcare_room_dashboard(self, quality, stats, cat_summary, correlations, anomalies) -> ComprehensiveDashboard:
        """Build comprehensive healthcare room dashboard"""

        # Find key columns
        capacity_col = self._find_col(['total_kamar', 'total', 'kapasitas', 'capacity'])
        available_col = self._find_col(['tersedia', 'available', 'kamar_tersedia'])
        class_col = self._find_col(['kelas', 'class', 'kategori'])
        name_col = self._find_col(['nama_kamar', 'nama', 'name', 'ruang'])

        # Calculate key metrics
        if capacity_col and available_col:
            total_capacity = self.df[capacity_col].sum()
            total_available = self.df[available_col].sum()
            total_occupied = total_capacity - total_available
            occupancy_rate = (total_occupied / total_capacity * 100) if total_capacity > 0 else 0

            self.df['_shortage'] = self.df[capacity_col] - self.df[available_col]
            self.df['_occupancy_rate'] = self.df['_shortage'] / self.df[capacity_col].replace(0, 1) * 100
            self.df['_availability_rate'] = self.df[available_col] / self.df[capacity_col].replace(0, 1) * 100

            zero_avail_count = (self.df[available_col] == 0).sum()
            critical_rooms = (self.df[available_col] <= 2).sum()
            high_avail_rooms = (self.df['_availability_rate'] > 80).sum()
        else:
            total_capacity = len(self.df)
            total_available = 0
            total_occupied = 0
            occupancy_rate = 0
            zero_avail_count = 0
            critical_rooms = 0
            high_avail_rooms = 0

        total_rooms = len(self.df)
        total_categories = self.df[class_col].nunique() if class_col else 0

        # Title & Subtitle
        title = "Hospital Room Availability Analytics"
        subtitle = f"Comprehensive analysis of {total_rooms} rooms across {total_categories} categories"

        # Overview
        overview = f"""This comprehensive dashboard provides real-time visibility into hospital room capacity and availability.
It analyzes {total_rooms:,} room entries with {int(total_capacity):,} total bed capacity, of which {int(total_available):,} beds are currently available.
The analysis covers occupancy patterns, capacity distribution, shortage identification, and data quality metrics.
Use this dashboard to optimize bed allocation, identify bottlenecks, and make data-driven decisions for resource management."""

        # Overall Insights (8-10 comprehensive insights)
        overall_insights = self._generate_comprehensive_room_insights(
            capacity_col, available_col, class_col, name_col,
            total_capacity, total_available, occupancy_rate, stats, cat_summary
        )

        # Primary Metrics (First Row - 4 boxes)
        primary_metrics = [
            MetricBox("Total Bed Capacity", f"{int(total_capacity):,}", "Maximum beds available", "🏥", self.COLORS['primary']),
            MetricBox("Available Beds", f"{int(total_available):,}", "Currently unoccupied", "🛏️", self.COLORS['success']),
            MetricBox("Occupancy Rate", f"{occupancy_rate:.1f}%", "Current utilization", "📊", self.COLORS['warning'] if occupancy_rate > 80 else self.COLORS['info']),
            MetricBox("Total Room Types", f"{total_rooms:,}", "Unique room entries", "🏠", self.COLORS['secondary']),
        ]

        # Secondary Metrics (Second Row - 4 boxes)
        secondary_metrics = [
            MetricBox("Fully Occupied", f"{zero_avail_count:,}", "Rooms at 100% capacity", "⚠️", self.COLORS['danger']),
            MetricBox("Critical Status", f"{critical_rooms:,}", "Rooms with ≤2 beds available", "🚨", self.COLORS['warning']),
            MetricBox("High Availability", f"{high_avail_rooms:,}", "Rooms with >80% available", "✅", self.COLORS['success']),
            MetricBox("Data Completeness", f"{quality['completeness']:.1f}%", "Data quality score", "📋", self.COLORS['info']),
        ]

        # Chart Sections
        sections = []

        # Section 1: Capacity Distribution (Donut)
        if class_col and capacity_col:
            class_dist = self.df.groupby(class_col)[capacity_col].sum().sort_values(ascending=False)
            dist_insights = [
                f"{class_dist.index[0]} holds the largest capacity share with {class_dist.iloc[0]:,.0f} beds ({class_dist.iloc[0]/class_dist.sum()*100:.1f}% of total).",
                f"Top 3 classes ({', '.join(class_dist.index[:3])}) account for {class_dist.head(3).sum()/class_dist.sum()*100:.1f}% of total capacity.",
                f"Capacity is distributed across {len(class_dist)} distinct room classes.",
                f"The smallest class ({class_dist.index[-1]}) has only {class_dist.iloc[-1]:,.0f} beds ({class_dist.iloc[-1]/class_dist.sum()*100:.1f}%)."
            ]
            sections.append(InsightSection(
                title="Capacity Distribution by Room Class",
                chart_type="donut",
                columns=[class_col, capacity_col],
                insights=dist_insights
            ))

        # Section 2: Capacity vs Availability (Stacked Bar)
        if class_col and capacity_col and available_col:
            class_stats = self.df.groupby(class_col).agg({
                capacity_col: 'sum',
                available_col: 'sum'
            }).sort_values(capacity_col, ascending=False)

            stacked_insights = [
                f"{class_stats.index[0]} has highest capacity ({class_stats.iloc[0][capacity_col]:,.0f}) with {class_stats.iloc[0][available_col]:,.0f} available ({class_stats.iloc[0][available_col]/class_stats.iloc[0][capacity_col]*100:.1f}% availability).",
                f"Utilization pressure is highest in classes with low availability ratios.",
                f"Classes with >50% occupancy may need resource reallocation.",
                f"Consider load balancing between high and low occupancy classes."
            ]
            sections.append(InsightSection(
                title="Capacity vs Availability by Room Class",
                chart_type="stacked_bar",
                columns=[class_col, capacity_col, available_col],
                insights=stacked_insights
            ))

        # Section 3: Occupancy Rate Distribution
        if '_occupancy_rate' in self.df.columns:
            occ_insights = [
                f"Average occupancy rate across all rooms is {self.df['_occupancy_rate'].mean():.1f}%.",
                f"{(self.df['_occupancy_rate'] > 90).sum()} rooms have occupancy >90% (critical level).",
                f"{(self.df['_occupancy_rate'] < 50).sum()} rooms have occupancy <50% (underutilized).",
                f"Occupancy ranges from {self.df['_occupancy_rate'].min():.1f}% to {self.df['_occupancy_rate'].max():.1f}%."
            ]
            sections.append(InsightSection(
                title="Occupancy Rate Distribution",
                chart_type="histogram",
                columns=['_occupancy_rate'],
                insights=occ_insights
            ))

        # Section 4: Zero Availability Rooms
        if available_col and name_col:
            zero_df = self.df[self.df[available_col] == 0]
            if len(zero_df) > 0:
                zero_insights = [
                    f"{len(zero_df)} rooms currently have zero availability.",
                    f"These rooms represent {len(zero_df)/len(self.df)*100:.1f}% of all room types.",
                    f"Total blocked capacity: {zero_df[capacity_col].sum() if capacity_col else len(zero_df):,.0f} beds.",
                    f"Immediate action needed for patient overflow management."
                ]
                sections.append(InsightSection(
                    title="Rooms With Zero Availability",
                    chart_type="bar_horizontal",
                    columns=[name_col, capacity_col] if capacity_col else [name_col],
                    insights=zero_insights,
                    options={'filter': 'zero_avail'}
                ))

        # Section 5: Top Shortage Analysis
        if '_shortage' in self.df.columns and name_col:
            top_shortage = self.df.nlargest(10, '_shortage')
            shortage_insights = [
                f"Top shortage room: {top_shortage.iloc[0][name_col]} with {top_shortage.iloc[0]['_shortage']:.0f} beds occupied.",
                f"Top 5 rooms account for {top_shortage.head(5)['_shortage'].sum():.0f} total shortage.",
                f"Average shortage per room: {self.df['_shortage'].mean():.1f} beds.",
                f"Consider capacity expansion for high-shortage rooms."
            ]
            sections.append(InsightSection(
                title="Top 10 Rooms by Shortage (Beds Occupied)",
                chart_type="bar_shortage",
                columns=[name_col, '_shortage'],
                insights=shortage_insights
            ))

        # Section 6: Availability Rate by Class
        if class_col and '_availability_rate' in self.df.columns:
            class_avail = self.df.groupby(class_col)['_availability_rate'].mean().sort_values(ascending=False)
            avail_insights = [
                f"Highest availability: {class_avail.index[0]} at {class_avail.iloc[0]:.1f}% average availability.",
                f"Lowest availability: {class_avail.index[-1]} at {class_avail.iloc[-1]:.1f}% average availability.",
                f"Availability varies by {class_avail.max() - class_avail.min():.1f} percentage points across classes.",
                f"Classes below 50% availability need immediate attention."
            ]
            sections.append(InsightSection(
                title="Average Availability Rate by Room Class",
                chart_type="bar_rate",
                columns=[class_col, '_availability_rate'],
                insights=avail_insights
            ))

        # Section 7: Correlation Analysis (if applicable)
        if len(self.analyzer.numeric_cols) >= 2:
            corr_insights = [
                f"Capacity and availability show {correlations.get('matrix', pd.DataFrame()).loc[capacity_col, available_col]:.2f} correlation." if capacity_col and available_col and not correlations.get('matrix', pd.DataFrame()).empty else "Correlation analysis available.",
                f"{len(correlations.get('strong_positive', []))} strong positive correlations detected.",
                f"{len(correlations.get('strong_negative', []))} strong negative correlations detected.",
                "Strong correlations indicate predictable relationships."
            ]
            sections.append(InsightSection(
                title="Correlation Matrix - Numeric Variables",
                chart_type="heatmap",
                columns=self.analyzer.numeric_cols[:6],
                insights=corr_insights
            ))

        # Tables
        tables = []

        # Table 1: Detailed Room Status
        if name_col and capacity_col and available_col:
            table_df = self.df[[name_col, capacity_col, available_col, '_shortage', '_availability_rate']].copy()
            table_df = table_df.sort_values('_shortage', ascending=False).head(15)
            table_df.columns = ['Room Name', 'Capacity', 'Available', 'Shortage', 'Availability %']
            table_df['Availability %'] = table_df['Availability %'].round(1)

            table_insights = [
                f"Showing top 15 rooms by shortage.",
                f"Rooms with 0% availability need immediate escalation.",
                f"Consider redistributing patients from high-shortage rooms.",
                f"Monitor rooms approaching full capacity."
            ]
            tables.append(TableSection(
                title="Room Status Details (Sorted by Shortage)",
                data=table_df,
                insights=table_insights
            ))

        # Table 2: Class Summary
        if class_col and capacity_col and available_col:
            class_summary = self.df.groupby(class_col).agg({
                capacity_col: 'sum',
                available_col: 'sum',
                '_shortage': 'sum',
                '_availability_rate': 'mean'
            }).round(1)
            class_summary.columns = ['Total Capacity', 'Total Available', 'Total Shortage', 'Avg Availability %']
            class_summary = class_summary.sort_values('Total Capacity', ascending=False)

            class_insights = [
                f"Summary across {len(class_summary)} room classes.",
                f"Total system capacity: {class_summary['Total Capacity'].sum():,.0f} beds.",
                f"System-wide shortage: {class_summary['Total Shortage'].sum():,.0f} beds.",
            ]
            tables.append(TableSection(
                title="Summary by Room Class",
                data=class_summary.reset_index(),
                insights=class_insights
            ))

        # Recommendations
        recommendations = self._generate_recommendations(
            occupancy_rate, zero_avail_count, critical_rooms, quality, anomalies
        )

        return ComprehensiveDashboard(
            title=title,
            subtitle=subtitle,
            overview=overview,
            overall_insights=overall_insights,
            primary_metrics=primary_metrics,
            secondary_metrics=secondary_metrics,
            sections=sections,
            tables=tables,
            data_quality=quality,
            recommendations=recommendations
        )

    def _generate_comprehensive_room_insights(self, capacity_col, available_col, class_col, name_col,
                                               total_capacity, total_available, occupancy_rate, stats, cat_summary) -> List[str]:
        """Generate comprehensive overall insights"""
        insights = []

        # Insight 1: Overall capacity utilization
        insights.append(
            f"Overall hospital bed utilization stands at {occupancy_rate:.1f}%, with {int(total_capacity - total_available):,} beds currently occupied out of {int(total_capacity):,} total capacity. "
            f"This {'indicates high demand and potential capacity constraints' if occupancy_rate > 75 else 'suggests adequate capacity buffer for patient influx'}."
        )

        # Insight 2: Class distribution analysis
        if class_col and capacity_col:
            class_caps = self.df.groupby(class_col)[capacity_col].sum().sort_values(ascending=False)
            top_3 = class_caps.head(3)
            insights.append(
                f"Capacity is concentrated in {', '.join(top_3.index)}, which together hold {top_3.sum()/class_caps.sum()*100:.1f}% of total beds. "
                f"{top_3.index[0]} alone accounts for {top_3.iloc[0]/class_caps.sum()*100:.1f}% ({int(top_3.iloc[0]):,} beds)."
            )

        # Insight 3: Availability patterns
        if available_col and class_col:
            class_avail = self.df.groupby(class_col)[available_col].sum()
            class_caps = self.df.groupby(class_col)[capacity_col].sum() if capacity_col else class_avail
            avail_rates = (class_avail / class_caps * 100).sort_values()

            low_avail = avail_rates[avail_rates < 50]
            high_avail = avail_rates[avail_rates > 75]

            if len(low_avail) > 0:
                insights.append(
                    f"{', '.join(low_avail.index[:3])} show critical low availability (<50%), indicating severe capacity constraints in these classes. "
                    f"Immediate bed management intervention may be required."
                )

            if len(high_avail) > 0:
                insights.append(
                    f"{', '.join(high_avail.index[:3])} maintain high availability (>75%), representing potential overflow capacity for patient redistribution."
                )

        # Insight 4: Zero availability analysis
        if available_col:
            zero_rooms = self.df[self.df[available_col] == 0]
            if len(zero_rooms) > 0:
                insights.append(
                    f"{len(zero_rooms)} rooms ({len(zero_rooms)/len(self.df)*100:.1f}%) are at full capacity with zero beds available. "
                    f"This affects an estimated {zero_rooms[capacity_col].sum() if capacity_col else len(zero_rooms):,.0f} bed capacity and requires immediate attention."
                )

        # Insight 5: Shortage leaders
        if '_shortage' in self.df.columns and name_col:
            top_short = self.df.nlargest(3, '_shortage')
            insights.append(
                f"Highest shortage concentration: {top_short.iloc[0][name_col]} ({top_short.iloc[0]['_shortage']:.0f} beds), "
                f"{top_short.iloc[1][name_col]} ({top_short.iloc[1]['_shortage']:.0f} beds), and "
                f"{top_short.iloc[2][name_col]} ({top_short.iloc[2]['_shortage']:.0f} beds) together account for "
                f"{top_short['_shortage'].sum()/self.df['_shortage'].sum()*100:.1f}% of total shortage."
            )

        # Insight 6: Statistical distribution
        if capacity_col and capacity_col in stats:
            cap_stats = stats[capacity_col]
            insights.append(
                f"Room capacity ranges from {cap_stats['min']:.0f} to {cap_stats['max']:.0f} beds (mean: {cap_stats['mean']:.1f}, median: {cap_stats['median']:.0f}). "
                f"{'High variability (CV > 1) suggests diverse room types.' if cap_stats['std']/cap_stats['mean'] > 1 else 'Relatively uniform capacity distribution across rooms.'}"
            )

        # Insight 7: Trend indicator (if time data available)
        insights.append(
            f"Based on current patterns, {'proactive capacity planning is recommended' if occupancy_rate > 70 else 'current capacity appears sufficient'}. "
            f"{'Consider activating overflow protocols for high-demand classes.' if occupancy_rate > 85 else 'Monitor for seasonal demand fluctuations.'}"
        )

        # Insight 8: Data quality note
        if self.analyzer.get_data_quality_report()['missing_pct'] > 5:
            insights.append(
                f"Data quality note: {self.analyzer.get_data_quality_report()['missing_pct']:.1f}% missing values detected. "
                f"Recommend data validation to ensure accurate capacity reporting."
            )

        return insights[:10]

    def _generate_recommendations(self, occupancy_rate, zero_avail, critical, quality, anomalies) -> List[str]:
        """Generate actionable recommendations"""
        recs = []

        if occupancy_rate > 85:
            recs.append("🚨 CRITICAL: Occupancy exceeds 85%. Activate emergency capacity protocols and consider patient diversion.")
        elif occupancy_rate > 70:
            recs.append("⚠️ HIGH UTILIZATION: Occupancy above 70%. Review discharge planning to optimize bed turnover.")

        if zero_avail > 0:
            recs.append(f"🔴 {zero_avail} rooms at full capacity. Prioritize discharge in these units or activate overflow areas.")

        if critical > 5:
            recs.append(f"⚠️ {critical} rooms in critical status (≤2 beds). Proactively manage admissions to these units.")

        if quality['missing_pct'] > 5:
            recs.append(f"📊 Data quality issue: {quality['missing_pct']:.1f}% missing data. Review data entry processes.")

        if quality['duplicate_pct'] > 1:
            recs.append(f"📋 {quality['duplicate_pct']:.1f}% duplicate records detected. Deduplicate for accurate reporting.")

        if len(anomalies) > 0:
            recs.append(f"🔍 {len(anomalies)} data anomalies detected. Review outliers for potential data entry errors.")

        recs.append("📈 Implement daily capacity forecasting to anticipate demand fluctuations.")
        recs.append("🔄 Establish inter-unit transfer protocols for load balancing during peak periods.")

        return recs[:6]

    def _build_general_dashboard(self, quality, stats, cat_summary, correlations, anomalies) -> ComprehensiveDashboard:
        """Build general comprehensive dashboard"""
        numeric_cols = self.analyzer.numeric_cols
        categorical_cols = self.analyzer.categorical_cols

        title = "Comprehensive Data Analytics Dashboard"
        subtitle = f"In-depth analysis of {len(self.df):,} records across {len(self.df.columns)} variables"

        overview = f"""This dashboard provides comprehensive analytics for your dataset containing {len(self.df):,} records and {len(self.df.columns)} columns.
The analysis includes {len(numeric_cols)} numeric variables and {len(categorical_cols)} categorical variables.
Data completeness is {quality['completeness']:.1f}% with {quality['duplicate_rows']} duplicate records identified."""

        # Generate insights
        overall_insights = []

        if numeric_cols and numeric_cols[0] in stats:
            s = stats[numeric_cols[0]]
            overall_insights.append(f"{numeric_cols[0]} ranges from {s['min']:,.2f} to {s['max']:,.2f} with mean {s['mean']:,.2f} and standard deviation {s['std']:,.2f}.")

        if categorical_cols and categorical_cols[0] in cat_summary:
            c = cat_summary[categorical_cols[0]]
            overall_insights.append(f"{categorical_cols[0]} has {c['unique_count']} unique values. Most common: '{c['mode']}' ({c['mode_pct']:.1f}% of records).")

        overall_insights.append(f"Data quality: {quality['completeness']:.1f}% complete, {quality['duplicate_pct']:.1f}% duplicates.")

        # Metrics
        primary_metrics = [
            MetricBox("Total Records", f"{len(self.df):,}", "Dataset size", "📊", self.COLORS['primary']),
            MetricBox("Variables", f"{len(self.df.columns)}", "Total columns", "📋", self.COLORS['secondary']),
            MetricBox("Completeness", f"{quality['completeness']:.1f}%", "Data quality", "✅", self.COLORS['success']),
            MetricBox("Duplicates", f"{quality['duplicate_rows']:,}", "Duplicate rows", "🔄", self.COLORS['warning']),
        ]

        secondary_metrics = []
        if numeric_cols:
            secondary_metrics.append(MetricBox("Numeric Cols", f"{len(numeric_cols)}", "", "🔢", self.COLORS['info']))
        if categorical_cols:
            secondary_metrics.append(MetricBox("Categorical", f"{len(categorical_cols)}", "", "📁", self.COLORS['info']))

        # Sections
        sections = []

        if categorical_cols:
            sections.append(InsightSection(
                title=f"Distribution of {categorical_cols[0]}",
                chart_type="pie",
                columns=[categorical_cols[0]],
                insights=[f"Shows distribution across {self.df[categorical_cols[0]].nunique()} categories."]
            ))

        if numeric_cols:
            sections.append(InsightSection(
                title=f"Distribution of {numeric_cols[0]}",
                chart_type="histogram",
                columns=[numeric_cols[0]],
                insights=[f"Histogram showing value distribution."]
            ))

        if len(numeric_cols) >= 2:
            sections.append(InsightSection(
                title="Correlation Analysis",
                chart_type="heatmap",
                columns=numeric_cols[:5],
                insights=["Correlation matrix for numeric variables."]
            ))

        return ComprehensiveDashboard(
            title=title,
            subtitle=subtitle,
            overview=overview,
            overall_insights=overall_insights,
            primary_metrics=primary_metrics,
            secondary_metrics=secondary_metrics,
            sections=sections,
            tables=[],
            data_quality=quality,
            recommendations=["Review data quality metrics.", "Explore correlations for insights."]
        )

    # ==================== CHART CREATION ====================

    def create_chart(self, section: InsightSection) -> Optional[go.Figure]:
        """Create chart for section"""
        try:
            if section.chart_type == "donut":
                return self._create_donut(section)
            elif section.chart_type == "stacked_bar":
                return self._create_stacked_bar(section)
            elif section.chart_type == "bar_horizontal":
                return self._create_horizontal_bar(section)
            elif section.chart_type == "bar_shortage":
                return self._create_shortage_bar(section)
            elif section.chart_type == "bar_rate":
                return self._create_rate_bar(section)
            elif section.chart_type == "histogram":
                return self._create_histogram(section)
            elif section.chart_type == "heatmap":
                return self._create_heatmap(section)
            elif section.chart_type == "pie":
                return self._create_pie(section)
            else:
                return self._create_bar(section)
        except:
            return None

    def _create_donut(self, section: InsightSection) -> go.Figure:
        cat_col, val_col = section.columns[0], section.columns[1]
        data = self.df.groupby(cat_col)[val_col].sum().sort_values(ascending=False)

        fig = go.Figure(data=[go.Pie(
            labels=data.index,
            values=data.values,
            hole=0.5,
            marker_colors=self.COLORS['chart'][:len(data)],
            textinfo='value+percent',
            textposition='outside'
        )])
        fig.update_layout(title=section.title, showlegend=True,
                         legend=dict(orientation='h', yanchor='bottom', y=-0.2))
        return fig

    def _create_stacked_bar(self, section: InsightSection) -> go.Figure:
        cat_col, cap_col, avail_col = section.columns[:3]
        agg = self.df.groupby(cat_col).agg({cap_col: 'sum', avail_col: 'sum'}).sort_values(cap_col, ascending=False)

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Capacity', x=agg.index, y=agg[cap_col],
                            marker_color='#a3bffa', text=agg[cap_col].astype(int), textposition='inside'))
        fig.add_trace(go.Bar(name='Available', x=agg.index, y=agg[avail_col],
                            marker_color='#68d391', text=agg[avail_col].astype(int), textposition='inside'))
        fig.update_layout(title=section.title, barmode='overlay',
                         legend=dict(orientation='h', yanchor='bottom', y=1.02))
        return fig

    def _create_horizontal_bar(self, section: InsightSection) -> go.Figure:
        name_col = section.columns[0]
        val_col = section.columns[1] if len(section.columns) > 1 else None

        if section.options.get('filter') == 'zero_avail':
            avail_col = self._find_col(['tersedia', 'available'])
            df_filtered = self.df[self.df[avail_col] == 0] if avail_col else self.df
        else:
            df_filtered = self.df

        if val_col and val_col in df_filtered.columns:
            data = df_filtered.groupby(name_col)[val_col].sum().sort_values(ascending=True).tail(10)
        else:
            data = df_filtered[name_col].value_counts().tail(10)

        fig = px.bar(x=data.values, y=data.index, orientation='h',
                    title=section.title, color_discrete_sequence=[self.COLORS['primary']])
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_title='')
        return fig

    def _create_shortage_bar(self, section: InsightSection) -> go.Figure:
        name_col, val_col = section.columns[:2]
        data = self.df.groupby(name_col)[val_col].sum().sort_values(ascending=False).head(10)

        fig = px.bar(x=data.index, y=data.values, title=section.title,
                    color_discrete_sequence=[self.COLORS['primary']], text=data.values.astype(int))
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_title='Shortage (Beds)')
        return fig

    def _create_rate_bar(self, section: InsightSection) -> go.Figure:
        cat_col = section.columns[0]
        rate_col = section.columns[1] if len(section.columns) > 1 else '_availability_rate'

        data = self.df.groupby(cat_col)[rate_col].mean().sort_values(ascending=False)

        fig = px.bar(x=data.index, y=data.values, title=section.title,
                    color_discrete_sequence=[self.COLORS['primary']],
                    text=[f'{v:.1f}%' for v in data.values])
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, xaxis_title='', yaxis_title='Availability Rate %')
        return fig

    def _create_histogram(self, section: InsightSection) -> go.Figure:
        col = section.columns[0]
        fig = px.histogram(self.df, x=col, title=section.title,
                          color_discrete_sequence=[self.COLORS['primary']], nbins=20)
        fig.update_layout(showlegend=False)
        return fig

    def _create_heatmap(self, section: InsightSection) -> go.Figure:
        cols = [c for c in section.columns if c in self.df.columns and pd.api.types.is_numeric_dtype(self.df[c])]
        if len(cols) < 2:
            return None
        corr = self.df[cols].corr()

        fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.index,
                                        colorscale='RdBu', zmid=0, text=np.round(corr.values, 2),
                                        texttemplate='%{text}', textfont={"size": 10}))
        fig.update_layout(title=section.title)
        return fig

    def _create_pie(self, section: InsightSection) -> go.Figure:
        col = section.columns[0]
        data = self.df[col].value_counts().head(10)
        fig = px.pie(values=data.values, names=data.index, title=section.title,
                    color_discrete_sequence=self.COLORS['chart'])
        return fig

    def _create_bar(self, section: InsightSection) -> go.Figure:
        col = section.columns[0]
        data = self.df[col].value_counts().head(15)
        fig = px.bar(x=data.index, y=data.values, title=section.title,
                    color_discrete_sequence=[self.COLORS['primary']])
        return fig

    # ==================== RENDER ====================

    def render(self, config: Optional[ComprehensiveDashboard] = None):
        """Render comprehensive dashboard"""
        config = config or self.config
        if not config:
            st.warning("Generate dashboard first.")
            return

        # Header
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 16px; margin-bottom: 24px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">{config.title}</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1rem;">{config.subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

        # Overview
        st.markdown(f"""
        <div style="background: #fff; padding: 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #667eea;">
            <h3 style="margin: 0 0 12px 0; color: #2d3748; font-size: 1.1rem;">📋 Overview</h3>
            <p style="margin: 0; color: #4a5568; line-height: 1.8; font-size: 0.95rem;">{config.overview}</p>
        </div>
        """, unsafe_allow_html=True)

        # Overall Insights
        if config.overall_insights:
            st.markdown("""
            <div style="background: #fff; padding: 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <h3 style="margin: 0 0 16px 0; color: #2d3748; font-size: 1.1rem;">💡 Overall Insights</h3>
            """, unsafe_allow_html=True)

            for insight in config.overall_insights:
                st.markdown(f"""
                <div style="display: flex; align-items: flex-start; margin-bottom: 14px; padding: 12px; background: #f7fafc; border-radius: 8px; border-left: 3px solid #667eea;">
                    <span style="color: #667eea; margin-right: 12px; font-size: 1.1rem;">•</span>
                    <p style="margin: 0; color: #4a5568; line-height: 1.6; font-size: 0.9rem;">{insight}</p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Primary Metrics
        if config.primary_metrics:
            st.markdown("<h3 style='color: #2d3748; margin: 24px 0 16px 0;'>📊 Key Metrics</h3>", unsafe_allow_html=True)
            cols = st.columns(len(config.primary_metrics))
            for i, m in enumerate(config.primary_metrics):
                with cols[i]:
                    st.markdown(f"""
                    <div style="background: #fff; padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid {m.color};">
                        <div style="font-size: 2rem; margin-bottom: 8px;">{m.icon}</div>
                        <div style="font-size: 0.75rem; color: #718096; text-transform: uppercase; letter-spacing: 1px;">{m.title}</div>
                        <div style="font-size: 2.2rem; font-weight: 700; color: {m.color}; margin: 8px 0;">{m.value}</div>
                        <div style="font-size: 0.8rem; color: #a0aec0;">{m.subtitle}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Secondary Metrics
        if config.secondary_metrics:
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(len(config.secondary_metrics))
            for i, m in enumerate(config.secondary_metrics):
                with cols[i]:
                    st.markdown(f"""
                    <div style="background: #fff; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid {m.color};">
                        <div style="font-size: 1.5rem; margin-bottom: 6px;">{m.icon}</div>
                        <div style="font-size: 0.7rem; color: #718096; text-transform: uppercase;">{m.title}</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: {m.color};">{m.value}</div>
                        <div style="font-size: 0.75rem; color: #a0aec0;">{m.subtitle}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Chart Sections
        for section in config.sections:
            st.markdown(f"""
            <div style="background: #fff; padding: 24px; border-radius: 12px; margin: 24px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            """, unsafe_allow_html=True)

            col_chart, col_insight = st.columns([3, 2])

            with col_chart:
                fig = self.create_chart(section)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

            with col_insight:
                st.markdown(f"""
                <h4 style="color: #2d3748; margin: 0 0 16px 0; font-size: 1rem;">🔍 Key Insights</h4>
                """, unsafe_allow_html=True)
                for insight in section.insights:
                    st.markdown(f"""
                    <div style="display: flex; align-items: flex-start; margin-bottom: 12px;">
                        <span style="color: #667eea; margin-right: 10px;">•</span>
                        <p style="margin: 0; color: #4a5568; font-size: 0.85rem; line-height: 1.5;">{insight}</p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Tables
        for table in config.tables:
            st.markdown(f"""
            <div style="background: #fff; padding: 24px; border-radius: 12px; margin: 24px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            """, unsafe_allow_html=True)

            col_insight, col_table = st.columns([1, 2])

            with col_insight:
                st.markdown(f"<h4 style='color: #2d3748;'>🔍 Key Insights</h4>", unsafe_allow_html=True)
                for insight in table.insights:
                    st.markdown(f"""
                    <div style="display: flex; align-items: flex-start; margin-bottom: 10px;">
                        <span style="color: #667eea; margin-right: 10px;">•</span>
                        <p style="margin: 0; color: #4a5568; font-size: 0.85rem;">{insight}</p>
                    </div>
                    """, unsafe_allow_html=True)

            with col_table:
                st.markdown(f"<h4 style='color: #2d3748;'>{table.title}</h4>", unsafe_allow_html=True)
                st.dataframe(table.data, use_container_width=True, hide_index=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Recommendations
        if config.recommendations:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f6f9fc 0%, #edf2f7 100%); padding: 24px; border-radius: 12px; margin: 24px 0; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 16px 0; color: #2d3748; font-size: 1.1rem;">🎯 Recommendations & Actions</h3>
            """, unsafe_allow_html=True)

            for rec in config.recommendations:
                st.markdown(f"""
                <div style="padding: 12px 16px; margin-bottom: 10px; background: #fff; border-radius: 8px; border-left: 4px solid #667eea;">
                    <p style="margin: 0; color: #4a5568; font-size: 0.9rem;">{rec}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Data Quality Footer
        st.markdown(f"""
        <div style="background: #fff; padding: 20px; border-radius: 12px; margin-top: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="margin: 0 0 12px 0; color: #2d3748; font-size: 0.95rem;">📈 Data Quality Summary</h4>
            <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                <span style="color: #718096; font-size: 0.85rem;">Rows: <strong>{config.data_quality['total_rows']:,}</strong></span>
                <span style="color: #718096; font-size: 0.85rem;">Columns: <strong>{config.data_quality['total_columns']}</strong></span>
                <span style="color: #718096; font-size: 0.85rem;">Completeness: <strong>{config.data_quality['completeness']:.1f}%</strong></span>
                <span style="color: #718096; font-size: 0.85rem;">Duplicates: <strong>{config.data_quality['duplicate_rows']:,}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_dashboard_tab(df: pd.DataFrame, ai_engine=None):
    """Render comprehensive dashboard tab"""
    st.subheader("Comprehensive Data Analytics")
    st.caption("Advanced analysis by AI Data Engineer & Data Scientist")

    builder = ComprehensiveDashboardBuilder(df, ai_engine)

    if st.button("🚀 Generate Comprehensive Dashboard", type="primary"):
        with st.spinner("Analyzing data and generating comprehensive insights..."):
            config = builder.generate()
            st.session_state['dashboard_config'] = config
            st.session_state['dashboard_builder'] = builder
        st.rerun()

    if 'dashboard_config' in st.session_state and 'dashboard_builder' in st.session_state:
        st.markdown("---")
        builder = st.session_state['dashboard_builder']
        builder.render(st.session_state['dashboard_config'])
        return builder

    st.info("Click 'Generate Comprehensive Dashboard' to create an advanced analytics dashboard.")
    return None


# Backward compatibility alias
DashboardBuilder = ComprehensiveDashboardBuilder
