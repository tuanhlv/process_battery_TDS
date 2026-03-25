# ==========================================
# Pydantic Models for Validation
# ==========================================

from pydantic import BaseModel, Field, ValidationError

class QuickBaseConfig(BaseModel):
    token: str = Field(default="user_token", description="QuickBase User Token")
    hostname: str = Field(default="https://company.quickbase.com", description="QuickBase Hostname")
    test_table: str = Field(default="test_table_id", description="Cell Test table ID")
    cell_part_table: str = Field(default="cell_table_id", description="Cell Part table ID")