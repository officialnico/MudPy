import os
import numpy as np
import pandas as pd
from thefuzz import process
from IPython.display import HTML
from typing import Optional, List, Dict
from executing.executing import NotOneValueFound
from web3.exceptions import ContractCustomError
from web3 import Web3
from eth_abi.packed import encode_packed

from mud import World as _World
from mud import Player as _Player


prefix = "./cafecosmos-contracts/icons/"

class World(_World):

    def __init__(self, rpc, world_address, abis_dir, indexer_url=None, mud_config_path=None, block_explorer_url=None):
        super().__init__(rpc, world_address, abis_dir, indexer_url, mud_config_path, block_explorer_url)
        add_external_contracts(self)

class Player(_Player):
    def __init__(
        self, 
        world: _World, 
        private_key: Optional[str] = None, 
        env_key_name: Optional[str] = None, 
        land_id: Optional[int] = None
    ) -> None:
        """
        Initialize a Player instance.
        
        Args:
            world (_World): The World object instance.
            private_key (Optional[str]): The private key of the player (default: None).
            env_key_name (Optional[str]): The environment key name for the private key (default: None).
            land_id (Optional[int]): The land ID associated with the player (default: None).
        """
        super().__init__(private_key, env_key_name)
        self.cafecosmos: _World = world
        add_external_contracts(world)

        if land_id is None:
            land_ids = find_player_lands(world, self.player_address, 1)
            if not land_ids:
                print("No lands found for the player... Create a new land with create_land(x, y) before proceeding.")
            land_id = land_ids[0]
        else:
            if(self.cafecosmos.LandNFTs.functions.ownerOf(land_id).call() != self.player_address):
                raise ValueError("The player does not own the specified land.")
        
        self.land_id: int = land_id

    def display_land(self) -> HTML:
        """
        Display the land grid for the player's land.

        Returns:
            HTML: The HTML object containing the land grid.
        """
        return display_land(self.cafecosmos, self.land_id)
    
    def display_inventory(self) -> HTML:
        """
        Display the player's inventory with icons and quantities.

        Returns:
            HTML: The HTML object containing the inventory display.
        """
        return display_inventory(self.cafecosmos, self.land_id)
    
    def place_item(self, x: int, y: int, item_name: str) -> None:
        """
        Place an item on the player's land.

        Args:
            x (int): The x-coordinate to place the item.
            y (int): The y-coordinate to place the item.
            item_name (str): The name of the item to place.
        """
        place_item(self, self.land_id, x, y, name_to_id_fuzzy(item_name))

    def create_land(self, limit_x: int, limit_y: int) -> None:
        """
        Create a new land for the player.

        Args:
            limit_x (int): The limit of the x-coordinate grid.
            limit_y (int): The limit of the y-coordinate grid.
        """
        create_land(self, limit_x, limit_y)
        print("Created land, setting new land ID...")
        land_ids = find_player_lands(self.cafecosmos, self.player_address, 1)
        if(not land_ids):
            raise ValueError("No lands found for the player after creation.")
        self.land_id = land_ids[0]
    
    def find_player_lands(self, amount_of_lands: int = 0) -> List[int]:
        """
        Find all lands owned by the player.

        Args:
            amount_of_lands (int): Maximum number of lands to find. Default is 0 (no limit).

        Returns:
            List[int]: A list of land IDs owned by the player.
        """
        return find_player_lands(self.cafecosmos, self.player_address, amount_of_lands)

    def get_inventory(self) -> Dict[str, int]:
        """
        Get the player's inventory as a dictionary.

        Returns:
            Dict[str, int]: A dictionary where keys are item names and values are their quantities.
        """
        return get_inventory(self.cafecosmos, self.land_id)
    
    def get_eth_balance(self) -> int:
        """
        Get the player's balance.

        Returns:
            int: The player's balance.
        """
        return self.cafecosmos.w3.eth.get_balance(self.player_address)

    def get_leaderboard(self) -> pd.DataFrame:
        """
        Get the leaderboard of players.

        Returns:
            pd.DataFrame: The leaderboard DataFrame.
        """
        leaderboard = self.cafecosmos.indexer.PlayerTotalEarned.get()
        
    def transfer_eth(self, to_address: str, amount: int) -> None:
        """
        Transfer ETH to another address.

        Args:
            to_address (str): The recipient address.
            amount (int): The amount of ETH to transfer.
        """
        function_call = self.cafecosmos.w3.eth.send_transaction({
            "from": self.player_address,
            "to": to_address,
            "value": amount,
        })
        _execute_function_call(self, function_call)

    def craft_item(self, item_name: str, quantity=1) -> None:
        """
        Craft an item using the player's inventory.

        Args:
            item_name (str): The name of the item to craft.
        """
        item_id = name_to_id_fuzzy(item_name)
        # for _ in range(quantity):
        craft_item_recursive(player=self, item_id=item_id, quantity=quantity)
        
    def get_craftable(self) -> pd.DataFrame:
        """
        Get a list of craftable items and the maximum quantity of each based on the player's inventory.

        Returns:
            pd.DataFrame: A DataFrame containing craftable items and their maximum quantities.
        """
        return get_craftable(self)
    
    @staticmethod
    def name_to_id_fuzzy(name: str, threshold: int = 80) -> int:
        """
        Given a (possibly misspelled) item name, return the best matching item ID
        if the fuzzy match is ≥ threshold. Otherwise, return None.
        """
        return name_to_id_fuzzy(name, threshold)
    
    @staticmethod
    def id_to_name(id: int) -> str:
        """
        Given an item ID, return the corresponding item name.
        """
        items_df = get_items()
        return items_df[items_df["ID"] == id]["Name"].values[0]

