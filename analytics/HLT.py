import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import handle_exceptions

@handle_exceptions("Temperature Performance")
def plot_temperature_perf(cls, csv_file_path: str, cycle_numbers_str: str, temperatures_str: str, png_path1: str, png_path2: str, csv_res_path: str, processed_folder: str) -> None:
    cycles: list[int] = [int(c.strip()) for c in cycle_numbers_str.split(',')]
    temperatures: list[int] = [int(t.strip()) for t in temperatures_str.split(',')]

    if 20 not in temperatures:
        raise ValueError("Reference temperature 20°C not found. Plotting skipped.")
    if len(cycles) != len(temperatures):
        raise ValueError("Cycles count must match temperatures count.")

    cycle_to_temp_map = dict(zip(cycles, temperatures))
    df = pd.read_csv(csv_file_path)
    color_map = cls.get_temp_color_map()

    fig1, ax1 = plt.subplots(figsize=(12, 8))
    ax1.set(xlabel='Discharge Capacity (Ah)', ylabel='Voltage (V)',
                title='Discharge Profile at Different Temperatures')
    ax1.grid()

    fig2, ax2 = plt.subplots(figsize=(12, 8))
    ax2.set(xlabel='Discharge Capacity Ratio (%)', ylabel='Voltage (V)',
                title='Normalized Discharge Profile at Different Temperatures')
    ax2.grid()

    ref_cycle_num = [k for k, v in cycle_to_temp_map.items() if v == 20][0]
    max_capacity_ref = df[(df['Cycle_Index'] == ref_cycle_num) & (df['Current'] < 0)]['Discharge_Capacity'].max()

    res_temp, res_cap = [], []

    for cycle, temp in cycle_to_temp_map.items():
        if temp not in color_map:
            continue

        discharge_df = df[(df['Cycle_Index'] == cycle) & (df['Current'] < 0)].copy()
        if not discharge_df.empty:
            color = color_map[temp]
            ax1.plot(discharge_df['Discharge_Capacity'], discharge_df['Voltage'], label=f'{temp}°C', color=color)

            discharge_df['Capacity_Ratio'] = (discharge_df['Discharge_Capacity'] / max_capacity_ref) * 100
            ax2.plot(discharge_df['Capacity_Ratio'], discharge_df['Voltage'], label=f'{temp}°C', color=color)

            split_csv = f"{processed_folder}_HLTdischargeProfile_{temp}C.csv"
            discharge_df[['Discharge_Capacity', 'Voltage', 'Capacity_Ratio']].to_csv(split_csv, index=False)

            res_temp.append(temp)
            res_cap.append(discharge_df['Discharge_Capacity'].max())

    pd.DataFrame({'Discharge Temperature': res_temp, 'Discharge Capacity': res_cap}).to_csv(csv_res_path, index=False)
    ax1.legend(title='Temperatures', loc='best')
    ax2.legend(title='Temperatures', loc='best')
    fig1.savefig(png_path1)
    fig2.savefig(png_path2)
    plt.close('all')