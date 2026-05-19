"""
Data Loader Module
Handles CSV and Excel file uploads and parsing
"""

import pandas as pd
import io
from typing import Optional, Tuple, List
import streamlit as st


class DataLoader:
    """Handles loading data from various file formats"""

    SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
    MAX_FILE_SIZE_MB = 100

    @staticmethod
    def get_supported_extensions() -> List[str]:
        """Return list of supported file extensions"""
        return list(DataLoader.SUPPORTED_EXTENSIONS)

    @staticmethod
    def load_file(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Load data from uploaded file

        Args:
            uploaded_file: Streamlit UploadedFile object

        Returns:
            Tuple of (DataFrame or None, error message or None)
        """
        if uploaded_file is None:
            return None, "No file uploaded"

        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > DataLoader.MAX_FILE_SIZE_MB:
            return None, f"File too large. Maximum size is {DataLoader.MAX_FILE_SIZE_MB}MB"

        # Get file extension
        file_name = uploaded_file.name.lower()

        try:
            if file_name.endswith('.csv'):
                return DataLoader._load_csv(uploaded_file)
            elif file_name.endswith('.xlsx'):
                return DataLoader._load_excel(uploaded_file, engine='openpyxl')
            elif file_name.endswith('.xls'):
                return DataLoader._load_excel(uploaded_file, engine='xlrd')
            else:
                return None, f"Unsupported file format. Supported: {', '.join(DataLoader.SUPPORTED_EXTENSIONS)}"
        except Exception as e:
            return None, f"Error loading file: {str(e)}"

    @staticmethod
    def _load_csv(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Load CSV file with encoding detection"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=encoding)
                return df, None
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                return None, "The file is empty"
            except pd.errors.ParserError as e:
                return None, f"CSV parsing error: {str(e)}"

        return None, "Could not decode file. Please ensure it's a valid CSV"

    @staticmethod
    def _load_excel(uploaded_file, engine: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Load Excel file"""
        try:
            uploaded_file.seek(0)

            # First, check available sheets
            xl = pd.ExcelFile(uploaded_file, engine=engine)
            sheet_names = xl.sheet_names

            if len(sheet_names) == 0:
                return None, "Excel file has no sheets"

            # Load first sheet by default
            df = pd.read_excel(xl, sheet_name=sheet_names[0])
            return df, None

        except Exception as e:
            return None, f"Excel parsing error: {str(e)}"

    @staticmethod
    def load_multiple_files(uploaded_files: List) -> Tuple[dict, List[str]]:
        """
        Load multiple files

        Args:
            uploaded_files: List of Streamlit UploadedFile objects

        Returns:
            Tuple of (dict of filename -> DataFrame, list of error messages)
        """
        dataframes = {}
        errors = []

        for uploaded_file in uploaded_files:
            df, error = DataLoader.load_file(uploaded_file)
            if df is not None:
                dataframes[uploaded_file.name] = df
            if error:
                errors.append(f"{uploaded_file.name}: {error}")

        return dataframes, errors

    @staticmethod
    def get_excel_sheets(uploaded_file) -> Tuple[Optional[List[str]], Optional[str]]:
        """Get list of sheet names from Excel file"""
        try:
            uploaded_file.seek(0)
            file_name = uploaded_file.name.lower()
            engine = 'openpyxl' if file_name.endswith('.xlsx') else 'xlrd'
            xl = pd.ExcelFile(uploaded_file, engine=engine)
            return xl.sheet_names, None
        except Exception as e:
            return None, f"Error reading Excel sheets: {str(e)}"

    @staticmethod
    def load_excel_sheet(uploaded_file, sheet_name: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Load specific sheet from Excel file"""
        try:
            uploaded_file.seek(0)
            file_name = uploaded_file.name.lower()
            engine = 'openpyxl' if file_name.endswith('.xlsx') else 'xlrd'
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine=engine)
            return df, None
        except Exception as e:
            return None, f"Error loading sheet '{sheet_name}': {str(e)}"