### Helper functions ###

def display_land(world: World, land_id: int):
    # 1) Get the land as a DataFrame
    df = get_land(world, land_id)

    # 2) Load items.csv and build ID → Name dictionary
    items_df = get_items()
    id_to_property = dict(zip(items_df["ID"], items_df["Name"]))

    # 3) Build the list of icon “base names” (filenames without .png)
    icon_files = os.listdir(prefix)
    icon_bases = [os.path.splitext(filename)[0] for filename in icon_files]

    # 4) Convert item IDs to icon paths (where possible)
    df_icons = df.applymap(lambda val: _replace_with_icons(val, id_to_property, icon_bases))

    # 5) Create a copy of your DataFrame and apply the formatter to every cell
    df_display = df_icons.applymap(path_to_image_html)

    # 6) Convert to HTML, making sure to disable HTML-escaping
    html = df_display.to_html(escape=False)

    # 7) Display inline in Jupyter (or return/print as needed)
    return HTML(html)

def get_land(world: World, land_id: int) -> pd.DataFrame:
    """
    Fetch land from the indexer, pick the topmost item (highest z, tie-break on
    placementtime), and return a 10×10 DataFrame of item IDs.
    """
    player_land = world.indexer.LandItem.get(landId=land_id)
    
    # Group by (x,y) and keep track of z, placementtime, itemid
    coord_map = {}
    for row in player_land:
        x = int(row["x"])
        y = int(row["y"])
        z = int(row["z"])
        t = int(row["placementtime"])
        item = int(row["itemid"])
        coord_map.setdefault((x, y), []).append((z, t, item))

    # For each (x, y), pick the topmost item by sorting on (z, placementtime)
    top_items = {}
    for (x, y), items in coord_map.items():
        items.sort(key=lambda triple: (triple[0], triple[1]))
        top_z, top_t, top_itemid = items[-1]  # largest z/t
        top_items[(x,y)] = top_itemid

    # Build a 10×10 grid, filling None if no item
    grid = []
    for y in range(10):
        row = []
        for x in range(10):
            row.append(top_items.get((x,y), np.nan))
        grid.append(row)

    df = pd.DataFrame(grid)
    df.index.name = "y"
    df.columns.name = "x"
    return df

def get_items() -> pd.DataFrame:
    """
    Load item definitions (ID, Name, etc.) from CSV.
    """
    items_df = pd.read_csv("cafecosmos-contracts/Items.csv")
    return items_df

def _find_icon_filename(property_str: str, icon_bases: list[str]) -> str:
    """
    Use fuzzy matching to find the best icon filename for a given item name.
    Return None if below the similarity threshold (e.g. 80).
    """
    lower_prop = property_str.lower()
    best_match, score = process.extractOne(lower_prop, icon_bases)
    if score >= 80:
        return best_match + ".png"
    return None

def _replace_with_icons(val, id_to_property, icon_bases):
    """
    Given a cell value (item ID), return a path to the .png icon if available,
    otherwise return NaN or the original value.
    """
    if pd.isna(val) or val == 0:
        return np.nan

    # Convert (e.g. float to int) for safer dictionary lookup
    val_int = int(val)
    if val_int not in id_to_property:
        return np.nan

    property_str = id_to_property[val_int]
    icon_filename = _find_icon_filename(property_str, icon_bases)
    if icon_filename is None:
        return val  # fallback to item ID or could be np.nan
    else:
        return os.path.join(prefix, icon_filename)

