Here’s the updated **Code Overview** section for the README, now including details about the `World` and `Player` classes:

---

### Code Overview

---

#### **MUDIndexerSDK**

The main class for interacting with MUD tables and querying data. It provides a dynamic interface for accessing and filtering table data.

##### **Functions**

**`parse_mud_config(file_path: str)`**  
Parses the MUD configuration file (`mud.config.ts`) to extract:
- **Table Names**: Identifies all the tables defined in the configuration.
- **Schemas**: Maps column names to their respective types.
- **Key Definitions**: Specifies the key columns for each table.

**Usage:**
```python
from mud import parse_mud_config

mud_config_path = "./path/to/mud.config.ts"
parsed_config = parse_mud_config(mud_config_path)
print(parsed_config)
```

---

##### **Classes**

**`BaseTable`**  
Represents a single table within the MUD world. Provides methods for querying data and constructing SQL-like queries dynamically.

- **`get(limit=1000, **filters):`**  
  Queries the table with optional filters and returns a list of matching rows.  
  - `limit`: Limits the number of rows returned (default: 1000).  
  - `filters`: Key-value pairs for filtering rows (e.g., `playerId=1, itemId=42`).

**Usage:**
```python
# Query a table with filters
inventory_items = world.indexer.Inventory.get(playerId=PLAYER_ID)

# Fetch all rows
all_items = world.indexer.Inventory.get()

# Limit results
limited_items = world.indexer.Inventory.get(limit=500)
```

**`TableRegistry`**  
Manages the dynamic creation and registration of table instances based on the parsed MUD configuration.

- **`register_table(table_name: str, schema: dict, keys: list):`**  
  Dynamically creates a `BaseTable` instance for the given table and registers it with the `TableRegistry`.

**Usage:**
```python
# Dynamically register a table
registry.register_table("Inventory", schema={"playerId": "uint256", "itemId": "uint256"}, keys=["playerId"])
```

**`MUDIndexerSDK`**  
The main SDK class for initializing the MUD Indexer, parsing the configuration file, and managing API requests.

- **`get_table_names():`**  
  Returns a list of all registered table names from the parsed configuration.

**Usage:**
```python
from mud import MUDIndexerSDK

indexer = MUDIndexerSDK(
    indexer_url="https://indexer.example.com",
    world_address="0x123...abc",
    mud_config_path="./path/to/mud.config.ts"
)

# List all registered table names
print(indexer.get_table_names())
```

---

#### **World**

The `World` class connects to a MUD world and provides access to its smart contract functions and indexer tables.

##### **Key Features**
- **Dynamic Smart Contract Integration:**  
  Functions from the world contract ABI are dynamically added to the `World` instance, complete with type hints.
- **Integrated Indexer:**  
  Optionally integrates with the MUD Indexer for table queries.

##### **Methods**

- **`set_indexer(indexer: MUDIndexerSDK):`**  
  Sets the MUD Indexer instance for the world, enabling table queries.
  
- **Dynamic Contract Functions**  
  Smart contract functions like `placeItem(x, y, z, itemId)` are dynamically available based on the ABI.

**Usage:**
```python
from mud import World

abi_dir = "./path/to/abi"
rpc = "https://rpc.mudchain.com"
world_address = "0x123...abc"
indexer_url = "https://indexer.mudchain.com"
mud_config_path = "./path/to/mud.config.ts"

world = World(
    rpc=rpc,
    world_address=world_address,
    abi_dir=abi_dir,
    indexer_url=indexer_url,
    mud_config_path=mud_config_path
)

# Call a contract function
world.placeItem(x=1, y=1, z=1, itemId=42)

# Query a table
player_inventory = world.indexer.Inventory.get(playerId=PLAYER_ID)
```

---

#### **Player**

The `Player` class wraps interactions with a MUD world for a specific player. It simplifies signing and sending transactions and enables seamless access to world functions.

##### **Key Features**
- **Private Key Management:**  
  Derives the player's address from the private key or loads it from an environment variable.
- **World Integration:**  
  Associates a world with the player, allowing direct calls to its functions.
- **Automatic Transactions:**  
  Automatically signs and sends transactions for contract calls.

##### **Methods**

- **`add_world(world: World, world_name: str):`**  
  Associates a world with the player. The world becomes accessible as an attribute with the specified name.

**Usage:**
```python
from mud import Player

# Initialize the Player
private_key = "0xYourPrivateKey"
player = Player(private_key=private_key)

# Link the World to the Player
player.add_world(world, "cafecosmos")

# Call a contract function through the Player
player.cafecosmos.placeItem(x=1, y=1, z=1, itemId=100)
```

- **Environment Variable Support**  
  Initialize the player by loading the private key from an environment variable:
  ```python
  player = Player(env_key_name="PLAYER1")
  ```

---

### Summary of Components

| Component       | Purpose                                        |
|------------------|------------------------------------------------|
| **MUDIndexerSDK** | Query MUD tables and manage table schemas      |
| **World**        | Interact with smart contract functions and tables |
| **Player**       | Simplify player-specific interactions and automate transactions |

