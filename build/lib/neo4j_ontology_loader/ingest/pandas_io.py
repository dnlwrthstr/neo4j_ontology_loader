import pandas as pd

def df_to_rows(df: pd.DataFrame) -> list[dict]:
    return df.to_dict(orient="records")