def path_to_image_html(path):
    """
    If the cell has a string ending in .png, return an HTML <img> tag.
    Otherwise, return the original value.
    """
    if isinstance(path, str) and path.endswith(".png"):
        return f'<img src="{path}" width="50"/>'
    else:
        return path

def find_player_lands(world, player_address, amount_of_lands=0):
    lands = []
    for i in range(1, 1000):
        try:
            owner = world.LandNFTs.functions.ownerOf(i).call()
            if owner == player_address:
                lands.append(i)
                if(amount_of_lands > 0 and len(lands) >= amount_of_lands):
                    break
        except:
            break
    return lands

def add_external_contracts(world):
    external_contract_addresses = world.indexer.ConfigAddresses.get(limit=10)
    world.add_contract("Redistributor", external_contract_addresses[0]["redistributoraddress"], world.abis["Redistributor"])
    world.add_contract("PerlinItemConfig", external_contract_addresses[0]["perlinitemconfigaddress"], world.abis["PerlinItemConfig"])
    world.add_contract("LandNFTs", external_contract_addresses[0]["landnftsaddress"], world.abis["LandNFTs"])
    world.add_contract("Vesting", external_contract_addresses[0]["vestingaddress"], world.abis["Vesting"])

def display_inventory(world: World, land_id: int):
    """
    Display the inventory of a land with icons and quantities in a DataFrame,
    excluding rows that have 0 quantity.
    """
    # Fetch inventory data for the land
    inventory = world.indexer.Inventory.get(landId=land_id)

    # Convert inventory data to a DataFrame
    inventory_df = pd.DataFrame(inventory)
    inventory_df["item"] = inventory_df["item"].astype(int)
    inventory_df["quantity"] = inventory_df["quantity"].astype(int)

    # Exclude rows where quantity is 0
    inventory_df = inventory_df[inventory_df["quantity"] != 0]

    # Load items.csv to build ID → Name mapping
    items_df = get_items()
    id_to_name = dict(zip(items_df["ID"].astype(int), items_df["Name"]))

    # Add item names to the inventory DataFrame
    inventory_df["name"] = inventory_df["item"].map(id_to_name)

    # Build the list of icon base names
    icon_files = os.listdir(prefix)
    icon_bases = [os.path.splitext(filename)[0] for filename in icon_files]

    # Map item names to icon paths with the full prefix
    inventory_df["icon"] = inventory_df["name"].apply(
        lambda name: _find_icon_filename(name, icon_bases)
    )
    inventory_df["icon"] = inventory_df["icon"].apply(
        lambda filename: os.path.join(prefix, filename) if filename else None
    )

    # Convert icon paths to HTML image tags
    inventory_df["icon_html"] = inventory_df["icon"].apply(path_to_image_html)

    # Create the final DataFrame for display
    display_df = inventory_df[["icon_html", "name", "quantity"]].copy()
    display_df.rename(
        columns={"icon_html": "Icon", "name": "Item Name", "quantity": "Quantity"},
        inplace=True,
    )

    # Convert to HTML and display
    html = display_df.to_html(escape=False, index=False)
    return HTML(html)

def name_to_id_fuzzy(name: str, threshold: int = 80) -> int:
    """
    Given a (possibly misspelled) item name, return the best matching item ID
    if the fuzzy match is ≥ threshold. Otherwise, return None.
    """
    # Load items.csv
    items_df = get_items()  # Your existing function to load the CSV

    # Build a dict: Name -> ID
    name_to_id_map = dict(zip(items_df["Name"], items_df["ID"]))

    # Find the best match
    best_match, score = process.extractOne(name, name_to_id_map.keys())

    # If score >= threshold, return its ID; else None
    if score >= threshold:
        return name_to_id_map[best_match]
    
    raise Exception(f"Could not find a match for {name} with a score of {score}")

def get_system_resource_id(system_name: str) -> str:
    """
    Generate the ResourceId for a system in MUD.

    Args:
        system_name (str): The name of the system (e.g., "CraftingSystem").

    Returns:
        str: The hexadecimal representation of the ResourceId.
    """
    # Constants
    RESOURCE_SYSTEM = Web3.keccak(text="system")[:16]

    # Encode namespace and system name
    namespace_bytes = b"".ljust(14, b'\0')  # Empty namespace, 14 bytes
    system_name_bytes = system_name.encode('utf-8')[:16].ljust(16, b'\0')  # System name, 16 bytes

    # Concatenate components
    concatenated = RESOURCE_SYSTEM + namespace_bytes + system_name_bytes

    # Compute ResourceId
    resource_id = Web3.keccak(concatenated)

    return resource_id.hex()

