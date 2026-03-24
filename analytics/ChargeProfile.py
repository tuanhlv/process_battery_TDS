import os
import pandas as pd
import matplotlib.pyplot as plt
from utils import handle_exceptions
from .common_helpers import get_c_rate_color_map

@handle_exceptions("Charge Profiling")
def plot_rate_charge(csv_file_path: str, cycle_numbers_str: str, charge_rates_str: str,
                     png_path1: str, png_path2: str, processed_folder: str, csv_res_path: str) -> None:
    cycles: list[int] = [int(c.strip()) for c in cycle_numbers_str.split(',')]
    charge_rates: list[float] = [float(r.strip()) for r in charge_rates_str.split(',')]

    if 0.2 not in charge_rates:
        raise ValueError("Reference C-rate 0.2 not found in the input list. Plotting skipped.")
    if len(cycles) != len(charge_rates):
        raise ValueError("Cycle numbers count must match charge rates count.")

    cycle_to_c_rate_map = dict(zip(cycles, charge_rates))
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"File not found: {csv_file_path}")

    df = pd.read_csv(csv_file_path)
    color_map = get_c_rate_color_map()

    res = {'rate': [], 'capCharge': [], 'capDischarge': [], 'temp1': [], 'temp2': []}

    fig1, ax11 = plt.subplots(figsize=(12, 8))
    ax11.set_title('Charge Profiles at Different C-Rates', size=20)
    ax12 = ax11.twinx()
    ax11.set_xlabel('Charge Capacity (Ah)', size=18)
    ax11.set_ylabel('Voltage (V)', size=18)
    ax12.set_ylabel('Current (A)', size=18)

    fig2, ax21 = plt.subplots(figsize=(12, 8))
    ax21.set_title('Charge Profiles at Different C-Rates', size=20)
    ax22 = ax21.twinx()
    ax21.set_xlabel('Charge Duration (min)', size=18)
    ax21.set_ylabel('Voltage (V)', size=18)
    ax22.set_ylabel('Current (A)', size=18)

    for cycle, c_rate in cycle_to_c_rate_map.items():
        if c_rate not in color_map:
            continue

        charge_df = df[(df['Cycle_Index'] == cycle) & (df['Current'] > 0)].copy()
        discharge_df = df[(df['Cycle_Index'] == cycle) & (df['Current'] < 0)].copy()

        if charge_df.empty:
            continue

        color = color_map[c_rate]
        res['rate'].append(c_rate)
        res['capCharge'].append(charge_df['Charge_Capacity'].max())
        res['capDischarge'].append(discharge_df['Discharge_Capacity'].max() if not discharge_df.empty else 0)

        charge_df['Temperature1'] = None
        charge_df['Temperature2'] = None

        arbin_interp = df.columns[df.columns.str.endswith("_interp")]
        if len(arbin_interp) > 0 and pd.api.types.is_numeric_dtype(charge_df[arbin_interp[0]]):
            charge_df['Temperature1'] = charge_df[arbin_interp[0]]
        elif 'X' in charge_df.columns and pd.api.types.is_numeric_dtype(charge_df['X']):
            charge_df['Temperature1'] = charge_df['X']
        elif 'T1' in charge_df.columns and pd.api.types.is_numeric_dtype(charge_df['T1']):
            charge_df['Temperature1'] = charge_df['T1']

        if 'T2' in charge_df.columns and pd.api.types.is_numeric_dtype(charge_df['T2']):
            charge_df['Temperature2'] = charge_df['T2']

        res['temp1'].append(charge_df['Temperature1'].max())
        res['temp2'].append(charge_df['Temperature2'].max())

        ax11.plot(charge_df['Charge_Capacity'], charge_df['Voltage'], label=f'{c_rate}C', color=color,
                  linestyle='-')
        ax12.plot(charge_df['Charge_Capacity'], charge_df['Current'], label=f'{c_rate}C Current', color=color,
                  linestyle='--')

        charge_df['Charge_Duration_min'] = (charge_df['Test_Time'] - charge_df['Test_Time'].iloc[0]) / 60
        ax21.plot(charge_df['Charge_Duration_min'], charge_df['Voltage'], label=f'{c_rate}C Voltage', color=color,
                  linestyle='-')
        ax22.plot(charge_df['Charge_Duration_min'], charge_df['Current'], label=f'{c_rate}C Current', color=color,
                  linestyle='--')

        split_csv = f"{processed_folder}_chargeProfile_{c_rate}C.csv"
        charge_df[['Charge_Duration_min', 'Voltage', 'Current']].to_csv(split_csv, index=False)

    ax11.grid(True)
    ax11.legend(title='Charge Rate', loc='best')
    fig1.tight_layout()
    fig1.savefig(png_path1)

    ax21.grid(True)
    ax21.legend(title='Charge Rate', loc='best')
    fig2.tight_layout()
    fig2.savefig(png_path2)
    plt.close('all')

    pd.DataFrame({
        'Charge Rate': res['rate'],
        'Charge Capacity': res['capCharge'],
        'Discharge Capacity': res['capDischarge'],
        'Max Temperature 1': res['temp1'],
        'Max Temperature 2': res['temp2']
    }).to_csv(csv_res_path, index=False)