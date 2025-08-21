from dotenv import load_dotenv
import os

load_dotenv()  # Automatically loads .env file

# TMDB API Keys
TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# OMDB API Keys
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# TRAKT.TV
TRAKT_URL = "https://api.trakt.tv"
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
TRAKT_ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")

# AWS SETUP
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# BEDROCK MODEL SELECTION
BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"