def _execute_function_call(player, function_call):
    try:
        # Estimate gas and send the transaction
        estimated_gas = function_call.estimate_gas({"from": player.player_address})
        txn = function_call.build_transaction({
            "chainId": player.cafecosmos.chain_id,
            "gas": estimated_gas,
            "gasPrice": player.cafecosmos.w3.eth.gas_price,
            "nonce": player.cafecosmos.w3.eth.get_transaction_count(player.player_address),
        })
        signed_txn = player.cafecosmos.w3.eth.account.sign_transaction(txn, player.private_key)
        txn_hash = player.cafecosmos.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Transaction sent. TX hash: {txn_hash.hex()}")
    except ContractCustomError as e:
        # Extract error data from the exception (it is returned as a tuple)
        error_data = e.args[0] if isinstance(e.args, tuple) else str(e)
        selector = error_data[2:10]  # First 4 bytes (without the "0x" prefix)

        # Match the selector in player.cafecosmos.errors
        if selector in player.cafecosmos.errors:
            error_info = player.cafecosmos.errors[selector]
            error_name = error_info[1]
            raise Exception(f"Transaction failed with custom error: {error_name}")
        else:
            raise Exception(f"Transaction failed with unknown custom error: {error_data}")
    except Exception as e:
        raise Exception(f"Transaction failed: {str(e)}")

def _execute_batch_call(player, batch_calls):
    # Execute the batchCall
    try:
        print(f"Executing batch call with {len(batch_calls)} crafting calls...")

        # Prepare the systemCalls parameter
        system_calls = batch_calls  # No further transformation is needed

        # Build the transaction
        txn = player.cafecosmos.batchCall(system_calls).build_transaction(
            {
                "from": player.player_address,
                "gasPrice": player.cafecosmos.w3.eth.gas_price,
                "nonce": player.cafecosmos.w3.eth.get_transaction_count(player.player_address),
            }
        )

        # Sign and send the transaction
        signed_txn = player.cafecosmos.w3.eth.account.sign_transaction(txn, player.private_key)
        txn_hash = player.cafecosmos.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        print(f"Batch transaction sent. TX hash: {txn_hash.hex()}")
    except ContractCustomError as e:
        # Extract error data from the exception (it is returned as a tuple)
        error_data = e.args[0] if isinstance(e.args, tuple) else str(e)
        selector = error_data[2:10]  # First 4 bytes (without the "0x" prefix)

        # Match the selector in player.cafecosmos.errors
        if selector in player.cafecosmos.errors:
            error_info = player.cafecosmos.errors[selector]
            error_name = error_info[1]
            raise Exception(f"Transaction failed with custom error: {error_name}")
        else:
            raise Exception(f"Transaction failed with unknown custom error: {error_data}")
    except Exception as e:
        raise Exception(f"Transaction failed: {str(e)}")

def place_item(player: Player, land_id: int, x: int, y: int, item_id: int):
    """
    Place an item on a land at the specified coordinates.
    """
    # Call the placeItem function in the World contract
    function_call = player.cafecosmos.placeItem(land_id, x, y, item_id, mode="raw")
    _execute_function_call(player=player, function_call=function_call)

def create_land(player: Player, limit_x: int, limit_y: int):
    """
    Create a new land for the player.
    """
    # Call the createLand function in the World contract
    function_call = player.cafecosmos.createLand(limitX=limit_x, limitY=limit_y, mode="raw")
    _execute_function_call(player=player, function_call=function_call)

def _craft_item(player: Player, item_id: int):
    """
    Craft an item using the player's inventory.
    """
    # Call the craftItem function in the World contract
    function_call = player.cafecosmos.craftRecipe(player.land_id, item_id, mode="raw")
    _execute_function_call(player=player, function_call=function_call)

def get_inventory(world: World, land_id: int) -> dict:
    """
    Fetch the inventory of a land and return it as a dictionary with item names
    as keys and their quantities as values.
    """
    # Fetch inventory data for the land
    inventory = world.indexer.Inventory.get(landId=land_id)

    # Convert inventory data to a DataFrame
    inventory_df = pd.DataFrame(inventory)
    inventory_df["item"] = inventory_df["item"].astype(int)
    inventory_df["quantity"] = inventory_df["quantity"].astype(int)

    # Exclude rows where quantity is 0
    inventory_df = inventory_df[inventory_df["quantity"] != 0]

    # Load items.csv to build ID → Name mapping
    items_df = get_items()
    id_to_name = dict(zip(items_df["ID"].astype(int), items_df["Name"]))

    # Add item names to the inventory DataFrame
    inventory_df["name"] = inventory_df["item"].map(id_to_name)

    # Convert the DataFrame to a dictionary
    inventory_dict = dict(zip(inventory_df["name"], inventory_df["quantity"]))

    return inventory_dict

