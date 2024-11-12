from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

REDIS_HOST= os.getenv("REDIS_HOST")
REDIS_PORT= os.getenv("REDIS_PORT")
REDIS_PASSWORD= os.getenv("REDIS_PASSWORD")

PROCESS_HTML_REQUEST = ""
CHAT_GPT_REQUEST = ""
FACILITATE_REQUEST = ""

