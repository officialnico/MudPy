
### Code Overview -- MUDIndexerSDK

#### `parse_mud_config(file_path: str)`

Parses the MUD configuration file to extract table names, schemas, and key definitions.

#### `BaseTable`

Represents a single table. Provides methods for querying data and constructing SQL queries dynamically.

- **`get(limit=1000, **filters)`**: Query the table with optional filters.

#### `TableRegistry`

Manages the dynamic creation and registration of table instances.

- **`register_table(table_name, schema, keys)`**: Registers a new table.

#### `MUDIndexerSDK`

Main class for initializing the SDK, parsing the configuration file, and managing API requests.

- **`get_table_names()`**: Returns a list of all registered table names.
