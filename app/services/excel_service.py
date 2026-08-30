import os
import pandas as pd


def extract_excel_data(file_path: str) -> list:
    """
    Extracts structured data from Excel or CSV files.
    """

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".csv":
        dataframe = pd.read_csv(file_path)

    elif file_extension in [".xlsx", ".xls"]:
        dataframe = pd.read_excel(file_path)

    else:
        raise ValueError(
            f"Unsupported spreadsheet type: {file_extension}"
        )

    dataframe = dataframe.fillna("")

    return dataframe.to_dict(orient="records")