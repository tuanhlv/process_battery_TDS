# ==========================================
# QuickBase API Client
# ==========================================

import requests
import pandas as pd
from config.settings import QuickBaseConfig
from utils.logger import ExecutionLogger

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
