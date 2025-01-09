import os
import numpy as np
import pandas as pd
from thefuzz import process
from IPython.display import HTML

from mud import World, Player

prefix = "./cafecosmos-contracts/icons/"

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
    Display the inventory of a land with icons and quantities in a DataFrame.
    """
    # Fetch inventory data for the land
    inventory = world.indexer.Inventory.get(landId=land_id)

    # Convert inventory data to a DataFrame
    inventory_df = pd.DataFrame(inventory)
    inventory_df["item"] = inventory_df["item"].astype(int)
    inventory_df["quantity"] = inventory_df["quantity"].astype(int)

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
