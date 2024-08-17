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
        "type": "autonomous", 
        "sender": {
            "name": "user_proxy",
            "type": "userproxy",
            "config": {
                "name": "user_proxy",
                "human_input_mode": "NEVER",
                "max_consecutive_auto_reply": 1,
                "system_message": "You are a curious user that only asks questions and follow-up queries.",
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
                "code_execution_config": False,
                "messages": [],
                "allow_repeat_speaker": False
            }
        },
        "receiver": [
            {
                "name": "assistant_team",
                "type": "groupchat",
                "config": {
                    "name": "assistant_team",
                    "human_input_mode": "NEVER",
                    "max_consecutive_auto_reply": 1,
                    "system_message": "You are a team with a scientist, their apprentice, and a salesperson.",
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
                    "agents": [
                        {
                            "name": "scientist",
                            "type": "assistant",
                            "config": {
                                "name": "scientist",
                                "human_input_mode": "NEVER",
                                "max_consecutive_auto_reply": 1,
                                "is_termination_msg": None,
                                "system_message": "You are a knowledgeable scientist who answers concisely and accurately.",
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
                                "code_execution_config": False,
                                "messages": [],
                                "allow_repeat_speaker": False
                            }
                        },
                        {
                            "name": "apprentice",
                            "type": "assistant",
                            "config": {
                                "name": "apprentice",
                                "human_input_mode": "NEVER",
                                "max_consecutive_auto_reply": 1,
                                "is_termination_msg": None,
                                "system_message": "You are the apprentice to a knowledgeable scientist. Supplement answers in a more casual manner.",
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
                                "code_execution_config": False,
                                "messages": [],
                                "allow_repeat_speaker": False
                            }
                        },
                        {
                            "name": "salesperson",
                            "type": "assistant",
                            "config": {
                                "name": "salesperson",
                                "human_input_mode": "NEVER",
                                "max_consecutive_auto_reply": 1,
                                "is_termination_msg": None,
                                "system_message": "You recommend advertisements related to the user's query.",
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
                                "code_execution_config": False,
                                "messages": [],
                                "allow_repeat_speaker": False
                            }
                        }
                    ],
                    "code_execution_config": False,
                    "messages": [],
                    "allow_repeat_speaker": False
                }
            }
        ],
        "agents": [
            {
                "agent": {
                    "name": "user_proxy",
                    "type": "userproxy",
                    "config": {
                        "name": "user_proxy",
                        "human_input_mode": "NEVER",
                        "max_consecutive_auto_reply": 1,
                        "system_message": "You are a curious user that only asks questions and follow-up queries.",
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
                        "code_execution_config": False,
                        "messages": [],
                        "allow_repeat_speaker": False
                    }
                },
                "link": {
                    "agent_type": "sender",
                    "sender_type": "agent"
                }
            },
            {
                "agent": {
                    "name": "assistant_team",
                    "type": "groupchat",
                    "config": {
                        "name": "assistant_team",
                        "human_input_mode": "NEVER",
                        "max_consecutive_auto_reply": 1,
                        "system_message": "You are a team with a scientist, their apprentice, and a salesperson.",
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
                        "code_execution_config": False,
                        "messages": [],
                        "allow_repeat_speaker": False
                    },
                    "agents": [
                        {
                            "name": "scientist",
                            "type": "assistant",
                            "config": {
                                "name": "scientist",
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
                                "code_execution_config": False,
                                "messages": [],
                                "allow_repeat_speaker": False
                            }
                        },
                        {
                            "name": "apprentice",
                            "type": "assistant",
                            "config": {
                                "name": "apprentice",
                                "human_input_mode": "NEVER",
                                "max_consecutive_auto_reply": 1,
                                "system_message": "You are an apprentice to the knowledgeable scientist. You answer questions in a more casual manner.",
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
                                "code_execution_config": False,
                                "messages": [],
                                "allow_repeat_speaker": False
                            }
                        },
                        {
                            "name": "salesperson",
                            "type": "assistant",
                            "config": {
                                "name": "salesperson",
                                "human_input_mode": "NEVER",
                                "max_consecutive_auto_reply": 1,
                                "system_message": "You recommend advertisements related to the user's query.",
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
                                "code_execution_config": False,
                                "messages": [],
                                "allow_repeat_speaker": False
                            }
                        }
                    ]
                },
                "link": {
                    "agent_type": "receiver",
                    "sender_type": "groupchat"
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
