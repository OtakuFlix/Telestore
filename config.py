# ==================== config.py ====================
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Telegram
    API_ID: int
    API_HASH: str
    BOT_TOKEN: str
    
    # MongoDB
    MONGODB_URI: str
    MONGODB_DB: str
    
    # App
    BASE_APP_URL: str
    PORT: int
    
    # Channel (for updates, announcements)
    CHANNEL_ID: int
    @staticmethod
    def load() -> "Config":
        return Config(
            API_ID=int(os.getenv("API_ID", 25198711)),  # fallback default
            API_HASH=os.getenv("API_HASH", "2a99a1375e26295626c04b4606f72752"),
            BOT_TOKEN=os.getenv("BOT_TOKEN", "7143196160:AAHPSGNx1fisHHL7Nesz57asBf-UovelUPk"),
            CHANNEL_ID=int(os.getenv("CHANNEL_ID", -1002151954601)),
            MONGODB_URI=os.getenv("MONGODB_URI", "mongodb+srv://mhsm:mhsm@cluster0.j9figvh.mongodb.net/?retryWrites=true&w=majority"),
            MONGODB_DB=os.getenv("MONGODB_DB", "tel"),
            BASE_APP_URL=os.getenv("BASE_APP_URL", "http://localhost:8000"),
            PORT=int(os.getenv("PORT", "8000")),
        )

config = Config.load()
