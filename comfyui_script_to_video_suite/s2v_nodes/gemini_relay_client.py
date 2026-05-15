import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
# Make sure it ends with /generate
RELAY_SERVER_URL =  os.getenv("RELAY_SERVER_URL")
CONNECT_TIMEOUT = int(os.getenv("RELAY_CONNECT_TIMEOUT", 100))
READ_TIMEOUT = int(os.getenv("RELAY_READ_TIMEOUT", 600))

def ask_gemini_via_relay(prompt: str) -> str:
    """
    Sends a prompt to our relay server, which then asks the Gemini API.

    Args:
        prompt: The text prompt to send to the model.

    Returns:
        The text response from the model, or an error message string.
    """
    if not RELAY_SERVER_URL:
        return "Error: RELAY_SERVER_URL is not set. Please check your .env file."
    headers = {
        "Content-Type": "application/json"
    }
    payload = { 
        "prompt": prompt
    }
    try:
        response = requests.post(RELAY_SERVER_URL, headers=headers, data=json.dumps(payload), timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))

        if response.status_code == 200:
            # Get the JSON response and return the text part
            return response.json().get("response", "Error: Response JSON was malformed.")
        else:
            error_details = response.json().get("error", "Unknown error from relay server.")
            return f"Error: Relay server responded with status {response.status_code}. Details: {error_details}"

    except requests.exceptions.RequestException as e:
        # Handle network errors (e.g., cannot connect to server)
        return f"Error: Could not connect to the relay server. Reason: {e}"
    
     