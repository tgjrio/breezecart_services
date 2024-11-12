from openai import OpenAI
from google.cloud import secretmanager
import os

# Set your project ID (ideally as an environment variable)
PROJECT_ID = os.getenv("PROJECT_ID")
if not PROJECT_ID:
    raise ValueError("The PROJECT_ID environment variable is not set.")

def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Access the payload of the specified secret version.

    Args:
        project_id (str): Google Cloud project ID.
        secret_id (str): ID of the secret in Secret Manager.
        version_id (str): Version number or 'latest'. Defaults to 'latest'.

    Returns:
        str: The secret payload as a string.
    """
    # Create the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = client.access_secret_version(name=name)

    # Return the decoded payload
    return response.payload.data.decode("UTF-8")

# Retrieve secrets from Secret Manager
try:
    OPENAI_API_KEY = access_secret_version(PROJECT_ID, "OPENAI_API_KEY")
    REDIS_HOST = access_secret_version(PROJECT_ID, "REDIS_HOST")
    REDIS_PORT = access_secret_version(PROJECT_ID, "REDIS_PORT")
    REDIS_PASSWORD = access_secret_version(PROJECT_ID, "REDIS_PASSWORD")
except Exception as e:
    raise RuntimeError(f"Failed to access secrets from Secret Manager: {e}")

# Initialize OpenAI client
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

# Set other constants or secrets if needed
PROCESS_HTML_REQUEST = ""
CHAT_GPT_REQUEST = ""
FACILITATE_REQUEST = ""