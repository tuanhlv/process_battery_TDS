import pandas as pd
import matplotlib.pyplot as plt
from typing import Any
from utils import handle_exceptions
from .common_helpers import get_c_rate_color_map

@handle_exceptions("Discharge Profiling")
def plot_rate_discharge(csv_file_path: str, cycle_numbers_str: str, discharge_rates_str: str,
                        png_path1: str, png_path2: str, csv_res_path: str, thermocouple: Any,
                        n_thermocouples: int, processed_folder: str) -> None:
    cycles: list[int] = [int(c.strip()) for c in cycle_numbers_str.split(',')]
    rates: list[float] = [float(r.strip()) for r in discharge_rates_str.split(',')]

    if 0.2 not in rates:
        raise ValueError("Reference C-rate 0.2 not found in the input list. Plotting skipped.")
    if len(cycles) != len(rates):
        raise ValueError("Cycle numbers count must match discharge rates count.")

    cycle_to_c_rate_map = dict(zip(cycles, rates))
    df = pd.read_csv(csv_file_path)
    color_map = get_c_rate_color_map()

    fig1, ax11 = plt.subplots(figsize=(12, 8))
    ax11.set(xlabel='Discharge Capacity (Ah)', ylabel='Voltage (V)', title='Discharge Profile at Different C-Rates')
    ax11.grid()
    ax12 = ax11.twinx()
    ax12.set_ylabel('Cell Body Temperature')

    fig2, ax21 = plt.subplots(figsize=(12, 8))
    ax21.set(xlabel='Discharge Capacity Ratio (%)', ylabel='Voltage (V)',
             title='Normalized Discharge Profile at Different C-Rates')
    ax21.grid()
    ax22 = ax21.twinx()
    ax22.set_ylabel('Cell Body Temperature')

    ref_cycle_num = [k for k, v in cycle_to_c_rate_map.items() if v == 0.2][0]
    ref_cycle_df = df[(df['Cycle_Index'] == ref_cycle_num) & (df['Current'] < 0)]
    max_capacity_ref = ref_cycle_df['Discharge_Capacity'].max()

    res = {'rate': [], 'cap': [], 'temp1': [], 'temp2': []}

    for cycle, c_rate in cycle_to_c_rate_map.items():
        if c_rate not in color_map:
            continue

        discharge_df = df[(df['Cycle_Index'] == cycle) & (df['Current'] < 0)].copy()
        if discharge_df.empty:
            continue

        color = color_map[c_rate]
        res['rate'].append(c_rate)
        res['cap'].append(discharge_df['Discharge_Capacity'].max())

        ax11.plot(discharge_df['Discharge_Capacity'], discharge_df['Voltage'], '-', label=f'{c_rate}C', color=color)
        discharge_df['Capacity_Ratio'] = (discharge_df['Discharge_Capacity'] / max_capacity_ref) * 100
        ax21.plot(discharge_df['Capacity_Ratio'], discharge_df['Voltage'], '-', label=f'{c_rate}C', color=color)

        discharge_df['Temperature1'] = None
        discharge_df['Temperature2'] = None

        arbin_interp = df.columns[df.columns.str.endswith("_interp")]
        if len(arbin_interp) > 0 and pd.api.types.is_numeric_dtype(discharge_df[arbin_interp[0]]):
            discharge_df['Temperature1'] = discharge_df[arbin_interp[0]]
        elif 'X' in discharge_df.columns and pd.api.types.is_numeric_dtype(discharge_df['X']):
            discharge_df['Temperature1'] = discharge_df['X']
        elif 'T1' in discharge_df.columns and pd.api.types.is_numeric_dtype(discharge_df['T1']):
            discharge_df['Temperature1'] = discharge_df['T1']

        if n_thermocouples > 1 and 'T2' in discharge_df.columns and pd.api.types.is_numeric_dtype(
                discharge_df['T2']):
            discharge_df['Temperature2'] = discharge_df['T2']

        if discharge_df['Temperature1'].notnull().any():
            ax12.plot(discharge_df['Discharge_Capacity'], discharge_df['Temperature1'], '--', color=color)
            ax22.plot(discharge_df['Capacity_Ratio'], discharge_df['Temperature1'], '--', color=color)
        if discharge_df['Temperature2'].notnull().any():
            ax12.plot(discharge_df['Discharge_Capacity'], discharge_df['Temperature2'], '.', color=color)
            ax22.plot(discharge_df['Capacity_Ratio'], discharge_df['Temperature2'], '.', color=color)

        res['temp1'].append(discharge_df['Temperature1'].max())
        res['temp2'].append(discharge_df['Temperature2'].max())

        export_cols = ['Discharge_Capacity', 'Voltage', 'Capacity_Ratio']
        if discharge_df['Temperature1'].notnull().any() and discharge_df['Temperature2'].notnull().any():
            t_col = 'Temperature2' if discharge_df['Temperature2'].max() > discharge_df[
                'Temperature1'].max() else 'Temperature1'
            export_cols.insert(2, t_col)
        elif discharge_df['Temperature1'].notnull().any():
            export_cols.insert(2, 'Temperature1')
        elif discharge_df['Temperature2'].notnull().any():
            export_cols.insert(2, 'Temperature2')

        split_csv = f"{processed_folder}_dischargeProfile_{c_rate}C.csv"
        discharge_df[export_cols].to_csv(split_csv, index=False)

    ax11.legend(title='C-Rate', loc='best')
    ax21.legend(title='C-Rate', loc='best')
    ax21.set_xticks(list(range(0, 100, 10)))
    fig1.savefig(png_path1)
    fig2.savefig(png_path2)
    plt.close('all')

    pd.DataFrame({
        'Discharge Rate': res['rate'],
        'Discharge Capacity': res['cap'],
        'Max Temperature 1': res['temp1'],
        'Max Temperature 2': res['temp2']
    }).to_csv(csv_res_path, index=False)