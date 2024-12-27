from .World import World
from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

class Player:
    def __init__(self, private_key: str = None, env_key_name: str = None):
        """
        Initialize the Player instance.
        Either `private_key` or `env_key_name` must be provided.

        Args:
            private_key (str): The private key for the player (optional).
            env_key_name (str): The name of the environment variable holding the private key (optional).

        Raises:
            ValueError: If neither `private_key` nor `env_key_name` is provided.
            ValueError: If `env_key_name` is provided but the environment variable is not set.
        """
        if private_key:
            self.private_key = private_key
        elif env_key_name:
            self.private_key = os.getenv(env_key_name)
            if not self.private_key:
                raise ValueError(
                    f"Environment variable '{env_key_name}' is not set or contains an invalid value. "
                    "Please set it in your .env file or provide a private key directly."
                )
        else:
            raise ValueError(
                "Initialization failed: You must provide either a `private_key` or an `env_key_name`. "
                "For example: Player(private_key='0xYourPrivateKey') or Player(env_key_name='PLAYER1')."
            )

        self.private_key = self.private_key if self.private_key.startswith('0x') else '0x' + self.private_key
        self.player_address = self._derive_address(self.private_key)
        self.worlds = {}  # Dictionary to manage multiple worlds

    def add_world(self, world: World, world_name: str):
        """
        Add a world to the player and assign it a dynamic name.

        Args:
            world (World): An instance of the World class.
            world_name (str): The name to assign to the world for dynamic access.
        """
        if not isinstance(world, World):
            raise TypeError("The `world` parameter must be an instance of the World class.")
        self.worlds[world_name] = world
        setattr(self, world_name, world)

    def _derive_address(self, private_key):
        """Derive the Ethereum address from the private key."""
        account = Web3().eth.account.from_key(private_key)
        return account.address
