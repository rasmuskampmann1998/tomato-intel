import os
from dotenv import load_dotenv
from supabase import Client, create_client
from loguru import logger  # Import Loguru logger

# Load environment variables from the .env file
load_dotenv()

# Loguru configuration for logging
logger.add("app.log", level="INFO")  # Log to app.log file with INFO level

# Log that environment variables have been loaded
logger.info("Environment variables loaded from .env file.")

# Retrieve Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Log if environment variables are missing
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials are missing from environment variables.")

# Create and initialize the Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing Supabase client: {e}")
