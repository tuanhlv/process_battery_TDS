import os
import pandas as pd
import matplotlib.pyplot as plt
from utils import handle_exceptions
from .common_helpers import get_c_rate_color_map

@handle_exceptions("Charge Profiling")

@handle_exceptions("Cycle Life Plotting")
def plot_cycle_life(cls, temperature_str: str, csv_file_paths_str: str, rates_str: str,
                        max_cycle: int, ref_cycle: int, plot_path1: str, plot_path2: str,
                        processed_folder: str, processed_csv_prefix: str) -> None:
    os.makedirs(processed_folder, exist_ok=True)
    csv_file_paths: List[str] = [r.strip() for r in csv_file_paths_str.split(',')]
    rates: List[float] = [float(r.strip()) for r in rates_str.split(',')]

    if len(csv_file_paths) != len(rates):
            raise ValueError("CSV files count must match cycling rates count.")

    color_map = cls.get_c_rate_color_map()
    fig1, ax1 = plt.subplots(figsize=(10, 7))
    fig2, ax2 = plt.subplots(figsize=(10, 7))
    cap0_list: List[float] = []

    for path, c_rate in zip(csv_file_paths, rates):
        if c_rate not in color_map:
            continue

        df = pd.read_csv(path)
        eoc = df.drop_duplicates(subset='Cycle_Index', keep='last').copy()
        ref_data = eoc[eoc['Cycle_Index'] == ref_cycle]['Discharge_Capacity']
        if ref_data.empty:
            continue

        cap0 = ref_data.max()
        cap0_list.append(cap0)
        eoc['Capacity_Retention'] = 100 * eoc['Discharge_Capacity'] / cap0

        line_color = color_map[c_rate]
        ax1.plot(eoc['Cycle_Index'], eoc['Discharge_Capacity'], color=line_color, label=f"{c_rate}C")
        ax2.plot(eoc['Cycle_Index'], eoc['Capacity_Retention'], color=line_color, label=f"{c_rate}C")

        processed_csv_fn = f"{processed_folder}{processed_csv_prefix}_{c_rate}.csv"
        eoc[['Cycle_Index', 'Discharge_Capacity', 'Capacity_Retention']].to_csv(processed_csv_fn, index=False)

    if not cap0_list:
        plt.close('all')
        return

    ymax = round((max(cap0_list) + 0.5) * 2) / 2
    ymin = round((0.8 * max(cap0_list) - 0.5) * 2) / 2

    ax1.set(title=f"{temperature_str}, Discharge Capacity", xlabel='Cycle Number', ylabel='Discharge Capacity (Ah)',
                xlim=(0, max_cycle), ylim=(ymin, ymax))
    ax1.grid(True)
    ax1.legend(title='Cycling Rate')
    fig1.tight_layout()
    fig1.savefig(plot_path1)

    ax2.set(title=f"{temperature_str}, Capacity Retention", xlabel='Cycle Number', ylabel='Capacity Retention (%)',
                xlim=(0, max_cycle), ylim=(80, 105))
    ax2.grid(True)
    ax2.legend(title='Cycling Rate')
    fig2.tight_layout()
    fig2.savefig(plot_path2)
    plt.close('all')