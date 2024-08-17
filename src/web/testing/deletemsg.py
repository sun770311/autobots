import requests
import json
import os

url = "http://127.0.0.1:8081/api/messages/delete"  

with open("src/web/config.json") as config_file:
    config = json.load(config_file)

default_user_id = config.get("default_user_id")

headers = {
    "Content-Type": "application/json"
}

# Define the payload (data to be sent in the POST request)
payload = {
    "user_id": default_user_id,  
    "msg_id": "4ef072cd-f307-47cb-9969-ff643bac4779",  # Replace with the actual message ID you want to delete
    "session_id": "firsttest"  # Replace with the actual session ID
}

# Send the POST request
response = requests.post(url, headers=headers, json=payload)

# Check the response status
if response.status_code == 200:
    data = response.json()
    if data.get("status"):
        print("Message deleted successfully!")
        print("Remaining Messages:", data.get("data"))
    else:
        print("Failed to delete message:", data.get("message"))
else:
    print("Error: Unable to connect to the server. Status Code:", response.status_code)
