import re
import requests


def parse_mud_config(file_path: str):
    with open(file_path, "r") as f:
        content = f.read()
    
    # Extract tables and schemas
    table_pattern = r"(\w+):\s*{\s*schema:\s*{([^}]+)},\s*key:\s*\[([^]]+)]"
    matches = re.findall(table_pattern, content)

    tables = {}
    for table_name, schema_block, keys in matches:
        schema = {
            k.strip(): v.strip().strip('"')
            for k, v in re.findall(r"(\w+):\s*\"?(\w+\[\]?|\w+)\"?", schema_block)
        }
        keys = [k.strip().strip('"') for k in keys.split(",")]
        tables[table_name] = {"schema": schema, "key": keys}

    return tables


class BaseTable:
    RESERVED_SQL_KEYWORDS = {"exists", "from", "values", "limit", "index"}  # Add more keywords if needed

    def __init__(self, sdk, table_name, schema, keys):
        self.sdk = sdk
        self.table_name = table_name
        self.schema = schema
        self.keys = keys

    def _escape_column_name(self, column_name):
        """Escape column names that are reserved SQL keywords."""
        return f'"{column_name}"' if column_name in self.RESERVED_SQL_KEYWORDS else column_name

    def get(self, limit=1000, **filters):
        """
        Query the table with optional filters.

        Args:
            limit (int): Maximum number of rows to retrieve. Default is 1000.
            **filters: Key-value pairs to filter the query.

        Returns:
            List[Dict[str, Any]]: A list of records from the table.
        """
        # Determine the columns to select based on whether the keys are filtered
        if any(key in filters for key in self.keys):
            # Exclude keys from SELECT if they are filtered
            select_columns = ", ".join(
                self._escape_column_name(col)
                for col in self.schema.keys()
                if col not in self.keys
            )
        else:
            # Include all columns if no keys are filtered
            select_columns = ", ".join(
                self._escape_column_name(col) for col in self.schema.keys()
            )

        # Construct the WHERE clause
        where_clause = " AND ".join(
            f"{self._escape_column_name(key)}={repr(value)}" for key, value in filters.items()
        )

        query = f"SELECT {select_columns} FROM {self.table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += f" LIMIT {limit};"

        payload = [{"address": self.sdk.world_address, "query": query}]
        response = self.sdk.post(payload)
        return self._parse_response(response)

    def _parse_response(self, response):
        if "result" not in response or not response["result"]:
            return None  # Return None if there are no results

        results = response["result"][0]
        if not results:  # Check if the results array is empty
            return None

        headers, *rows = results
        return [dict(zip(headers, row)) for row in rows]


class TableRegistry:
    def __init__(self, sdk):
        self.sdk = sdk

    def register_table(self, table_name, schema, keys):
        """
        Dynamically create and register a table as an attribute of the registry.
        """
        table_class = type(table_name, (BaseTable,), {})
        table_instance = table_class(self.sdk, table_name, schema, keys)
        setattr(self, table_name, table_instance)


class MUDIndexerSDK:
    def __init__(self, indexer_url, world_address, mud_config_path):
        self.indexer_url = indexer_url
        self.world_address = world_address
        self.tables = TableRegistry(self)

        # Parse and register tables from the configuration file
        self._parsed_tables = parse_mud_config(mud_config_path)
        for table_name, table_info in self._parsed_tables.items():
            self.tables.register_table(table_name, table_info["schema"], table_info["key"])

    def post(self, payload):
        response = requests.post(self.indexer_url, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            raise Exception(f"Request failed with status {response.status_code}: {response.text}")
        return response.json()

    def get_table_names(self):
        """Return a list of all table names from the parsed configuration."""
        return list(self._parsed_tables.keys())
    