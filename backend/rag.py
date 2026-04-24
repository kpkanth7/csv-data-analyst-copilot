import pandas as pd
import io

def build_csv_context(file_bytes: bytes) -> str:
    # Converting bytes to a dataframe so we can actually work with it
    df = pd.read_csv(io.BytesIO(file_bytes))
    lines = []

    # Getting the basic scale of the data
    lines.append(f"Dataset: {df.shape[0]} rows x {df.shape[1]} columns\n")

    # Mapping out the columns and checking for missing values
    lines.append("Columns (name | dtype | null count):")
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = int(df[col].isnull().sum())
        lines.append(f" - {col!r}: {dtype}, {nulls} nulls")
    
    # Grabbing math stats for the numbers
    numeric_cols = df.select_dtypes(include="number")
    if not numeric_cols.empty:
        lines.append("\nSummary statistics (numeric columns):")
        lines.append(numeric_cols.describe().round(2).to_string())

    # Looking at the top categories for text columns
    categorical_cols = df.select_dtypes(include=["object", "category"])
    if not categorical_cols.empty:
        lines.append("\nCategorical columns (top 5 values):")
        for col in categorical_cols.columns:
            counts = df[col].value_counts().head(5).to_dict()
            lines.append(f" - {col!r}: {counts}")

    # Dropping in a 20-row sample so the AI sees the data format
    lines.append("\nSample data (first 20 rows):")
    lines.append(df.head(20).to_string(index=False))
    
    return "\n".join(lines)
