import os
import numpy as np
import pandas as pd
from thefuzz import process
from IPython.display import HTML
from typing import Optional, List, Dict, Tuple
from executing.executing import NotOneValueFound
from web3.exceptions import ContractCustomError
from web3 import Web3
from eth_abi.packed import encode_packed
import time

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
        if(item_name=="unlock"):
            item_id=0
        else: 
            item_id=name_to_id_fuzzy(item_name)
        
        place_item(self, self.land_id, x, y, item_id)

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
        for _ in range(quantity):
            _craft_item(player=self, item_id=item_id)
        
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
    
    def get_unlockable_transformations(self) -> Dict[str, Optional[List[Tuple[int, int]]]]:
        unlockable_transformations = self.cafecosmos.indexer.Transformations.get(input=0)
        player_land = self.cafecosmos.indexer.LandItem.get(landId=self.land_id)
        timestamp = self.cafecosmos.w3.eth.get_block('latest').timestamp

        coordinates = []
        closest_unlock_time = None

        for item in player_land:
            item_id = str(item["itemid"])

            # Find the matching transformation
            matching_transformation = next(
                (transformation for transformation in unlockable_transformations if transformation.get('base') == item_id),
                None
            )

            if matching_transformation:
                unlocktime = int(matching_transformation.get('unlocktime', 0))
                placementtime = int(item.get('placementtime', 0))
                total_unlock_time = unlocktime + placementtime

                # Adjust unlock logic to add a safety margin
                if total_unlock_time <= timestamp:
                    # Add to unlockable coordinates
                    coordinates.append((int(item['x']), int(item['y'])))
                else:
                    # Track the closest future unlock time
                    if closest_unlock_time is None or total_unlock_time < closest_unlock_time:
                        closest_unlock_time = total_unlock_time

        return {
            "coordinates": coordinates,
            "nextUnlock": closest_unlock_time
        }
    
    def unlock_all(self):
        unlock_data = self.get_unlockable_transformations()
        coordinates = unlock_data['coordinates']
        failed_items = []

        for coord in coordinates:
            try:
                # Ensure a recheck of the unlock condition before unlocking
                unlock_data = self.get_unlockable_transformations()
                if coord not in unlock_data['coordinates']:
                    print(f"Skipping {coord}: Not unlockable anymore.")
                    continue

                self.place_item(coord[0], coord[1], "unlock")
                print(f"Unlocked item at coordinates {coord}")
            except Exception as e:
                print(f"Failed to unlock item at coordinates {coord}: {e}")
                failed_items.append(coord)
        
        # Return failed items for potential retries
        return failed_items

    def auto_farm(self):
        while True:
            unlock_data = self.get_unlockable_transformations()
            coordinates = unlock_data["coordinates"]
            next_unlock_time = unlock_data["nextUnlock"]

            if coordinates:
                print(f"Unlocking {len(coordinates)} items...")
                failed_items = self.unlock_all()

                # Retry failed items if needed
                if failed_items:
                    print(f"Retrying {len(failed_items)} failed items...")
                    for coord in failed_items:
                        try:
                            # Recheck unlock condition before retry
                            unlock_data = self.get_unlockable_transformations()
                            if coord not in unlock_data['coordinates']:
                                print(f"Skipping retry for {coord}: Not unlockable anymore.")
                                continue

                            self.place_item(coord[0], coord[1], "unlock")
                            print(f"Retried and unlocked item at coordinates {coord}")
                        except Exception as e:
                            print(f"Retry failed for item at coordinates {coord}: {e}")
            
            if next_unlock_time:
                # Wait until the next unlock time with a small buffer
                wait_time = max(0, next_unlock_time - time.time() + 1)  # Add a 1-second safety margin
                print(f"Waiting {wait_time:.2f} seconds for the next unlock...")
                time.sleep(wait_time)
            else:
                # No unlock time available, wait a default interval
                print("No unlockable items. Retrying in 30 seconds...")
                time.sleep(30)
                
### Helper functions ###

def display_land(world: World, land_id: int):
    # 1) Get the land as a DataFrame
    df = get_land(world, land_id)

    # 2) Load items.csv and build ID → Name and Name → ID dictionaries
    items_df = get_items()
    id_to_property = dict(zip(items_df["ID"], items_df["Name"]))
    property_to_id = {v: k for k, v in id_to_property.items()}

    # 3) Build the list of icon “base names” (filenames without .png)
    icon_files = os.listdir(prefix)
    icon_bases = [os.path.splitext(filename)[0] for filename in icon_files]

    # 4) Get coordinates for each cell
    def format_cell(val, x, y, z):
        # Replace with icon path if possible
        icon_path = _replace_with_icons(val, id_to_property, icon_bases)
        # Get the corresponding item ID and name for the tooltip
        item_id = val if isinstance(val, (int, float)) else None
        item_name = id_to_property.get(item_id, "Unknown")
        coordinates = (x, y)
        # Return the HTML with the tooltip
        return path_to_image_html(icon_path, item_id, item_name, coordinates)

    # Apply the formatter to the DataFrame
    df_display = df.copy()
    for index, row in df.iterrows():
        for col in df.columns:
            x, y, z = col, index, 0  # Assuming x = column, y = row, and z = 0 (if not provided)
            df_display.at[index, col] = format_cell(df.at[index, col], x, y, z)

    # 5) Convert to HTML, making sure to disable HTML-escaping
    html = df_display.to_html(escape=False)

    # 6) Display inline in Jupyter (or return/print as needed)
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

