# ==================== bot/handlers/__init__.py ====================
# Import all handlers to register them with the bot
from . import commands
from . import callbacks
from . import media

__all__ = ['commands', 'callbacks', 'media']