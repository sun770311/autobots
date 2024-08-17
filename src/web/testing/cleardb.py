import requests
import json
import os

url = "http://127.0.0.1:8081/api/cleardb"  

# Configure SQL database-related variables
with open("src/web/config.json") as config_file:
    config = json.load(config_file)

default_user_id = config.get("default_user_id")

headers = {
    "Content-Type": "application/json"
}

# Define the payload (data to be sent in the POST request)
payload = {
    "user_id": default_user_id, 
    "session_id": "firsttest" 
}

# Send the POST request
response = requests.post(url, headers=headers, json=payload)

# Check the response status
if response.status_code == 200:
    data = response.json()
    if data.get("status"):
        print("Deleted successfully!")
        print("Deleted content:", data.get("data"))
    else:
        print("Failed to delete:", data.get("message"))
else:
    print("Error: Unable to connect to the server. Status Code:", response.status_code)
