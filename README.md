# mud-aw.py 🧱🐍


A Python API for MUD worlds

**Handle hundreds of bots across multiple chains on multiple worlds**

#### Python tools for:

- Querying [MUD](https://mud.dev/) tables
- Creating Python game wrappers
- Interacting with MUD worlds

#### Use Cases

- Create data dashboards for MUD worlds
- Automate in-game actions
- Build game-specific libraries for player interactions

---

## Installation

```bash
pip install mud-aw.py
```

or build from source

```bash
cd mud-aw.py
pip install -e .
```

---

## Possibilities

```python
from mud import World, Player
from IPython.display import display

#Create world objects
biomes = World(rpc, world_address, abi_dir, indexer_url, mud_config_path)
cafecosmos = World(c_rpc, c_world_address, c_abi_dir, c_indexer_url, c_mud_config_path)
primodium = World(p_rpc, p_world_address, p_abi_dir, p_indexer_url, p_mud_config_path)

#Load player(s) and link worlds
player = Player(env_key_name="PLAYER1")
player.add_world(biomes, "biomes")
player.add_world(cafecosmos, "cafecosmos")
player.add_world(primodium, "primodium")

#Execute onchain actions
player.biomes.mine(...) 
player.cafecosmos.placeItem(...)
player.primodium.fight(...)

#Query indexer
player.biomes.indexer.Map.get(x=1, y=2, z=1) #filter by row
player.cafecosmos.indexer.Inventory.get(landId=1337)
player.primodium.indexer.Alliance.get() #returns every entry in that table

#Download multiple or single world tables from the indexer as Pandas DataFrames with optional filtering params
biomes_tables_dfs = player.biomes.indexer.dl_tables_as_dataframes() #dl every table as dataframes
cafecosmos_inventories_df = player.cafecosmos.indexer.Inventory.to_dataframe() #dl individual tables

#Display DataFrames
display(biomes_tables_dfs["Map"])
display(cafecosmos_inventories_df)
```

---

## Key Components

### **MUD Indexer SDK**

The MUD Indexer SDK provides a simplified interface for querying MUD tables.

#### Inputs:
- **MUD Indexer URL**
- **World Address**
- Path to the `mud.config.ts` file

![fast_compressed_mud_sdk](https://github.com/user-attachments/assets/092bc23b-7253-4f71-a3f8-232d653386a9)

1. **Individual Table Downloads**: Query individual tables and download their data as Pandas DataFrames.
   ```python
   crafting_recipe_df = sdk.tables.CraftingRecipe.to_dataframe()
   ```
2. **Batch Table Downloads**: Download all tables as DataFrames for analysis.
   ```python
   all_tables = sdk.dl_tables_as_dataframes()
   print(all_tables["CraftingRecipe"].head())
   ```

---

### **World Class**

The `World` class allows you to interact with a MUD world and its smart contract functions. It dynamically registers functions based on the ABI, providing type-safe access and auto-completion in your IDE.

#### Features:
- **Smart Contract Integration**: Interact with world contract functions directly.
- **Dynamic Typing**: Input arguments and return types are dynamically typed based on the ABI.
- **Integrated Indexer**: Optionally link the MUD Indexer for seamless access to table data.

---

### **Player Class**

The `Player` class simplifies interactions with a MUD world for a specific player. It can:
- Derive the player address from a private key
- Automatically sign and send transactions
- Dynamically wrap world functions for player-specific interactions

---

## Usage

### 1. Initialize the World

The `World` class connects to a MUD world and optionally integrates the MUD Indexer.

```python
from mud import World

abi_dir = "./path/to/abis_directory"
rpc = "https://rpc.mudchain.com"
world_address = "0x123...abc"
indexer_url = "https://indexer.mudchain.com"
mud_config_path = "./path/to/mud.config.ts"

# Initialize the World with an optional indexer
world = World(
    rpc=rpc,
    world_address=world_address,
    abi_dir=abi_dir,
    indexer_url=indexer_url,
    mud_config_path=mud_config_path
)
```

---

### 2. Access Contract Functions

Functions from the world's ABI are dynamically registered on the `World` instance with type-safe signatures.

```python
# Call a smart contract function directly
land_items = world.getLandItems(user="0x123...")
print(land_items)

# Use IDE auto-completion for arguments and types
world.placeItem(x=1, y=2, z=3, itemId=42)
```

---

### 3. Query Tables with the Indexer

If the world is linked to a MUD Indexer, you can query tables directly.

```python
# Fetch all entries from the Inventory table
inventories = world.indexer.Inventory.get()

# Filter entries by playerId and itemId
player_inventory = world.indexer.Inventory.get(playerId=PLAYER_ID, itemId=ITEM_ID)

# Limit results
limited_inventories = world.indexer.Inventory.get(limit=500)
```

#### Table Querying Methods:

- **Download Individual Tables**
   ```python
   crafting_recipe_df = sdk.tables.CraftingRecipe.to_dataframe()
   print(crafting_recipe_df)
   ```

- **Batch Download All Tables**
   ```python
   all_tables_df = sdk.dl_tables_as_dataframes()
   print(all_tables_df["CraftingRecipe"])
   ```

---

### 4. Initialize a Player

The `Player` class wraps interactions for a specific player.

```python
from mud import Player

private_key = "0xYourPrivateKey"

# Initialize the Player
player = Player(private_key=private_key)

# Link the World to the Player
player.add_world(world, "cafecosmos")

# Call functions directly through the Player
player.cafecosmos.placeItem(x=1, y=1, z=1, itemId=100)
```

You can also load the private key from an environment variable:

```python
player = Player(env_key_name="PLAYER1")
```

---

## Features

- **Dynamic Table Registration**: Automatically register tables and schemas defined in a MUD configuration file.
- **SQL-like Queries**: Query tables with filtering.
- **Smart Contract Interactions**: Access world contract functions dynamically.
- **Player-Specific Wrappers**: Automate transactions and player actions.
- **Individual and Batch Table Downloads**: Flexible methods for accessing table data as DataFrames.

---

## Contributing

1. Fork the repository.
2. Create a new feature branch.
3. Submit a pull request.