def craft_item_recursive(player: Player, item_id: int, quantity: int):
    """
    Recursively craft an item using batchCall, automatically handling intermediate crafting steps.

    Args:
        player (Player): The player instance performing the crafting.
        item_id (int): The ID of the item to craft.
        quantity (int): The quantity of the item to craft.
    """
    items_to_craft = {item_id: quantity}
    batch_calls = []  # List to store all batch calls

    def _craft_item_recursive(player: Player, item_id: int):
        # Get all crafting recipes
        recipes = player.cafecosmos.indexer.CraftingRecipe.get()

        # Find the recipe for the desired item
        recipe = next((r for r in recipes if int(r["output"]) == item_id), None)
        if not recipe:
            return

        # Check the player's inventory
        inventory = player.get_inventory()
        current_quantity = inventory.get(item_id, 0)

        # If the item is already in inventory, no need to craft it
        if current_quantity > 0:
            return

        # Recursively craft all required inputs
        for input_id, quantity_needed in zip(recipe["inputs"], recipe["quantities"]):
            input_id = int(input_id)
            quantity_needed = int(quantity_needed)
            input_quantity = inventory.get(input_id, 0)

            # Craft the necessary quantity of the input
            if input_quantity < quantity_needed:
                missing_quantity = quantity_needed - input_quantity
                for _ in range(missing_quantity):
                    _craft_item_recursive(player, input_id)

        # Add the crafting call for the current item to the batch
        print(f"Adding batch call to craft item ID {item_id}")
        craft_function_data = player.cafecosmos.contract.functions.craftRecipe(
            player.land_id, item_id
        ).build_transaction({"from": player.player_address})["data"]

        # Encode the system ID (use namespace if applicable)
        crafting_system_id = get_system_resource_id("Crafting")

        # Append the crafting call to the batch
        batch_calls.append(
            (
                Web3.to_bytes(hexstr=crafting_system_id.hex()),  # Convert to bytes32
                Web3.to_bytes(hexstr=craft_function_data),  # Convert to bytes
            )
        )

    # Start the recursive crafting process
    _craft_item_recursive(player, item_id)

    _execute_batch_call(player, batch_calls)

def get_craftable(player: Player) -> pd.DataFrame:
    """
    Get a list of craftable items, the maximum quantity of each based on the player's inventory,
    and the required items and their quantities for each recipe.

    Args:
        player (Player): The player instance.

    Returns:
        pd.DataFrame: A DataFrame containing craftable items, their maximum quantities,
                      and their required items with quantities.
    """
    # Retrieve all crafting recipes
    recipes = player.cafecosmos.indexer.CraftingRecipe.get()

    # Fetch the player's current inventory
    inventory = player.get_inventory()

    # Load items.csv to build ID → Name mapping
    items_df = get_items()
    id_to_name = {int(row["ID"]): row["Name"].strip() for _, row in items_df.iterrows()}

    # Standardize inventory keys: strip whitespace and convert to lowercase for consistency
    standardized_inventory = {k.strip().lower(): v for k, v in inventory.items()}

    # Prepare a list to store craftable items
    craftable = []

    for recipe in recipes:
        output_id = int(recipe["output"])
        output_name = id_to_name.get(output_id, f"Unknown ID {output_id}")

        input_ids = list(map(int, recipe["inputs"]))
        input_quantities = list(map(int, recipe["quantities"]))

        # Gather requirements
        requirements = []
        max_craftable = float('inf')  # Start with a very large number

        for input_id, input_quantity in zip(input_ids, input_quantities):
            input_name = id_to_name.get(input_id, f"Unknown ID {input_id}")
            available_quantity = standardized_inventory.get(input_name.lower(), 0)

            requirements.append(f"{input_quantity} x {input_name}")

            if available_quantity < input_quantity:
                max_craftable = 0
                break
            else:
                possible = available_quantity // input_quantity
                if possible < max_craftable:
                    max_craftable = possible

        if max_craftable > 0:
            requirements_str = ", ".join(requirements)
            craftable.append({
                "Item ID": output_id,
                "Item Name": output_name,
                "Max Craftable": max_craftable,
                "Requirements": requirements_str
            })

    craftable_df = pd.DataFrame(craftable)
    pd.set_option('display.max_colwidth', None)


    return craftable_df
