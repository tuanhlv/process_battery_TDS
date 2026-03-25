# ==========================================
# Main Processor Pipeline
# ==========================================

from config import QuickBaseConfig
from utils import ExecutionLogger
from analytics import plot_rate_charge, plot_rate_discharge, plot_temperature_perf, plot_dcir, plot_ocv, plot_cycle_life
from api import QuickBaseAPIClient


class TestPipeline:
    """Orchestrates the querying and plotting pipeline."""

    def __init__(self, qb_config: QuickBaseConfig, exec_logger: ExecutionLogger):
        self.api = QuickBaseAPIClient(config, logger)
        self.logger = exec_logger

    def process_cell_tests(self) -> None:
        fids = ["3", "203", "443", "444", "445", "446", "447", "448", "457", "458",
                "460", "454", "497", "461", "463", "462", "464", "465", "466", "504",
                "469", "470", "480", "486", "495"]
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
                  "TDS Input - DCIR Pulse C-rate", "TDS filepath - CSV folder"]

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

            if row.get('TDS Input - Charge Profiling - Cycle Numbers') and row.get('TDS Input - Charge Profiling - Charge Rates'):
                self.logger.log("  -> Plotting charge profiles")
                plot_rate_charge(
                    raw_csv, row['TDS Input - Charge Profiling - Cycle Numbers'],
                    row['TDS Input - Charge Profiling - Charge Rates'], row['TDS filepath - charge profile PNG1'],
                    row['TDS filepath - charge profile PNG2'],
                    row['TDS filepath - charge rate capability results CSV'], folder
                )

            if row.get('TDS Input - Rate Capability - Cycle Numbers') and row.get('TDS Input - Rate Capability - Discharge Rates'):
                self.logger.log("  -> Plotting discharge profiles")
                plot_rate_discharge(
                    raw_csv, row['TDS Input - Rate Capability - Cycle Numbers'],
                    row['TDS Input - Rate Capability - Discharge Rates'], row['TDS filepath - discharge profile PNG'],
                    row['TDS filepath - discharge profile, norm PNG'],
                    row['TDS filepath - discharge rate capability results CSV'], folder
                )

            if row.get('TDS Input - Temperature Perf - Cycle Numbers') and row.get('TDS Input - Temperature Perf - Discharge Temperature'):
                self.logger.log("  -> Plotting HLT discharge profiles")
                plot_temperature_perf(
                    raw_csv, row['TDS Input - Temperature Perf - Cycle Numbers'],
                    row['TDS Input - Temperature Perf - Discharge Temperature'],
                    row['TDS filepath - HLT discharge profile PNG'],
                    row['TDS filepath - HLT norm PNG'], row['TDS filepath - temperature performance results CSV'],
                    folder
                )

            if row.get('TDS Input - OCV vs SOC'):
                self.logger.log("  -> Plotting OCV profile")
                plot_ocv(raw_csv, row["TDS filepath - OCV PNG"])

            if row.get('TDS Input - DCIR vs SOC'):
                self.logger.log("  -> Plotting DCIR profile")
                plot_dcir(
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
                    plot_cycle_life(
                        temp_str, csv_paths_str, str(row[f"{mode} Cycling - Rates"]),
                        int(row[f"{mode} Cycling - max cycle"]), int(row[f"{mode} Cycling - ref cycle"]),
                        row[f"{mode} cycling plot - PNG path"], row[f"{mode} cycling plot, norm - PNG path"],
                        row["Cycling data folder"], prefix
                    )
                    
    def run(self) -> None:
        self.process_cell_tests()
        self.process_cell_parts()