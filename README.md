# mud-aw.py

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/mud-aw.py.git
cd mud-aw.py
pip install -e .
```


## MUD Indexer SDK

This repository provides a Python SDK for interacting with MUD-indexed databases. It allows users to parse a MUD configuration file, register tables dynamically, and query data using a simplified API.

## Features

- **Dynamic Table Registration:** Automatically register tables and schemas defined in a MUD configuration file.
- **SQL-like Queries:** Perform table queries with filtering and limit support.
- **Escaped Reserved Keywords:** Handles reserved SQL keywords in column names.
- **Error Handling:** Provides detailed error feedback for API requests.


---

## Usage

### 1. Initialize the SDK
Create an instance of `MUDIndexerSDK`:

```python
from mud_indexer_sdk import MUDIndexerSDK

indexer_url = "https://indexer.example.com"
world_address = "0x123...abc"
mud_config_path = "path/to/mud.config"

sdk = MUDIndexerSDK(indexer_url, world_address, mud_config_path)
```

---

### 2. Query Tables

Use the SDK to interact with dynamically registered tables. For example, if `Player` is defined in the MUD configuration:

```python
# Fetch up to 500 rows from the Player table with specific filters
players = sdk.tables.Player.get(limit=500, id=1, name="JohnDoe")

# Print the results
print(players)
```

---

### 3. Access Table Names

Retrieve a list of all registered tables:

```python
table_names = sdk.get_table_names()
print("Registered tables:", table_names)
```

---

## Code Overview

### `parse_mud_config(file_path: str)`

Parses the MUD configuration file to extract table names, schemas, and key definitions.

### `BaseTable`

Represents a single table. Provides methods for querying data and constructing SQL queries dynamically.

- **`get(limit=1000, **filters)`**: Query the table with optional filters.

### `TableRegistry`

Manages the dynamic creation and registration of table instances.

- **`register_table(table_name, schema, keys)`**: Registers a new table.

### `MUDIndexerSDK`

Main class for initializing the SDK, parsing the configuration file, and managing API requests.

- **`get_table_names()`**: Returns a list of all registered table names.

---

## Example MUD Configuration File

```yaml
Player:
  schema:
    id: "int"
    name: "string"
    level: "int"
  key: ["id"]
Monster:
  schema:
    id: "int"
    type: "string"
    strength: "int"
  key: ["id"]
```

---

## Requirements

- Python 3.7+
- `requests` library

Install dependencies with:

```bash
pip install requests
```

---

## Error Handling

- If the MUD configuration file is not properly formatted, an exception will be raised during initialization.
- API requests will throw an exception if the HTTP response status is not 200.

---

## Contributing

1. Fork the repository.
2. Create a new feature branch.
3. Submit a pull request.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

For more information or support, please contact the project maintainers.

