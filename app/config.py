import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    wallet_address: str = os.getenv("WALLET_ADDRESS", "")
    bscscan_api_key: str = os.getenv("BSCSCAN_API_KEY", "")
    favored_character: str = os.getenv("FAVORED_CHARACTER", "left")
    phantom_vote_interval: int = int(os.getenv("PHANTOM_VOTE_INTERVAL", "300"))
    left_character_name: str = os.getenv("LEFT_CHARACTER_NAME", "Character A")
    right_character_name: str = os.getenv("RIGHT_CHARACTER_NAME", "Character B")
    usdt_amount: float = float(os.getenv("USDT_AMOUNT", "5"))

    usdt_contract: str = "0x55d398326f99059fF775485246999027B3197955"
    bscscan_api_url: str = "https://api.bscscan.com/api"


settings = Settings()
