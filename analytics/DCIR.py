import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import handle_exceptions

@handle_exceptions("DCIR Plotting")
def plot_dcir(cls, csv_file_path: str, capacity: float, rate: float, plot_path: str, csv_res_path: str) -> None:
    socs = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    df = pd.read_csv(csv_file_path)
    df.columns = df.columns.str.replace('Channel_Normal_Table.', '', regex=False)

    i_pulse = rate * capacity
    pulse_start_indices = df.index[(df['Current'] < 0.98 * i_pulse) & (df['Current'] > 1.02 * i_pulse) & (df['Current'].shift(1) == 0)].tolist()

    soc_levels, dcir_01, dcir_10, dcir_30, dcir_60 = [], [], [], [], []

    for i, start_idx in enumerate(pulse_start_indices):
        if i >= len(socs):
            break
        soc_levels.append(socs[i])
        v_start = df.loc[start_idx - 1, 'Voltage']

        mask = (df.loc[start_idx:, 'Current'] < 0.98 * i_pulse) & (df.loc[start_idx:, 'Current'] > 1.02 * i_pulse)
        pulse_len = mask.argmin() if not mask.all() else len(mask)
        pulse = df.loc[start_idx:start_idx + pulse_len - 1, ['Step_Time', 'Current', 'Voltage']].copy()
        pulse.columns = ['Time', 'Current', 'Voltage']

        def calc_dcir(t_limit: int) -> float:
            if pulse['Time'].max() >= t_limit:
                p_sub = pulse[pulse['Time'] <= t_limit]
                return 1000 * (p_sub['Voltage'].iloc[-1] - v_start) / p_sub['Current'].mean()
            return np.nan

        dcir_60.append(calc_dcir(60))
        dcir_30.append(calc_dcir(30))
        dcir_10.append(calc_dcir(10))
        dcir_01.append(calc_dcir(1))

    pd.DataFrame({
        '%SOC': soc_levels,
        'DCIR (mΩ) at 60 sec': dcir_60,
        'DCIR (mΩ) at 30 sec': dcir_30,
        'DCIR (mΩ) at 10 sec': dcir_10,
        'DCIR (mΩ) at 1 sec': dcir_01
    }).to_csv(csv_res_path, index=False)

    display_pulse_rate = f"{rate}C {'Discharge' if rate < 0 else 'Charge'} Pulse Rate"
    plt.figure(figsize=(10, 7))
    plt.plot(soc_levels, dcir_60, label='60sec', color='black')
    plt.plot(soc_levels, dcir_30, label='30sec', color='blue')
    plt.plot(soc_levels, dcir_10, label='10sec', color='red')
    plt.plot(soc_levels, dcir_01, label='1sec', color='magenta')
    plt.xlim(100, 0)
    plt.xlabel('%SOC')
    plt.ylabel('DCIR (mOhm)')
    plt.title(f'DCIR vs. SOC with {display_pulse_rate}')
    plt.legend(title='Pulse Duration')
    plt.grid()
    plt.xticks(list(range(100, 0, -10)))
    plt.savefig(plot_path)
    plt.close('all')