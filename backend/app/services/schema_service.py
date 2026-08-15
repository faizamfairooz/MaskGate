from typing import Dict, List, Optional

from app.database.postgresql import db
from app.schemas.database import ColumnSchema, DatabaseSchema, TableSchema, ForeignKeySchema


class SchemaService:
    """Service for database schema operations."""

    def get_schemas(self) -> List[str]:
        return db.get_schemas()

    def get_all_tables(self, schema: str = "public") -> List[str]:
        return db.get_tables(schema=schema, exclude_metadata=True)

    def get_full_schema(self, schema: str = "public") -> DatabaseSchema:
        tables = []
        for table_name in self.get_all_tables(schema=schema):
            tables.append(self.get_table_schema(table_name, schema=schema))
        return DatabaseSchema(tables=tables)

    def get_table_schema(self, table_name: str, schema: str = "public") -> TableSchema:
        if not db.table_exists(table_name, schema=schema):
            raise ValueError(f"Table '{table_name}' does not exist")

        columns_data = db.get_table_schema(table_name, schema=schema)
        primary_keys = db.get_primary_keys(table_name, schema=schema)
        foreign_keys_data = db.get_foreign_keys(table_name, schema=schema)

        columns = [
            ColumnSchema(
                column_name=col["column_name"],
                data_type=col["data_type"],
                is_nullable=col["is_nullable"] == "YES",
                column_default=col.get("column_default"),
                character_maximum_length=col.get("character_maximum_length"),
                is_primary_key=col["column_name"] in primary_keys,
            )
            for col in columns_data
        ]

        foreign_keys = [
            ForeignKeySchema(
                column_name=fk["column_name"],
                foreign_table_name=fk["foreign_table_name"],
                foreign_column_name=fk["foreign_column_name"],
                constraint_name=fk["constraint_name"],
            )
            for fk in foreign_keys_data
        ]

        return TableSchema(
            table_name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
        )
