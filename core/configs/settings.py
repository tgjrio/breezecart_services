from openai import OpenAI
from google.cloud import secretmanager
import os
from dotenv import load_dotenv
load_dotenv()

def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """
    # Create the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = client.access_secret_version(name=name)

    # Return the decoded payload
    return response.payload.data.decode("UTF-8")

# Set your project ID (ideally as an environment variable)
PROJECT_ID = os.getenv("PROJECT_ID")


# Retrieve secrets from Secret Manager
OPENAI_API_KEY = access_secret_version(PROJECT_ID, "OPENAI_API_KEY")
REDIS_HOST = access_secret_version(PROJECT_ID, "REDIS_HOST")
REDIS_PORT = access_secret_version(PROJECT_ID, "REDIS_PORT")
REDIS_PASSWORD = access_secret_version(PROJECT_ID, "REDIS_PASSWORD")

# Initialize OpenAI client
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

# Set other constants or secrets if needed
PROCESS_HTML_REQUEST = ""
CHAT_GPT_REQUEST = ""
FACILITATE_REQUEST = ""