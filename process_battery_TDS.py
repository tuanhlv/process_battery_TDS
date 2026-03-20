import os
import csv
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Callable
from functools import wraps
from pydantic import BaseModel, Field, ValidationError


# ==========================================
# Pydantic Models for Validation
# ==========================================
class QuickBaseConfig(BaseModel):
    token: str = Field(default="bytuu3_wfx_53f6zibdnpvd5bavwjd26avh8", description="QuickBase User Token")
    hostname: str = Field(default="https://ampriusinc.quickbase.com", description="QuickBase Hostname")
    test_table: str = Field(default="bqg4mcgfv", description="Cell Test table ID")
    cell_part_table: str = Field(default="bqg4mcgch", description="Cell Part table ID")


# ==========================================
# Context Managers
# ==========================================
class ExecutionLogger:
    """Context manager for handling execution logging to a CSV file."""

    def __init__(self, log_filepath: str):
        self.log_filepath = log_filepath
        self.entries: List[List[str]] = []

    def __enter__(self):
        return self

    def log(self, message: str) -> None:
        print(message)
        self.entries.append([message])

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.log_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for entry in self.entries:
                writer.writerow(entry)


# ==========================================
# Decorators
# ==========================================
def handle_exceptions(stage: str):
    """Decorator to standardize error handling and logging for methods."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exception:
                error_msg = f"An error occurred during {stage} in {func.__name__}: {exception}"
                print(error_msg)
                # If the first argument is a class instance with a logger, use it
                if args and hasattr(args[0], 'logger') and args[0].logger:
                    args[0].logger.log(error_msg)
                return None

        return wrapper

    return decorator


# ==========================================
# Core Analytics & Plotting Class (OOP)
# ==========================================
class BatteryAnalyzer:
    """Encapsulates all battery data processing and plotting logic."""

    @staticmethod
    def get_c_rate_color_map() -> Dict[float, str]:
        possible_rates = [0.1, 0.2, 0.33, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12]
        colors = ['grey', 'black', 'red', 'salmon', 'magenta', 'blue', 'skyblue',
                  'chocolate', 'orange', 'green', 'lightgreen', 'magenta', 'salmon', 'red', 'grey']
        return {rate: colors[i] for i, rate in enumerate(possible_rates)}

    @staticmethod
    def get_temp_color_map() -> Dict[int, str]:
        temps = [-60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60]
        colors = ['red', 'salmon', 'blue', 'skyblue', 'chocolate', 'orange', 'green',
                  'lightgreen', 'black', 'grey', 'magenta', 'violet', 'darkred']
        return {temp: colors[i] for i, temp in enumerate(temps)}

    @classmethod
    @handle_exceptions("Charge Profiling")
    def plot_rate_charge(cls, csv_file_path: str, cycle_numbers_str: str, charge_rates_str: str,
                         png_path1: str, png_path2: str, processed_folder: str, csv_res_path: str) -> None:
        cycles: List[int] = [int(c.strip()) for c in cycle_numbers_str.split(',')]
        charge_rates: List[float] = [float(r.strip()) for r in charge_rates_str.split(',')]

        if 0.2 not in charge_rates:
            raise ValueError("Reference C-rate 0.2 not found in the input list. Plotting skipped.")
        if len(cycles) != len(charge_rates):
            raise ValueError("Cycle numbers count must match charge rates count.")

        cycle_to_c_rate_map = dict(zip(cycles, charge_rates))
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"File not found: {csv_file_path}")

        df = pd.read_csv(csv_file_path)
        color_map = cls.get_c_rate_color_map()

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

    @classmethod
    @handle_exceptions("Discharge Profiling")
    def plot_rate_discharge(cls, csv_file_path: str, cycle_numbers_str: str, discharge_rates_str: str,
                            png_path1: str, png_path2: str, csv_res_path: str, thermocouple: Any,
                            n_thermocouples: int, processed_folder: str) -> None:
        cycles: List[int] = [int(c.strip()) for c in cycle_numbers_str.split(',')]
        rates: List[float] = [float(r.strip()) for r in discharge_rates_str.split(',')]

        if 0.2 not in rates:
            raise ValueError("Reference C-rate 0.2 not found in the input list. Plotting skipped.")
        if len(cycles) != len(rates):
            raise ValueError("Cycle numbers count must match discharge rates count.")

        cycle_to_c_rate_map = dict(zip(cycles, rates))
        df = pd.read_csv(csv_file_path)
        color_map = cls.get_c_rate_color_map()

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

    @classmethod
    @handle_exceptions("Temperature Performance")
    def plot_temperature_perf(cls, csv_file_path: str, cycle_numbers_str: str, temperatures_str: str,
                              png_path1: str, png_path2: str, csv_res_path: str, processed_folder: str) -> None:
        cycles: List[int] = [int(c.strip()) for c in cycle_numbers_str.split(',')]
        temperatures: List[int] = [int(t.strip()) for t in temperatures_str.split(',')]

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

        pd.DataFrame({'Discharge Temperature': res_temp, 'Discharge Capacity': res_cap}).to_csv(csv_res_path,
                                                                                                index=False)
        ax1.legend(title='Temperatures', loc='best')
        ax2.legend(title='Temperatures', loc='best')
        fig1.savefig(png_path1)
        fig2.savefig(png_path2)
        plt.close('all')

    @classmethod
    @handle_exceptions("OCV Plotting")
    def plot_ocv(cls, csv_file_path: str, plot_path: str) -> None:
        df = pd.read_csv(csv_file_path)
        plt.figure(figsize=(10, 7))

        discharge = df[(df['Cycle_Index'] == 1) & (df['Step_Time'] == 7200) & (df['Current'] == 0)].copy()
        discharge_step = -2
        discharge_stop = 100 + len(discharge['Voltage']) * discharge_step
        discharge['SOC'] = list(range(100, discharge_stop, discharge_step))
        plt.plot(discharge['SOC'], discharge['Voltage'].tolist(), label='Discharge', linestyle='--', color='black')

        charge = df[(df['Cycle_Index'] == 2) & (df['Step_Time'] == 7200) & (df['Current'] == 0)].copy()
        charge_step = 2
        charge_start = discharge_stop + charge_step
        charge_stop = charge_start + len(charge['Voltage']) * charge_step
        charge['SOC'] = list(range(charge_start, charge_stop, charge_step))
        plt.plot(charge['SOC'], charge['Voltage'].tolist(), label='Charge', linestyle='-', color='black')

        plt.xlabel('SOC (%)')
        plt.ylabel('OCV')
        plt.xticks(list(range(0, 101, 10)))
        plt.title('OCV vs SOC')
        plt.legend()
        plt.grid(True)
        plt.savefig(plot_path)
        plt.close('all')

    @classmethod
    @handle_exceptions("DCIR Plotting")
    def plot_dcir(cls, csv_file_path: str, capacity: float, rate: float, plot_path: str, csv_res_path: str) -> None:
        socs = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
        df = pd.read_csv(csv_file_path)
        df.columns = df.columns.str.replace('Channel_Normal_Table.', '', regex=False)

        i_pulse = rate * capacity
        pulse_start_indices = df.index[(df['Current'] < 0.98 * i_pulse) &
                                       (df['Current'] > 1.02 * i_pulse) &
                                       (df['Current'].shift(1) == 0)].tolist()

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

    @classmethod
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


# ==========================================
# API Client
# ==========================================
class QuickBaseAPIClient:
    """Handles API communications with QuickBase."""

    def __init__(self, qb_config: QuickBaseConfig, exec_logger: ExecutionLogger):
        self.config = qb_config
        self.logger = exec_logger
        self.headers = {
            'QB-Realm-Hostname': self.config.hostname,
            'User-Agent': 'Amprius',
            'Authorization': f'QB-USER-TOKEN {self.config.token}'
        }

    def query_table(self, table_id: str, query: str, fields: List[str], field_names: List[str]) -> pd.DataFrame:
        self.logger.log(f"Querying meta data from table {table_id}...")
        body = {
            "from": table_id,
            "select": fields,
            "where": query
        }

        response = requests.post(
            'https://api.quickbase.com/v1/records/query',
            headers=self.headers,
            json=body
        )
        response.raise_for_status()

        data = response.json().get('data', [])
        df = pd.json_normalize(data)

        if not df.empty:
            # Re-map random nested dict columns back to friendly text via field ID
            df_cols_number = [col.split('.')[0] for col in df.columns]
            df.columns = [field_names[fields.index(key)] for key in df_cols_number]

        return df


# ==========================================
# Main Processor Pipeline
# ==========================================
class TestPipeline:
    """Orchestrates the querying and plotting pipeline."""

    def __init__(self, qb_config: QuickBaseConfig, exec_logger: ExecutionLogger):
        self.api = QuickBaseAPIClient(config, logger)
        self.logger = exec_logger
        self.analyzer = BatteryAnalyzer()

    def run(self) -> None:
        self.process_cell_tests()
        self.process_cell_parts()

    def process_cell_tests(self) -> None:
        fids = ["3", "203", "443", "444", "445", "446", "447", "448", "457", "458",
                "460", "454", "497", "461", "463", "462", "464", "465", "466", "504",
                "469", "470", "480", "486", "224", "361", "495"]
        fnames = ["Test ID", "Cell - Target Capacity (Ah)", "TDS Input - Rate Capability - Cycle Numbers",
                  "TDS Input - Rate Capability - Discharge Rates", "TDS Input - Charge Profiling - Cycle Numbers",
                  "TDS Input - Charge Profiling - Charge Rates", "TDS Input - Temperature Perf - Cycle Numbers",
                  "TDS Input - Temperature Perf - Discharge Temperature", "TDS Input - OCV vs SOC",
                  "TDS Input - DCIR vs SOC", "TDS filepath - raw data CSV", "TDS filepath - charge profile PNG1",
                  "TDS filepath - charge profile PNG2", "TDS filepath - discharge profile PNG",
                  "TDS filepath - discharge profile, norm PNG", "TDS filepath - HLT discharge profile PNG",
                  "TDS filepath - HLT norm PNG", "TDS filepath - OCV PNG", "TDS filepath - DCIR PNG",
                  "TDS filepath - charge rate capability results CSV",
                  "TDS filepath - discharge rate capability results CSV",
                  "TDS filepath - temperature performance results CSV", "TDS filepath - DCIR results CSV",
                  "TDS Input - DCIR Pulse C-rate", "Thermocouple?", "# thermocouples", "TDS filepath - CSV folder"]

        query = "({457.EX.'TRUE'} OR {458.EX.'TRUE'}"
        for fid in fids[2:-18]:
            query += f" OR {{{fid}.XEX.''}}"
        query += ") AND {468.LT.'4'}"

        query_df = self.api.query_table(self.api.config.test_table, query, fids, fnames)
        query_df.to_csv('queriedTestRecords.csv')
        self.logger.log("Queried Cell Test records saved to queriedTestRecords.csv")

        for _, row in query_df.iterrows():
            test_id = row.get("Test ID")
            self.logger.log(f"Processing test ID #{test_id}")

            raw_csv = row.get('TDS filepath - raw data CSV')
            folder = row.get('TDS filepath - CSV folder')

            if row.get('TDS Input - Charge Profiling - Cycle Numbers') and row.get(
                    'TDS Input - Charge Profiling - Charge Rates'):
                self.logger.log("  -> Plotting charge profiles")
                self.analyzer.plot_rate_charge(
                    raw_csv, row['TDS Input - Charge Profiling - Cycle Numbers'],
                    row['TDS Input - Charge Profiling - Charge Rates'], row['TDS filepath - charge profile PNG1'],
                    row['TDS filepath - charge profile PNG2'], folder,
                    row['TDS filepath - charge rate capability results CSV']
                )

            if row.get('TDS Input - Rate Capability - Cycle Numbers') and row.get(
                    'TDS Input - Rate Capability - Discharge Rates'):
                self.logger.log("  -> Plotting discharge profiles")
                self.analyzer.plot_rate_discharge(
                    raw_csv, row['TDS Input - Rate Capability - Cycle Numbers'],
                    row['TDS Input - Rate Capability - Discharge Rates'], row['TDS filepath - discharge profile PNG'],
                    row['TDS filepath - discharge profile, norm PNG'],
                    row['TDS filepath - discharge rate capability results CSV'],
                    row['Thermocouple?'], int(row.get('# thermocouples', 1)), folder
                )

            if row.get('TDS Input - Temperature Perf - Cycle Numbers') and row.get(
                    'TDS Input - Temperature Perf - Discharge Temperature'):
                self.logger.log("  -> Plotting HLT discharge profiles")
                self.analyzer.plot_temperature_perf(
                    raw_csv, row['TDS Input - Temperature Perf - Cycle Numbers'],
                    row['TDS Input - Temperature Perf - Discharge Temperature'],
                    row['TDS filepath - HLT discharge profile PNG'],
                    row['TDS filepath - HLT norm PNG'], row['TDS filepath - temperature performance results CSV'],
                    folder
                )

            if row.get('TDS Input - OCV vs SOC'):
                self.logger.log("  -> Plotting OCV profile")
                self.analyzer.plot_ocv(raw_csv, row["TDS filepath - OCV PNG"])

            if row.get('TDS Input - DCIR vs SOC'):
                self.logger.log("  -> Plotting DCIR profile")
                self.analyzer.plot_dcir(
                    raw_csv, float(row["Cell - Target Capacity (Ah)"]), float(row["TDS Input - DCIR Pulse C-rate"]),
                    row["TDS filepath - DCIR PNG"], row['TDS filepath - DCIR results CSV']
                )

    def process_cell_parts(self) -> None:
        fids_cp = ["263", "279", "282", "281", "280", "283", "285", "286", "287", "288", "312", "311", "325"]
        fnames_cp = ["RT Cycling - Test IDs", "RT Cycling - Rates", "RT Cycling - max cycle",
                     "45C Cycling - Test IDs", "45C Cycling - Rates", "45C Cycling - max cycle",
                     "RT cycling plot - PNG path", "RT cycling plot, norm - PNG path",
                     "45C cycling plot - PNG path", "45C cycling plot, norm - PNG path",
                     "RT Cycling - ref cycle", "45C Cycling - ref cycle", "Cycling data folder"]

        query_cp = "({263.XEX.''} OR {281.XEX.''}) AND {296.LT.'4'}"
        df_cp = self.api.query_table(self.api.config.cell_part_table, query_cp, fids_cp, fnames_cp)

        fid_test, fname_test = ["3", "460"], ["Test ID", "TDS filepath - raw data CSV"]

        for _, row in df_cp.iterrows():
            for mode, prefix, temp_str in [('RT', 'RT', 'RT cycling'), ('45C', '40C', '45C cycling')]:
                test_id_str = row.get(f'{mode} Cycling - Test IDs')
                if not test_id_str:
                    continue

                self.logger.log(f"Processing {mode} cycling data")
                test_list = [t.strip() for t in test_id_str.split(',')]
                csv_paths = []

                for test in test_list:
                    query_test = f"{{'3'.EX.{test}}}"
                    df_test = self.api.query_table(self.api.config.test_table, query_test, fid_test, fname_test)
                    if not df_test.empty:
                        csv_paths.append(str(df_test.loc[0, 'TDS filepath - raw data CSV']))

                if csv_paths:
                    csv_paths_str = ", ".join(csv_paths)
                    self.analyzer.plot_cycle_life(
                        temp_str, csv_paths_str, str(row[f"{mode} Cycling - Rates"]),
                        int(row[f"{mode} Cycling - max cycle"]), int(row[f"{mode} Cycling - ref cycle"]),
                        row[f"{mode} cycling plot - PNG path"], row[f"{mode} cycling plot, norm - PNG path"],
                        row["Cycling data folder"], prefix
                    )


if __name__ == "__main__":
    try:
        config = QuickBaseConfig()
        with ExecutionLogger('scheduledProcessedLog.csv') as logger:
            pipeline = TestPipeline(config, logger)
            pipeline.run()
    except ValidationError as e:
        print(f"Configuration Validation Error: {e}")
