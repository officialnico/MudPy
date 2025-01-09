from web3 import Web3
import json
from pathlib import Path
from .MUDIndexerSDK import MUDIndexerSDK

def find_abi_files(root_dir):
    """Recursively find all ABI files"""
    abi_files = []
    root_path = Path(root_dir)
    abi_patterns = ["*.abi.json", "*.json"]
    for pattern in abi_patterns:
        abi_files.extend(root_path.rglob(pattern))
    return abi_files

def load_abis(root_dir) -> dict:
    """Load all ABI files from directory structure"""
    abis = {}
    for abi_file in find_abi_files(root_dir):
        try:
            with open(abi_file, 'r') as f:
                abi_data = json.load(f)
                
            if isinstance(abi_data, dict):
                if 'abi' in abi_data:
                    abi_data = abi_data['abi']
                elif 'contracts' in abi_data:
                    for contract_name, contract_data in abi_data['contracts'].items():
                        if 'abi' in contract_data:
                            abis[contract_name] = contract_data['abi']
                    continue
                
            contract_name = abi_file.parent.name if abi_file.name == 'abi.json' else abi_file.stem.replace('.abi', '')
            abis[contract_name] = abi_data
                
        except Exception as e:
            print(f"Error processing {abi_file}: {e}")
    
    return abis

class World:
    def __init__(self, rpc, world_address, abis_dir, indexer_url=None, mud_config_path=None, block_explorer_url=None):
        """
        Initialize the World instance.

        Args:
            rpc (str): RPC endpoint URL.
            world_address (str): The address of the World contract.
            abis_dir (str): Directory containing ABI files.
            indexer_url (str, optional): URL for the indexer. If provided, initializes the indexer.
            mud_config_path (str, optional): Path to the mud.config.ts file. Required if indexer_url is provided.
        """
        self.rpc = rpc
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self.chain_id = self.w3.eth.chain_id  # Automatically fetch the chain ID
        self.abis = load_abis(abis_dir)
        self.indexer = None
        self.block_explorer_url = block_explorer_url

        # Initialize the contract
        if "IWorld" in self.abis:
            self.contract = self.w3.eth.contract(address=world_address, abi=self.abis["IWorld"])
            self.errors = self._extract_all_errors()

            # Wrap only functions in the ABI
            abi_functions = [item['name'] for item in self.abis["IWorld"] if item['type'] == 'function']
            for func_name in abi_functions:
                original_function = getattr(self.contract.functions, func_name, None)
                if original_function:
                    setattr(self, func_name, self._wrap_function(original_function, func_name))
        else:
            raise Exception("IWorld ABI not found")

        # Automatically set up the indexer if parameters are provided
        if indexer_url and mud_config_path:
            self._initialize_indexer(indexer_url, world_address, mud_config_path)

    def _initialize_indexer(self, indexer_url, world_address, mud_config_path):
        """
        Initialize and set the indexer.

        Args:
            indexer_url (str): URL for the indexer.
            world_address (str): The address of the World contract.
            mud_config_path (str): Path to the mud.config.ts file.
        """

        # Create the indexer
        indexer = MUDIndexerSDK(indexer_url, world_address, mud_config_path)
        self.set_indexer(indexer)

    def set_indexer(self, indexer):
        """
        Set the indexer instance and expose its tables.

        Args:
            indexer (MUDIndexerSDK): The indexer instance.
        """
        self.indexer = indexer

        # Expose tables as attributes directly under world.indexer
        for table_name in indexer.get_table_names():
            table_instance = getattr(indexer.tables, table_name)
            setattr(self.indexer, table_name, table_instance)

    def _extract_all_errors(self):
        errors = {}
        for contract_name, abi in self.abis.items():
            if not isinstance(abi, list):
                continue

            for item in abi:
                if item.get('type') == 'error':
                    signature = f"{item['name']}({','.join(inp['type'] for inp in item.get('inputs', []))})"
                    selector = self.w3.keccak(text=signature)[:4].hex()
                    errors[selector] = (contract_name, item['name'])
        return errors

    def _wrap_function(self, contract_function, func_name):
        def wrapped_function(*args, mode="raw", tx_opts=None, **kwargs):
            """
            mode: "raw" (default), "call", "transact", "estimateGas", "buildTransaction"
            tx_opts: dict for transaction-related options if needed
            """
            fn = contract_function(*args, **kwargs)

            def _parse_error_and_reraise(e):
                """
                Decode custom contract errors and re-raise them with a friendly message.
                """
                error_str = str(e)
                if '0x' in error_str:
                    # Match the full error hex
                    import re
                    hex_match = re.search(r'0x[a-fA-F0-9]{8}', error_str)
                    if hex_match:
                        selector = hex_match.group(0)[2:10]  # Extract selector (first 4 bytes)
                        if selector in self.errors:
                            contract_name, error_name = self.errors[selector]
                            raise ValueError(
                                f"{error_name} error in contract '{contract_name}' when calling '{func_name}' with args={args}."
                            ) from None
                # If no match, re-raise the original error
                raise e

            try:
                if mode == "raw":
                    return fn  # raw function object
                elif mode == "call":
                    return fn.call(tx_opts or {})
                elif mode == "transact":
                    return fn.transact(tx_opts or {})
                elif mode == "estimate_gas":
                    return fn.estimate_gas(tx_opts or {})
                elif mode == "build_transaction":
                    return fn.build_transaction(tx_opts or {})
                else:
                    raise ValueError(f"Unknown mode: {mode}")
            except Exception as e:
                _parse_error_and_reraise(e)

        return wrapped_function


    def add_contract(self, contract_name, address, abi):
        """
        Add a contract to the World instance.

        Args:
            address (str): The address of the contract.
            abi (dict): The ABI of the contract.
        """
        if(not Web3.is_checksum_address(address)):
            address = Web3.to_checksum_address(address)
        contract = Web3(Web3.HTTPProvider(self.rpc)).eth.contract(address=address, abi=abi)
        setattr(self, contract_name, contract)

    