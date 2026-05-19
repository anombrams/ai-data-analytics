"""
Data Analyzer Module
Auto-detect column types, generate statistics, and assess data quality
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ColumnType(Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    inferred_type: ColumnType
    missing_count: int
    missing_pct: float
    unique_count: int
    unique_pct: float
    sample_values: List[Any]
    statistics: Dict[str, Any]


@dataclass
class DataQuality:
    score: float  # 0-100
    completeness: float
    uniqueness: float
    consistency: float
    issues: List[str]
    recommendations: List[str]


class DataAnalyzer:
    """Analyzes DataFrame structure, types, and quality"""

    # Thresholds for type inference
    CATEGORICAL_THRESHOLD = 20  # Max unique values for categorical
    TEXT_MIN_AVG_LENGTH = 50  # Min avg length to consider as text

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._column_info: Optional[Dict[str, ColumnInfo]] = None
        self._quality: Optional[DataQuality] = None

    def analyze(self) -> Dict[str, Any]:
        """Run full analysis on the DataFrame"""
        return {
            'shape': self.get_shape(),
            'columns': self.get_column_info(),
            'quality': self.assess_quality(),
            'summary': self.get_summary(),
            'schema': self.get_schema_for_ai()
        }

    def get_shape(self) -> Dict[str, int]:
        """Get DataFrame dimensions"""
        return {
            'rows': len(self.df),
            'columns': len(self.df.columns)
        }

    def get_column_info(self) -> Dict[str, ColumnInfo]:
        """Analyze each column"""
        if self._column_info is not None:
            return self._column_info

        self._column_info = {}

        for col in self.df.columns:
            series = self.df[col]

            # Basic stats
            missing_count = series.isna().sum()
            missing_pct = (missing_count / len(series)) * 100 if len(series) > 0 else 0
            unique_count = series.nunique()
            unique_pct = (unique_count / len(series)) * 100 if len(series) > 0 else 0

            # Infer type
            inferred_type = self._infer_column_type(series)

            # Get sample values (non-null)
            non_null = series.dropna()
            sample_values = non_null.head(5).tolist() if len(non_null) > 0 else []

            # Calculate statistics based on type
            statistics = self._calculate_statistics(series, inferred_type)

            self._column_info[col] = ColumnInfo(
                name=col,
                dtype=str(series.dtype),
                inferred_type=inferred_type,
                missing_count=int(missing_count),
                missing_pct=round(missing_pct, 2),
                unique_count=int(unique_count),
                unique_pct=round(unique_pct, 2),
                sample_values=sample_values,
                statistics=statistics
            )

        return self._column_info

    def _infer_column_type(self, series: pd.Series) -> ColumnType:
        """Infer the semantic type of a column"""
        # Drop nulls for analysis
        non_null = series.dropna()

        if len(non_null) == 0:
            return ColumnType.UNKNOWN

        # Check if boolean
        if series.dtype == bool or set(non_null.unique()).issubset({True, False, 0, 1, '0', '1', 'true', 'false', 'True', 'False'}):
            return ColumnType.BOOLEAN

        # Check if datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.DATETIME

        # Try to parse as datetime
        if series.dtype == object:
            try:
                pd.to_datetime(non_null.head(100), errors='raise')
                return ColumnType.DATETIME
            except:
                pass

        # Check if numeric
        if pd.api.types.is_numeric_dtype(series):
            unique_count = non_null.nunique()
            if unique_count <= self.CATEGORICAL_THRESHOLD and unique_count < len(non_null) * 0.5:
                return ColumnType.CATEGORICAL
            return ColumnType.NUMERIC

        # For object/string types
        if series.dtype == object:
            unique_count = non_null.nunique()

            # Check if categorical (low cardinality)
            if unique_count <= self.CATEGORICAL_THRESHOLD:
                return ColumnType.CATEGORICAL

            # Check if text (long strings)
            avg_length = non_null.astype(str).str.len().mean()
            if avg_length > self.TEXT_MIN_AVG_LENGTH:
                return ColumnType.TEXT

            # Default to categorical for strings
            return ColumnType.CATEGORICAL

        return ColumnType.UNKNOWN

    def _calculate_statistics(self, series: pd.Series, col_type: ColumnType) -> Dict[str, Any]:
        """Calculate statistics based on column type"""
        stats = {}
        non_null = series.dropna()

        if len(non_null) == 0:
            return stats

        if col_type == ColumnType.NUMERIC:
            stats = {
                'mean': round(float(non_null.mean()), 4),
                'median': round(float(non_null.median()), 4),
                'std': round(float(non_null.std()), 4),
                'min': float(non_null.min()),
                'max': float(non_null.max()),
                'q25': round(float(non_null.quantile(0.25)), 4),
                'q75': round(float(non_null.quantile(0.75)), 4),
            }
        elif col_type == ColumnType.CATEGORICAL:
            value_counts = non_null.value_counts()
            stats = {
                'mode': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                'mode_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                'top_values': {str(k): int(v) for k, v in value_counts.head(10).items()}
            }
        elif col_type == ColumnType.DATETIME:
            try:
                dt_series = pd.to_datetime(non_null, errors='coerce').dropna()
                if len(dt_series) > 0:
                    stats = {
                        'min': str(dt_series.min()),
                        'max': str(dt_series.max()),
                        'range_days': (dt_series.max() - dt_series.min()).days
                    }
            except:
                pass
        elif col_type == ColumnType.TEXT:
            str_series = non_null.astype(str)
            stats = {
                'avg_length': round(str_series.str.len().mean(), 2),
                'min_length': int(str_series.str.len().min()),
                'max_length': int(str_series.str.len().max()),
            }

        return stats

    def assess_quality(self) -> DataQuality:
        """Assess overall data quality"""
        if self._quality is not None:
            return self._quality

        issues = []
        recommendations = []

        # Completeness (% of non-null values)
        total_cells = self.df.size
        missing_cells = self.df.isna().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells) * 100 if total_cells > 0 else 0

        if completeness < 80:
            issues.append(f"Low completeness: {completeness:.1f}% of data is filled")
            recommendations.append("Consider handling missing values through imputation or removal")

        # Check for columns with high missing values
        col_info = self.get_column_info()
        for col, info in col_info.items():
            if info.missing_pct > 50:
                issues.append(f"Column '{col}' has {info.missing_pct}% missing values")

        # Uniqueness (check for duplicate rows)
        duplicate_count = self.df.duplicated().sum()
        duplicate_pct = (duplicate_count / len(self.df)) * 100 if len(self.df) > 0 else 0
        uniqueness = 100 - duplicate_pct

        if duplicate_pct > 10:
            issues.append(f"{duplicate_count} duplicate rows found ({duplicate_pct:.1f}%)")
            recommendations.append("Consider removing duplicate rows")

        # Consistency checks
        consistency_issues = 0

        # Check for mixed types in object columns
        for col in self.df.select_dtypes(include=['object']).columns:
            series = self.df[col].dropna()
            if len(series) > 0:
                # Check if column has mixed numeric and non-numeric values
                numeric_count = pd.to_numeric(series, errors='coerce').notna().sum()
                if 0 < numeric_count < len(series):
                    consistency_issues += 1
                    issues.append(f"Column '{col}' has mixed data types")

        consistency = 100 - (consistency_issues / len(self.df.columns) * 100) if len(self.df.columns) > 0 else 100

        # Calculate overall score (weighted average)
        score = (completeness * 0.4 + uniqueness * 0.3 + consistency * 0.3)

        # Add general recommendations
        if len(self.df) < 100:
            recommendations.append("Dataset is small. Results may not be statistically significant")

        if not recommendations:
            recommendations.append("Data quality looks good!")

        self._quality = DataQuality(
            score=round(score, 2),
            completeness=round(completeness, 2),
            uniqueness=round(uniqueness, 2),
            consistency=round(consistency, 2),
            issues=issues,
            recommendations=recommendations
        )

        return self._quality

    def get_summary(self) -> Dict[str, Any]:
        """Get a human-readable summary"""
        shape = self.get_shape()
        quality = self.assess_quality()
        col_info = self.get_column_info()

        # Count column types
        type_counts = {}
        for info in col_info.values():
            type_name = info.inferred_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            'total_rows': shape['rows'],
            'total_columns': shape['columns'],
            'column_types': type_counts,
            'quality_score': quality.score,
            'missing_values': self.df.isna().sum().sum(),
            'duplicate_rows': self.df.duplicated().sum()
        }

    def get_schema_for_ai(self) -> str:
        """Generate schema description for AI context"""
        col_info = self.get_column_info()
        lines = ["DataFrame Schema:"]
        lines.append(f"- Total rows: {len(self.df)}")
        lines.append(f"- Total columns: {len(self.df.columns)}")
        lines.append("\nColumns:")

        for col, info in col_info.items():
            type_str = f"{info.inferred_type.value} ({info.dtype})"
            missing_str = f"{info.missing_pct}% missing" if info.missing_pct > 0 else "no missing"
            lines.append(f"  - {col}: {type_str}, {info.unique_count} unique values, {missing_str}")

            if info.inferred_type == ColumnType.NUMERIC and info.statistics:
                stats = info.statistics
                lines.append(f"    Range: {stats.get('min', 'N/A')} to {stats.get('max', 'N/A')}, Mean: {stats.get('mean', 'N/A')}")

            if info.inferred_type == ColumnType.CATEGORICAL and info.statistics:
                top_vals = list(info.statistics.get('top_values', {}).keys())[:5]
                if top_vals:
                    lines.append(f"    Top values: {', '.join(top_vals)}")

        return "\n".join(lines)

    def get_sample_data(self, n: int = 5) -> str:
        """Get sample data as formatted string"""
        return self.df.head(n).to_string()

    def get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns"""
        col_info = self.get_column_info()
        return [col for col, info in col_info.items() if info.inferred_type == ColumnType.NUMERIC]

    def get_categorical_columns(self) -> List[str]:
        """Get list of categorical columns"""
        col_info = self.get_column_info()
        return [col for col, info in col_info.items() if info.inferred_type == ColumnType.CATEGORICAL]

    def get_datetime_columns(self) -> List[str]:
        """Get list of datetime columns"""
        col_info = self.get_column_info()
        return [col for col, info in col_info.items() if info.inferred_type == ColumnType.DATETIME]
