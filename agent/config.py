from dotenv import load_dotenv
import os

load_dotenv()  # Automatically loads .env file

# TRAKT.TV
TRAKT_URL = "https://api.trakt.tv"
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
TRAKT_ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")