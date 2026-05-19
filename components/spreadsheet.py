"""
Spreadsheet Component
Editable grid with Excel-like functionality including formulas
"""

import pandas as pd
import numpy as np
import streamlit as st
import re
from typing import Optional, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class CellChange:
    """Represents a single cell change for undo/redo"""
    row: int
    column: str
    old_value: Any
    new_value: Any
    timestamp: float = 0.0


@dataclass
class SpreadsheetState:
    """Tracks spreadsheet state for undo/redo"""
    history: List[pd.DataFrame] = field(default_factory=list)
    current_index: int = -1
    max_history: int = 50


class FormulaEngine:
    """Parses and evaluates spreadsheet formulas"""

    # Supported functions
    FUNCTIONS = {
        'SUM': lambda values: sum(v for v in values if pd.notna(v) and isinstance(v, (int, float))),
        'AVG': lambda values: np.nanmean([v for v in values if isinstance(v, (int, float))]),
        'AVERAGE': lambda values: np.nanmean([v for v in values if isinstance(v, (int, float))]),
        'COUNT': lambda values: sum(1 for v in values if pd.notna(v)),
        'COUNTA': lambda values: sum(1 for v in values if pd.notna(v) and v != ''),
        'MIN': lambda values: min((v for v in values if pd.notna(v) and isinstance(v, (int, float))), default=0),
        'MAX': lambda values: max((v for v in values if pd.notna(v) and isinstance(v, (int, float))), default=0),
        'MEDIAN': lambda values: np.nanmedian([v for v in values if isinstance(v, (int, float))]),
        'STDEV': lambda values: np.nanstd([v for v in values if isinstance(v, (int, float))]),
        'VAR': lambda values: np.nanvar([v for v in values if isinstance(v, (int, float))]),
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._column_letter_map = self._create_column_map()

    def _create_column_map(self) -> Dict[str, str]:
        """Create mapping from Excel-style letters (A, B, C...) to column names"""
        mapping = {}
        for i, col in enumerate(self.df.columns):
            # Convert index to letter (A=0, B=1, ..., Z=25, AA=26, etc.)
            letter = self._index_to_letter(i)
            mapping[letter] = col
        return mapping

    def _index_to_letter(self, index: int) -> str:
        """Convert column index to Excel-style letter"""
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord('A')) + result
            index = index // 26 - 1
        return result

    def _letter_to_index(self, letter: str) -> int:
        """Convert Excel-style letter to column index"""
        result = 0
        for char in letter.upper():
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result - 1

    def _parse_cell_reference(self, ref: str) -> Tuple[Optional[str], Optional[int]]:
        """Parse cell reference like 'A1' into (column_letter, row_number)"""
        match = re.match(r'^([A-Za-z]+)(\d+)$', ref.strip())
        if match:
            col_letter = match.group(1).upper()
            row_num = int(match.group(2)) - 1  # Convert to 0-indexed
            return col_letter, row_num
        return None, None

    def _parse_range(self, range_str: str) -> List[Any]:
        """Parse range like 'A1:A10' and return values"""
        values = []

        if ':' in range_str:
            # Range reference (A1:B5)
            start, end = range_str.split(':')
            start_col, start_row = self._parse_cell_reference(start)
            end_col, end_row = self._parse_cell_reference(end)

            if all(v is not None for v in [start_col, start_row, end_col, end_row]):
                start_col_idx = self._letter_to_index(start_col)
                end_col_idx = self._letter_to_index(end_col)

                for col_idx in range(start_col_idx, end_col_idx + 1):
                    col_letter = self._index_to_letter(col_idx)
                    if col_letter in self._column_letter_map:
                        col_name = self._column_letter_map[col_letter]
                        for row_idx in range(start_row, end_row + 1):
                            if 0 <= row_idx < len(self.df):
                                values.append(self.df.iloc[row_idx][col_name])
        else:
            # Single cell reference
            col_letter, row_num = self._parse_cell_reference(range_str)
            if col_letter and row_num is not None:
                if col_letter in self._column_letter_map:
                    col_name = self._column_letter_map[col_letter]
                    if 0 <= row_num < len(self.df):
                        values.append(self.df.iloc[row_num][col_name])

        return values

    def _get_cell_value(self, ref: str) -> Any:
        """Get value from a single cell reference"""
        col_letter, row_num = self._parse_cell_reference(ref)
        if col_letter and row_num is not None:
            if col_letter in self._column_letter_map:
                col_name = self._column_letter_map[col_letter]
                if 0 <= row_num < len(self.df):
                    return self.df.iloc[row_num][col_name]
        return None

    def evaluate(self, formula: str) -> Tuple[Any, Optional[str]]:
        """
        Evaluate a formula and return (result, error)

        Supported formulas:
        - =SUM(A1:A10)
        - =AVG(B1:B5)
        - =COUNT(C1:C100)
        - =MIN(D1:D50)
        - =MAX(E1:E50)
        - =IF(A1>10, "Yes", "No")
        - =VLOOKUP(value, A1:B10, 2)
        - =CONCATENATE(A1, " ", B1)
        """
        if not formula.startswith('='):
            return formula, None

        formula = formula[1:].strip()  # Remove leading =

        try:
            # Check for function calls
            func_match = re.match(r'^(\w+)\((.*)\)$', formula, re.IGNORECASE)

            if func_match:
                func_name = func_match.group(1).upper()
                args_str = func_match.group(2)

                # Handle IF function
                if func_name == 'IF':
                    return self._evaluate_if(args_str)

                # Handle VLOOKUP function
                elif func_name == 'VLOOKUP':
                    return self._evaluate_vlookup(args_str)

                # Handle CONCATENATE function
                elif func_name == 'CONCATENATE':
                    return self._evaluate_concatenate(args_str)

                # Handle aggregate functions (SUM, AVG, etc.)
                elif func_name in self.FUNCTIONS:
                    values = self._parse_range(args_str.strip())
                    result = self.FUNCTIONS[func_name](values)
                    return result, None

                else:
                    return None, f"Unknown function: {func_name}"

            # Simple cell reference
            col_letter, row_num = self._parse_cell_reference(formula)
            if col_letter and row_num is not None:
                return self._get_cell_value(formula), None

            # Try to evaluate as simple expression
            return None, "Invalid formula"

        except Exception as e:
            return None, str(e)

    def _evaluate_if(self, args_str: str) -> Tuple[Any, Optional[str]]:
        """Evaluate IF(condition, true_value, false_value)"""
        # Simple parsing - split by comma but handle nested functions
        parts = self._split_args(args_str)

        if len(parts) != 3:
            return None, "IF requires 3 arguments: condition, true_value, false_value"

        condition_str, true_val_str, false_val_str = parts

        # Evaluate condition
        condition_result = self._evaluate_condition(condition_str.strip())

        # Return appropriate value
        if condition_result:
            return self._parse_value(true_val_str.strip()), None
        else:
            return self._parse_value(false_val_str.strip()), None

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a condition like 'A1>10' or 'B2="Yes"'"""
        # Support operators: >, <, >=, <=, =, <>
        operators = ['>=', '<=', '<>', '!=', '>', '<', '=']

        for op in operators:
            if op in condition:
                parts = condition.split(op, 1)
                if len(parts) == 2:
                    left = self._parse_value(parts[0].strip())
                    right = self._parse_value(parts[1].strip())

                    try:
                        if op == '>':
                            return float(left) > float(right)
                        elif op == '<':
                            return float(left) < float(right)
                        elif op == '>=':
                            return float(left) >= float(right)
                        elif op == '<=':
                            return float(left) <= float(right)
                        elif op in ('=', '=='):
                            return str(left) == str(right)
                        elif op in ('<>', '!='):
                            return str(left) != str(right)
                    except (ValueError, TypeError):
                        return str(left) == str(right) if op == '=' else str(left) != str(right)

        return False

    def _parse_value(self, value_str: str) -> Any:
        """Parse a value - could be cell reference, string literal, or number"""
        value_str = value_str.strip()

        # String literal (quoted)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        # Cell reference
        col_letter, row_num = self._parse_cell_reference(value_str)
        if col_letter and row_num is not None:
            return self._get_cell_value(value_str)

        # Try number
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            return value_str

    def _evaluate_vlookup(self, args_str: str) -> Tuple[Any, Optional[str]]:
        """Evaluate VLOOKUP(lookup_value, range, col_index)"""
        parts = self._split_args(args_str)

        if len(parts) < 3:
            return None, "VLOOKUP requires at least 3 arguments"

        lookup_value = self._parse_value(parts[0].strip())
        range_str = parts[1].strip()
        col_index = int(parts[2].strip())

        # Parse the range
        if ':' not in range_str:
            return None, "VLOOKUP range must be in format A1:B10"

        start, end = range_str.split(':')
        start_col, start_row = self._parse_cell_reference(start)
        end_col, end_row = self._parse_cell_reference(end)

        if not all(v is not None for v in [start_col, start_row, end_col, end_row]):
            return None, "Invalid range"

        start_col_idx = self._letter_to_index(start_col)

        # Search in first column of range
        first_col_letter = start_col
        if first_col_letter in self._column_letter_map:
            search_col = self._column_letter_map[first_col_letter]

            for row_idx in range(start_row, end_row + 1):
                if 0 <= row_idx < len(self.df):
                    cell_val = self.df.iloc[row_idx][search_col]
                    if str(cell_val) == str(lookup_value):
                        # Found match, get value from specified column
                        result_col_letter = self._index_to_letter(start_col_idx + col_index - 1)
                        if result_col_letter in self._column_letter_map:
                            result_col = self._column_letter_map[result_col_letter]
                            return self.df.iloc[row_idx][result_col], None

        return None, "Value not found"

    def _evaluate_concatenate(self, args_str: str) -> Tuple[Any, Optional[str]]:
        """Evaluate CONCATENATE(val1, val2, ...)"""
        parts = self._split_args(args_str)
        result = ""

        for part in parts:
            value = self._parse_value(part.strip())
            result += str(value) if value is not None else ""

        return result, None

    def _split_args(self, args_str: str) -> List[str]:
        """Split function arguments, handling nested parentheses and quotes"""
        parts = []
        current = ""
        paren_depth = 0
        in_quotes = False
        quote_char = None

        for char in args_str:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current += char
            elif char == '(' and not in_quotes:
                paren_depth += 1
                current += char
            elif char == ')' and not in_quotes:
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0 and not in_quotes:
                parts.append(current)
                current = ""
            else:
                current += char

        if current:
            parts.append(current)

        return parts


class Spreadsheet:
    """Excel-like editable spreadsheet component"""

    def __init__(self, df: pd.DataFrame, key: str = "spreadsheet"):
        self.original_df = df.copy()
        self.key = key
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state for this spreadsheet"""
        state_key = f"{self.key}_state"

        if state_key not in st.session_state:
            st.session_state[state_key] = SpreadsheetState()
            # Add initial state to history
            st.session_state[state_key].history.append(self.original_df.copy())
            st.session_state[state_key].current_index = 0

        if f"{self.key}_df" not in st.session_state:
            st.session_state[f"{self.key}_df"] = self.original_df.copy()

        if f"{self.key}_formulas" not in st.session_state:
            st.session_state[f"{self.key}_formulas"] = {}  # {(row, col): formula}

    @property
    def df(self) -> pd.DataFrame:
        """Get current DataFrame"""
        return st.session_state[f"{self.key}_df"]

    @df.setter
    def df(self, value: pd.DataFrame):
        """Set current DataFrame"""
        st.session_state[f"{self.key}_df"] = value

    @property
    def state(self) -> SpreadsheetState:
        """Get spreadsheet state"""
        return st.session_state[f"{self.key}_state"]

    def _save_state(self):
        """Save current state to history"""
        state = self.state

        # Remove any future states if we're not at the end
        if state.current_index < len(state.history) - 1:
            state.history = state.history[:state.current_index + 1]

        # Add new state
        state.history.append(self.df.copy())
        state.current_index = len(state.history) - 1

        # Limit history size
        if len(state.history) > state.max_history:
            state.history = state.history[-state.max_history:]
            state.current_index = len(state.history) - 1

    def undo(self) -> bool:
        """Undo last change"""
        state = self.state
        if state.current_index > 0:
            state.current_index -= 1
            self.df = state.history[state.current_index].copy()
            return True
        return False

    def redo(self) -> bool:
        """Redo last undone change"""
        state = self.state
        if state.current_index < len(state.history) - 1:
            state.current_index += 1
            self.df = state.history[state.current_index].copy()
            return True
        return False

    def add_row(self, index: Optional[int] = None, values: Optional[Dict] = None):
        """Add a new row"""
        new_row = pd.DataFrame([values or {col: None for col in self.df.columns}])

        if index is None:
            self.df = pd.concat([self.df, new_row], ignore_index=True)
        else:
            top = self.df.iloc[:index]
            bottom = self.df.iloc[index:]
            self.df = pd.concat([top, new_row, bottom], ignore_index=True)

        self._save_state()

    def delete_row(self, index: int):
        """Delete a row by index"""
        if 0 <= index < len(self.df):
            self.df = self.df.drop(self.df.index[index]).reset_index(drop=True)
            self._save_state()

    def add_column(self, name: str, default_value: Any = None, position: Optional[int] = None):
        """Add a new column"""
        if name not in self.df.columns:
            if position is None:
                self.df[name] = default_value
            else:
                self.df.insert(position, name, default_value)
            self._save_state()

    def delete_column(self, name: str):
        """Delete a column"""
        if name in self.df.columns:
            self.df = self.df.drop(columns=[name])
            self._save_state()

    def apply_formula(self, formula: str, target_column: str, start_row: int = 0, end_row: Optional[int] = None):
        """Apply a formula to a column range"""
        engine = FormulaEngine(self.df)

        if end_row is None:
            end_row = len(self.df)

        for row_idx in range(start_row, end_row):
            # Replace row references in formula
            row_formula = formula.replace('[ROW]', str(row_idx + 1))
            result, error = engine.evaluate(row_formula)

            if error is None and result is not None:
                self.df.at[row_idx, target_column] = result

        self._save_state()

    def evaluate_single_formula(self, formula: str) -> Tuple[Any, Optional[str]]:
        """Evaluate a single formula"""
        engine = FormulaEngine(self.df)
        return engine.evaluate(formula)

    def get_changes(self) -> pd.DataFrame:
        """Get changes between original and current DataFrame"""
        orig = self.original_df
        curr = self.df

        # Find differences
        changes = []

        # Check for modified values in common rows/columns
        common_rows = min(len(orig), len(curr))
        common_cols = list(set(orig.columns) & set(curr.columns))

        for row_idx in range(common_rows):
            for col in common_cols:
                orig_val = orig.iloc[row_idx][col]
                curr_val = curr.iloc[row_idx][col]

                # Handle NaN comparison
                if pd.isna(orig_val) and pd.isna(curr_val):
                    continue
                if str(orig_val) != str(curr_val):
                    changes.append({
                        'row': row_idx,
                        'column': col,
                        'old_value': orig_val,
                        'new_value': curr_val
                    })

        return pd.DataFrame(changes)

    def render_editor(self, height: int = 400) -> pd.DataFrame:
        """Render the editable spreadsheet"""
        # Toolbar
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])

        with col1:
            if st.button("Undo", key=f"{self.key}_undo", disabled=self.state.current_index <= 0):
                self.undo()
                st.rerun()

        with col2:
            if st.button("Redo", key=f"{self.key}_redo", disabled=self.state.current_index >= len(self.state.history) - 1):
                self.redo()
                st.rerun()

        with col3:
            if st.button("+ Row", key=f"{self.key}_add_row"):
                self.add_row()
                st.rerun()

        with col4:
            if st.button("+ Column", key=f"{self.key}_add_col"):
                st.session_state[f"{self.key}_show_add_col"] = True

        with col5:
            if st.button("Reset", key=f"{self.key}_reset"):
                self.df = self.original_df.copy()
                self._save_state()
                st.rerun()

        # Add column dialog
        if st.session_state.get(f"{self.key}_show_add_col", False):
            with st.form(key=f"{self.key}_add_col_form"):
                new_col_name = st.text_input("Column name")
                submitted = st.form_submit_button("Add")
                if submitted and new_col_name:
                    self.add_column(new_col_name)
                    st.session_state[f"{self.key}_show_add_col"] = False
                    st.rerun()

        # Formula bar
        with st.expander("Formula Bar", expanded=False):
            formula_col1, formula_col2, formula_col3 = st.columns([2, 2, 1])

            with formula_col1:
                formula_input = st.text_input(
                    "Enter formula",
                    placeholder="=SUM(A1:A10)",
                    key=f"{self.key}_formula_input"
                )

            with formula_col2:
                target_col = st.selectbox(
                    "Apply to column",
                    self.df.columns.tolist(),
                    key=f"{self.key}_formula_target"
                )

            with formula_col3:
                if st.button("Apply", key=f"{self.key}_apply_formula"):
                    if formula_input:
                        result, error = self.evaluate_single_formula(formula_input)
                        if error:
                            st.error(f"Formula error: {error}")
                        else:
                            st.success(f"Result: {result}")

            st.caption("Supported: SUM, AVG, COUNT, MIN, MAX, MEDIAN, IF, VLOOKUP, CONCATENATE")
            st.caption("Example: =SUM(A1:A10), =IF(A1>10, 'Yes', 'No'), =VLOOKUP(A1, B1:C10, 2)")

        # Data editor
        edited_df = st.data_editor(
            self.df,
            num_rows="dynamic",
            use_container_width=True,
            height=height,
            key=f"{self.key}_editor"
        )

        # Check for changes
        if not edited_df.equals(self.df):
            self.df = edited_df
            self._save_state()

        # Statistics bar
        st.caption(f"Rows: {len(self.df)} | Columns: {len(self.df.columns)} | History: {self.state.current_index + 1}/{len(self.state.history)}")

        return self.df

    def render_with_row_actions(self, height: int = 400) -> pd.DataFrame:
        """Render spreadsheet with row-level actions"""
        # Main editor
        edited_df = self.render_editor(height)

        # Row actions
        with st.expander("Row Actions", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                row_to_delete = st.number_input(
                    "Delete row #",
                    min_value=0,
                    max_value=max(0, len(self.df) - 1),
                    value=0,
                    key=f"{self.key}_delete_row_num"
                )
                if st.button("Delete Row", key=f"{self.key}_delete_row_btn"):
                    self.delete_row(row_to_delete)
                    st.rerun()

            with col2:
                col_to_delete = st.selectbox(
                    "Delete column",
                    self.df.columns.tolist(),
                    key=f"{self.key}_delete_col_select"
                )
                if st.button("Delete Column", key=f"{self.key}_delete_col_btn"):
                    self.delete_column(col_to_delete)
                    st.rerun()

        return edited_df

    def export_data(self, format: str = 'csv') -> bytes:
        """Export current data"""
        if format == 'csv':
            return self.df.to_csv(index=False).encode('utf-8')
        elif format == 'excel':
            import io
            buffer = io.BytesIO()
            self.df.to_excel(buffer, index=False, engine='openpyxl')
            return buffer.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


def render_spreadsheet_tab(df: pd.DataFrame) -> pd.DataFrame:
    """Render the spreadsheet tab in the main app"""
    st.subheader("Spreadsheet Editor")
    st.caption("Edit cells directly, add/delete rows and columns, and use formulas")

    spreadsheet = Spreadsheet(df, key="main_spreadsheet")
    edited_df = spreadsheet.render_with_row_actions(height=500)

    # Export options
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        csv_data = spreadsheet.export_data('csv')
        st.download_button(
            "Download CSV",
            csv_data,
            "edited_data.csv",
            "text/csv",
            use_container_width=True
        )

    with col2:
        excel_data = spreadsheet.export_data('excel')
        st.download_button(
            "Download Excel",
            excel_data,
            "edited_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # Show changes if any
    changes = spreadsheet.get_changes()
    if not changes.empty:
        with st.expander(f"View Changes ({len(changes)} modifications)", expanded=False):
            st.dataframe(changes, use_container_width=True)

    return edited_df
