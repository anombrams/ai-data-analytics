"""
AI Engine Module
Claude API integration for natural language data analysis
"""

import os
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import anthropic
import streamlit as st


@dataclass
class AIResponse:
    explanation: str
    code: Optional[str] = None
    chart_type: Optional[str] = None
    error: Optional[str] = None
    execution_result: Optional[Any] = None


class AIEngine:
    """Claude API integration for data analysis"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI Engine with API key"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            try:
                self.api_key = st.secrets.get('ANTHROPIC_API_KEY')
            except:
                pass

        self.client = None
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        self.model = "claude-sonnet-4-20250514"

    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return self.client is not None

    def analyze_query(self, query: str, schema: str, sample_data: str, df: pd.DataFrame) -> AIResponse:
        """
        Process natural language query and return analysis

        Args:
            query: User's natural language query
            schema: DataFrame schema description
            sample_data: Sample rows from DataFrame
            df: The actual DataFrame for code execution

        Returns:
            AIResponse with explanation, code, and results
        """
        if not self.is_configured():
            return AIResponse(
                explanation="API key not configured. Please set ANTHROPIC_API_KEY environment variable.",
                error="API key not configured"
            )

        # Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, schema, sample_data)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Parse response
            ai_text = response.content[0].text
            parsed = self._parse_response(ai_text)

            # Execute code if present
            if parsed.code:
                execution_result, error = self._execute_code(parsed.code, df)
                parsed.execution_result = execution_result
                if error:
                    parsed.error = error

            return parsed

        except anthropic.APIError as e:
            return AIResponse(
                explanation=f"API Error: {str(e)}",
                error=str(e)
            )
        except Exception as e:
            return AIResponse(
                explanation=f"Error processing query: {str(e)}",
                error=str(e)
            )

    def _build_system_prompt(self) -> str:
        """Build system prompt for Claude"""
        return """You are a data analyst assistant helping users analyze their data. You have access to a pandas DataFrame called `df`.

Your capabilities:
1. Analyze data and provide insights
2. Generate Python code using pandas for data manipulation
3. Create visualizations using plotly
4. Answer questions about the data

Rules:
1. Always use the variable name `df` for the DataFrame
2. For visualizations, use plotly and assign the figure to variable `fig`
3. Keep code simple and focused on the user's request
4. Provide clear explanations in English
5. If the query is ambiguous, make reasonable assumptions and state them
6. For aggregations, always handle missing values appropriately

Response format - always structure your response with these sections:
---EXPLANATION---
Your explanation here

---CODE---
# Python code here (optional, only if needed)

---CHART_TYPE---
chart type here (optional: bar, line, pie, scatter, histogram, box, heatmap, none)
---END---

If no code is needed, omit the CODE section.
If no chart is needed, omit the CHART_TYPE section or set it to "none"."""

    def _build_user_prompt(self, query: str, schema: str, sample_data: str) -> str:
        """Build user prompt with context"""
        return f"""Here is the data context:

{schema}

Sample Data (first 5 rows):
{sample_data}

User Query: {query}

