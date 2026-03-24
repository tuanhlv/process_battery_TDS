import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import handle_exceptions

@handle_exceptions("OCV Plotting")
def plot_ocv(csv_file_path: str, plot_path: str) -> None:
    df = pd.read_csv(csv_file_path)
    plt.figure(figsize=(10, 7))

    # Discharge logic
    discharge = df[(df['Cycle_Index'] == 1) & (df['Step_Time'] == 7200) & (df['Current'] == 0)].copy()
    discharge_step = -2
    discharge_stop = 100 + len(discharge['Voltage']) * discharge_step
    discharge['SOC'] = list(range(100, discharge_stop, discharge_step))
    plt.plot(discharge['SOC'], discharge['Voltage'].tolist(), label='Discharge', linestyle='--', color='black')

    # Charge logic
    charge = df[(df['Cycle_Index'] == 2) & (df['Step_Time'] == 7200) & (df['Current'] == 0)].copy()
    charge_step = 2
    charge_start = discharge_stop + charge_step
    charge_stop = charge_start + len(charge['Voltage']) * charge_step
    charge['SOC'] = list(range(charge_start, charge_stop, charge_step))
    
    # Plot OCV vs. SOC
    plt.plot(charge['SOC'], charge['Voltage'].tolist(), label='Charge', linestyle='-', color='black')
    plt.xlabel('SOC (%)')
    plt.ylabel('OCV')
    plt.xticks(list(range(0, 101, 10)))
    plt.title('OCV vs SOC')
    plt.legend()
    plt.grid(True)
    plt.savefig(plot_path)
    plt.close('all')