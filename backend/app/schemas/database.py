from pydantic import BaseModel
from typing import List, Optional


class ColumnSchema(BaseModel):
    """Schema information for a database column."""
    column_name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str] = None
    character_maximum_length: Optional[int] = None
    is_primary_key: bool = False


class ForeignKeySchema(BaseModel):
    """Foreign key relationship information."""
    column_name: str
    foreign_table_name: str
    foreign_column_name: str
    constraint_name: str


class TableSchema(BaseModel):
    """Schema information for a database table."""
    table_name: str
    columns: List[ColumnSchema]
    primary_keys: List[str] = []
    foreign_keys: List[ForeignKeySchema] = []


class DatabaseSchema(BaseModel):
    """Complete database schema."""
    tables: List[TableSchema]