Please analyze this request and provide a response. If code is needed, provide executable Python code using pandas/plotly."""

    def _parse_response(self, response_text: str) -> AIResponse:
        """Parse Claude's response into structured format"""
        explanation = ""
        code = None
        chart_type = None

        # Extract explanation
        expl_match = re.search(r'---EXPLANATION---\s*(.*?)(?=---CODE---|---CHART_TYPE---|---END---|$)', response_text, re.DOTALL)
        if expl_match:
            explanation = expl_match.group(1).strip()
        else:
            # If no structured format, use the whole response as explanation
            explanation = response_text.strip()

        # Extract code
        code_match = re.search(r'---CODE---\s*(.*?)(?=---CHART_TYPE---|---END---|$)', response_text, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            # Remove markdown code blocks if present
            code = re.sub(r'^```python\s*', '', code)
            code = re.sub(r'^```\s*', '', code)
            code = re.sub(r'\s*```$', '', code)
            code = code.strip()

        # Extract chart type
        chart_match = re.search(r'---CHART_TYPE---\s*(.*?)(?=---END---|$)', response_text, re.DOTALL)
        if chart_match:
            chart_type = chart_match.group(1).strip().lower()
            if chart_type == 'none':
                chart_type = None

        return AIResponse(
            explanation=explanation,
            code=code if code else None,
            chart_type=chart_type
        )

    def _execute_code(self, code: str, df: pd.DataFrame) -> Tuple[Any, Optional[str]]:
        """
        Execute generated code in a sandboxed environment

        Args:
            code: Python code to execute
            df: DataFrame to operate on

        Returns:
            Tuple of (result, error_message)
        """
        # Create restricted globals
        safe_globals = {
            'pd': pd,
            'np': np,
            'df': df.copy(),  # Work on a copy
            '__builtins__': {
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'print': print,
                'isinstance': isinstance,
                'type': type,
            }
        }

        # Add plotly for visualizations
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            safe_globals['px'] = px
            safe_globals['go'] = go
        except ImportError:
            pass

        local_vars = {}

        try:
            # Execute the code
            exec(code, safe_globals, local_vars)

            # Check for common result variables
            result = None

            # Priority: fig (for charts), result, then any DataFrame
            if 'fig' in local_vars:
                result = local_vars['fig']
            elif 'result' in local_vars:
                result = local_vars['result']
            elif 'output' in local_vars:
                result = local_vars['output']
            else:
                # Look for any DataFrame or figure in local vars
                for var_name, var_value in local_vars.items():
                    if isinstance(var_value, pd.DataFrame):
                        result = var_value
                        break
                    elif hasattr(var_value, 'show'):  # Plotly figure
                        result = var_value
                        break

            # If still no result, check if df was modified
            if result is None and 'df' in local_vars:
                # Check if local df is different from original
                if not local_vars['df'].equals(safe_globals['df']):
                    result = local_vars['df']

            return result, None

        except SyntaxError as e:
            return None, f"Syntax error in generated code: {str(e)}"
        except Exception as e:
            return None, f"Execution error: {str(e)}"

    def get_insights(self, schema: str, sample_data: str, summary: Dict[str, Any]) -> AIResponse:
        """
        Generate automatic insights for the dataset

        Args:
            schema: DataFrame schema description
            sample_data: Sample rows
            summary: Data summary dictionary

        Returns:
            AIResponse with insights
        """
        if not self.is_configured():
            return AIResponse(
                explanation="API key not configured.",
                error="API key not configured"
            )

        prompt = f"""Analyze this dataset and provide key insights:

{schema}

Sample Data:
{sample_data}

Summary Statistics:
- Total rows: {summary.get('total_rows', 'N/A')}
- Total columns: {summary.get('total_columns', 'N/A')}
- Missing values: {summary.get('missing_values', 'N/A')}
- Duplicate rows: {summary.get('duplicate_rows', 'N/A')}
- Data quality score: {summary.get('quality_score', 'N/A')}

Please provide:
1. Executive Summary (2-3 sentences overview)
2. Key Findings (3-5 bullet points)
3. Data Quality Assessment
4. Recommended Analyses
5. Potential Issues or Concerns

Keep the response concise and actionable."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            return AIResponse(
                explanation=response.content[0].text
            )

        except Exception as e:
            return AIResponse(
                explanation=f"Error generating insights: {str(e)}",
                error=str(e)
            )

    def suggest_visualizations(self, schema: str, column_types: Dict[str, str]) -> AIResponse:
        """
        Suggest appropriate visualizations based on data

        Args:
            schema: DataFrame schema description
            column_types: Dictionary of column names to their types

        Returns:
            AIResponse with visualization suggestions
        """
        if not self.is_configured():
            return AIResponse(
                explanation="API key not configured.",
                error="API key not configured"
            )

        prompt = f"""Based on this dataset schema, suggest the most insightful visualizations:

{schema}

Column Types:
{column_types}

For each suggestion, provide:
1. Chart type
2. Which columns to use
3. What insight it would reveal

Suggest 3-5 visualizations, prioritized by potential insight value."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            return AIResponse(
                explanation=response.content[0].text
            )

        except Exception as e:
            return AIResponse(
                explanation=f"Error suggesting visualizations: {str(e)}",
                error=str(e)
            )

    def generate_dashboard_config(self, schema: str, sample_data: str, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete dashboard configuration using AI

        Args:
            schema: DataFrame schema description
            sample_data: Sample rows from DataFrame
            summary: Data summary dictionary

        Returns:
            Dictionary with dashboard configuration
        """
        if not self.is_configured():
            return {"error": "API key not configured"}

        prompt = f"""Analyze this dataset and create a complete dashboard configuration.

{schema}

Sample Data:
{sample_data}

Summary:
- Total rows: {summary.get('total_rows', 'N/A')}
- Total columns: {summary.get('total_columns', 'N/A')}
- Column types: {summary.get('column_types', {})}

Create a JSON dashboard configuration with:

1. "title": A descriptive dashboard title
2. "kpis": Array of 3-5 most important KPIs. Each KPI should have:
   - "title": Display name
   - "column": Column to aggregate
   - "aggregation": One of "sum", "mean", "count", "max", "min", "unique"
3. "charts": Array of 3-8 visualizations based on data complexity. Each chart:
   - "type": One of "bar", "line", "pie", "scatter", "histogram", "box", "heatmap", "area"
   - "title": Chart title
   - "columns": Array of column names to use
   - "description": Brief description of the insight
4. "layout": Grid layout based on chart count:
   - 2-3 charts: "1x2" or "1x3"
   - 4 charts: "2x2"
   - 5-6 charts: "2x3"
   - 7-9 charts: "3x3"
5. "insights": 2-4 sentences summarizing key findings
6. "filters": Array of 1-3 column names good for interactive filtering (categorical with <20 unique values)

Rules:
- Choose chart types appropriate for the data types
- Bar/Pie for categorical distributions
- Line for time series
- Scatter for relationships between numeric columns
- Histogram for numeric distributions
- Heatmap for correlations
- Prioritize insights over quantity

Respond with ONLY valid JSON, no explanation or markdown."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Try to extract JSON
            import json
            import re

            # Remove markdown code blocks if present
            json_text = response_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            return json.loads(json_text.strip())

        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse AI response: {str(e)}"}
        except Exception as e:
            return {"error": f"Error generating dashboard config: {str(e)}"}

    def generate_dashboard_insights(self, schema: str, sample_data: str, chart_types: list) -> str:
        """
        Generate written insights for a dashboard

        Args:
            schema: DataFrame schema
            sample_data: Sample data rows
            chart_types: List of chart types being displayed

        Returns:
            Insights text string
        """
        if not self.is_configured():
            return "AI insights unavailable - API key not configured."

        prompt = f"""Based on this data, write 3-4 concise sentences of key insights that would be valuable for a business report.

{schema}

Sample Data:
{sample_data}

The dashboard includes these visualizations: {', '.join(chart_types)}

Write insights that:
1. Highlight the most significant patterns or trends
2. Note any anomalies or interesting findings
3. Suggest potential areas for further investigation
4. Are specific with numbers when possible

Keep it concise and actionable."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            return f"Unable to generate insights: {str(e)}"
