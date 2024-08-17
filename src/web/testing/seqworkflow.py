import requests
import json
import os

url = "http://127.0.0.1:8081/api/messages"

headers = {
    "Content-Type": "application/json"
}

api_key = os.getenv("OPENAI_API_KEY")

with open("src/web/config.json") as config_file:
    config = json.load(config_file)

default_gallery_id = config.get("default_gallery_id")
default_user_id = config.get("default_user_id")
default_session_id = config.get("default_session_id")
default_user_dir = config.get("default_user_dir")
default_query = config.get("default_query")

data = {
    "message": {
        "user_id": default_user_id,  
        "role": "user",
        "content": default_query,
        "session_id": default_session_id,  
        "user_dir": default_user_dir,
        "gallery_id": default_gallery_id
    },
    "flow_config": {
        "name": "wf1",
        "type": "sequential",  # Could be "sequential" or "autonomous"
        "sender": {  
            "name": "user_proxy",
            "type": "userproxy",
            "config": {
                "name": "user_proxy",
                "type": "userproxy",
                "human_input_mode": "NEVER",
                "max_consecutive_auto_reply": 1,
                "system_message": "You are representing the user in this session.",
                "is_termination_msg": None
            }
        },
        "receiver": [
            {
                "name": "primary_assistant",
                "type": "assistant",
                "config": {
                    "name": "primary_assistant",
                    "type": "assistant",
                    "human_input_mode": "NEVER",
                    "max_consecutive_auto_reply": 1,
                    "system_message": "You are a scientist with lots of general knowledge. Answer the user's questions concisely, ending with `TERMINATE`.",
                    "is_termination_msg": None
                }
            },
            {
                "name": "secondary_assistant",
                "type": "assistant",
                "config": {
                    "name": "secondary_assistant",
                    "type": "assistant",
                    "human_input_mode": "NEVER",
                    "max_consecutive_auto_reply": 2,
                    "system_message": "You are the user's friend. Answer the user's questions in a casual manner, ending with `TERMINATE.`",
                    "is_termination_msg": None
                }
            }
        ],
        "agents": [
            {
                "agent": {
                    "name": "primary_assistant",
                    "type": "assistant",
                    "config": {
                        "name": "primary_assistant",
                        "human_input_mode": "NEVER",
                        "max_consecutive_auto_reply": 1,
                        "system_message": "You are a scientist with lots of general knowledge. Answer the user's questions concisely.",
                        "is_termination_msg": None,
                        "llm_config": {
                            "config_list": [
                                {
                                    "model": "gpt-4",
                                    "api_key": api_key
                                }
                            ],
                            "temperature": 0.7,
                            "cache_seed": None,
                            "timeout": None
                        },
                        "code_execution_config": False
                    }
                },
                "link": {
                    "agent_type": "receiver"
                }
            },
            {
                "agent": {
                    "name": "secondary_assistant",
                    "type": "assistant",
                    "config": {
                        "name": "secondary_assistant",
                        "human_input_mode": "NEVER",
                        "max_consecutive_auto_reply": 2,
                        "system_message": "You are the user's friend. Answer the user's questions in a casual manner.",
                        "is_termination_msg": None,
                        "llm_config": {
                            "config_list": [
                                {
                                    "model": "gpt-4",
                                    "api_key": api_key
                                }
                            ],
                            "temperature": 0.7,
                            "cache_seed": None,
                            "timeout": None
                        },
                        "code_execution_config": False
                    }
                },
                "link": {
                    "agent_type": "receiver"  # Specifies this agent as the receiver
                }
            }
        ]
    }
}

try:
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("Message processed successfully!")
    else:
        print(f"Failed to process message. Status Code: {response.status_code}")
        print("Response JSON:", response.json())

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

print(f"Status Code: {response.status_code}")
print("Response JSON:", response.json())

