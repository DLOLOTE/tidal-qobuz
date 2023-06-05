import logging
from config import Config

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
LOGGER = logging.getLogger(__name__)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
logging.getLogger("Librespot:Session").setLevel(logging.WARNING)
logging.getLogger("Librespot:MercuryClient").setLevel(logging.WARNING)
logging.getLogger("Librespot:TokenProvider").setLevel(logging.WARNING)
logging.getLogger("librespot.audio").setLevel(logging.WARNING)
logging.getLogger("Librespot:ApiClient").setLevel(logging.WARNING)
logging.getLogger("pydub").setLevel(logging.WARNING)

bot = Config.BOT_USERNAME

class CMD(object):
    START = ["start", f"start@{bot}"]
    HELP = ["help", f"help@{bot}"]
    # Open Settings Panel
    SETTINGS = ["admin_settings", f"admin_settings@{bot}"]
    DOWNLOAD = ["download", f"download@{bot}"]
    # Auth user or chat to use the bot
    # TODO Add cmd to remove auth
    AUTH = ["auth", f"auth@{bot}"]
    # Add user as admin user
    ADD_ADMIN = ["add_sudo", f"add_sudo@{bot}"]
    # To execute shell cmds
    SHELL = ["shell", f"shell@{bot}"]