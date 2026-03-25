import pandas as pd
import numpy as np

@staticmethod
def get_c_rate_color_map() -> dict[float, str]:
    possible_rates = [0.1, 0.2, 0.33, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12]
    colors = ['grey', 'black', 'red', 'salmon', 'magenta', 'blue', 'skyblue', 'chocolate', 'orange', 'green', 'lightgreen', 'magenta', 'salmon', 'red', 'grey']
    return {rate: colors[i] for i, rate in enumerate(possible_rates)}

@staticmethod
def get_temp_color_map() -> dict[int, str]:
    temps = [-60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60]
    colors = ['red', 'salmon', 'blue', 'skyblue', 'chocolate', 'orange', 'green', 'lightgreen', 'black', 'grey', 'magenta', 'violet', 'darkred']
    return {temp: colors[i] for i, temp in enumerate(temps)}
    
def extract_temperature_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Helper to standardize finding temperature columns across all Arbin/Neware formats."""
    df = df.copy()
    df['Temperature1'] = None
    df['Temperature2'] = None
    
    arbin_interp = df.columns[df.columns.str.startswith("T_") & df.columns.str.endswith("_interp")]
    if len(arbin_interp) > 0 and pd.api.types.is_numeric_dtype(df[arbin_interp[0]]):
        df['Temperature1'] = df[arbin_interp[0]]
    elif 'X' in df.columns and pd.api.types.is_numeric_dtype(df['X']):
        df['Temperature1'] = df['X']
    elif 'T1' in df.columns and pd.api.types.is_numeric_dtype(df['T1']):
        df['Temperature1'] = df['T1']
    else:
        df['Temperature1'] = np.nan

    if 'T2' in df.columns and pd.api.types.is_numeric_dtype(df['T2']):
        df['Temperature2'] = df['T2']
    else:
        df['Temperature2'] = np.nan
        
    return df