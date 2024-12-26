# mud-aw.py

#### Python tools for:
 
- querying mud tables
- creating your own python game wrappers
- interacting with worlds
and more

#### Use case

- create data dashboards of MUD worlds
- automate in-game actions
- create game-specific libraries for player interactions (wrappers)

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/mud-aw.py.git
cd mud-aw.py
pip install -e .
```


## MUD Indexer SDK

The MUD Indexer SDK allows users to parse a MUD configuration file, register tables dynamically, and query data using a simplified API.

## Features

- **Dynamic Table Registration:** Automatically register tables and schemas defined in a MUD configuration file.
- **SQL-like Queries:** Perform table queries with filtering and limit support.


---

## Usage

### 1. Initialize the SDK
Create an instance of `MUDIndexerSDK`:

```python
from mud import MUDIndexerSDK

indexer_url = "https://indexer.example.com"
world_address = "0x123...abc"
mud_config_path = "path/to/mud.config"

sdk = MUDIndexerSDK(indexer_url, world_address, mud_config_path)
```

---

### 2. Query Tables

Use the SDK to interact with dynamically registered tables. For example, if `Player` is defined in the MUD configuration:

```python
# Fetch tables and filter by properties
pickaxe_balance = sdk.tables.Inventory.get(playerId=PLAYER_ID, itemId=PICKAXE_ID)

# Fetch every table entry. limit is the max amount of inventories you want returned, defautls to 1000
inventories = sdk.tables.Inventory.get(limit=500)
```

---

### 3. Access Table Names

Retrieve a list of all tables registered to the world:

```python
table_names = sdk.get_table_names()
print("Registered tables:", table_names)
```

---

## Contributing

1. Fork the repository.
2. Create a new feature branch.
3. Submit a pull request.