def path_to_image_html(path, item_id=None, item_name=None, coordinates=None):
    """
    Converts a cell value into an HTML <img> tag with a tooltip showing the item ID, name, and coordinates.

    Args:
        path (str): Path to the image file.
        item_id (int, optional): The item ID to include in the tooltip.
        item_name (str, optional): The name of the item to include in the tooltip.
        coordinates (tuple, optional): The (x, y, z) coordinates of the item.

    Returns:
        str: An HTML <img> tag with a tooltip if it's an image path; otherwise, the original value.
    """
    if isinstance(path, str) and path.endswith(".png"):
        tooltip_parts = []
        if item_name:
            tooltip_parts.append(f"Name: {item_name}")
        if item_id:
            tooltip_parts.append(f"Item ID: {item_id}")
        if coordinates:
            tooltip_parts.append(f"Coordinates: {coordinates}")
        tooltip = " | ".join(tooltip_parts) if tooltip_parts else "Unknown Item"
        return f'<img src="{path}" title="{tooltip}" width="50"/>'
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

        if(player.cafecosmos.block_explorer_url is not None):
            print(f"Transaction sent: {player.cafecosmos.block_explorer_url}/tx/0x{txn_hash.hex()}")
            receipt = player.cafecosmos.w3.eth.wait_for_transaction_receipt(txn_hash, timeout=120)
            print(f"Transaction confirmed in block: {receipt['blockNumber']}")
        else:
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

def place_item(player: Player, land_id: int, x: int, y: int, item_id: int, display=True):
    """
    Place an item on a land at the specified coordinates.
    """
    # Call the placeItem function in the World contract
    function_call = player.cafecosmos.placeItem(land_id, x, y, item_id, mode="raw")
    _execute_function_call(player=player, function_call=function_call)
    if(display):
        display_land(player.cafecosmos, land_id)

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

# def get_unlockable_transformations(world: World, land_id: int) -> pd.DataFrame:
#     """
#     Determine which transformations can be unlocked based on the player's land inventory.

#     Args:
#         world (World): The world object containing indexers.
#         land_id (int): The ID of the player's land.

#     Returns:
#         pd.DataFrame: A DataFrame of transformations that can be unlocked.
#     """
#     # Fetch land items
#     land_items = world.indexer.LandItem.get(landId=land_id)
#     transformations = world.indexer.Transformations.get()
#     timestamp = world.w3.eth.get_block('latest').timestamp

#     # Count the available items on the land


#     for item in land_items:
#         item_id = int(item["itemid"])
#         if item_id == 0:  # Ignore placeholder or empty items
#             continue
#         if(item)

#     # print("land_inventory", land_inventory)
#     # Determine unlockable transformations
#     unlockable = []
#     for trans in transformations:
#         input_id = int(trans["input"])
#         required_quantity = int(trans.get("yieldquantity", 1))  # Default to 1 if not specified
#         if input_id in land_inventory and land_inventory[input_id] >= required_quantity:
#             unlockable.append({
#                 "Base": int(trans["base"]),
#                 "Input": input_id,
#                 "Next": int(trans["next"]),
#                 "Yield": int(trans["yield"]),
#                 "YieldQuantity": required_quantity,
#                 "UnlockTime": int(trans["unlocktime"]),
#                 "Timeout": int(trans["timeout"]),
#                 "IsRecipe": trans["isrecipe"],
#                 "IsWaterCollection": trans["iswatercollection"],
#                 "XP": int(trans["xp"]),
#                 "Exists": trans["exists"]
#             })

#     # Convert to DataFrame
#     unlockable_df = pd.DataFrame(unlockable)
#     if unlockable_df.empty:
#         print("No transformations can be unlocked.")
#     else:
#         unlockable_df.sort_values(by=["Base", "Input"], inplace=True)

#     return unlockable_df

# def get_time_to_unlock(player: Player) -> pd.DataFrame:
    
    

# def collect_all(player: Player):
#     """
#     Collect all collectable resources from the player's land.
#     """
#     # Call the collectAll function in the World contract
    
#     function_call = player.cafecosmos.collectAll(player.land_id, mode="raw")
#     _execute_function_call(player=player, function_call=function_call)