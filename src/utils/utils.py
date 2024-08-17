import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Union, Any, Optional
import os
import shutil
from pathlib import Path
from .autogenmain.autogen.coding import DockerCommandLineCodeExecutor, LocalCommandLineCodeExecutor
from ..datamodel import AgentConfig, AgentFlowSpec, AgentWorkFlowConfig, LLMConfig, CodeExecutionConfigTypes

from ..datamodel import (
    Message,
    Session,
    Gallery,
    Model
)

from .autogenmain.autogen.oai.client import ModelClient
from .autogenmain.autogen.agentchat.assistant_agent import AssistantAgent as assistAgent

def summarize_chat_history(task: str, messages: List[Dict[str, str]], client: ModelClient):
    """
    Summarize the chat history using the model endpoint and returning the response.
    """

    summarization_system_prompt = f"""
    You are a helpful assistant that is able to review the chat history between a set of agents (userproxy agents, assistants etc) as they try to address a given TASK and provide a summary. Be SUCCINCT but also comprehensive enough to allow others (who cannot see the chat history) understand and recreate the solution.

    The task requested by the user is:
    ===
    {task}
    ===
    The summary should focus on extracting the actual solution to the task from the chat history (assuming the task was addressed) such that any other agent reading the summary will understand what the actual solution is. Use a neutral tone and DO NOT directly mention the agents. Instead only focus on the actions that were carried out (e.g. do not say 'assistant agent generated some code visualization code ..'  instead say say 'visualization code was generated ..'. The answer should be framed as a response to the user task. E.g. if the task is "What is the height of the Eiffel tower", the summary should be "The height of the Eiffel Tower is ...").
    """
    summarization_prompt = [
        {
            "role": "system",
            "content": summarization_system_prompt,
        },
        {
            "role": "user",
            "content": f"Summarize the following chat history. {str(messages)}",
        },
    ]

    response = client.create(messages=summarization_prompt, cache_seed=None)
    return response.choices[0].message.content

def clear_folder(folder_path: str) -> None:
    """
    Clear the contents of a folder.

    :param folder_path: The path to the folder to clear.
    """
    # exit if the folder does not exist
    if not os.path.exists(folder_path):
        return
    # exit if the folder does not exist
    if not os.path.exists(folder_path):
        return
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def find_key_value(data: Union[Dict, List], target_key: str) -> Optional[Any]:
    """
    Recursively searches for a target key in a dictionary or list of dictionaries
    and returns the associated value if found.

    Args:
        data (Union[Dict, List]): The dictionary or list of dictionaries to search.
        target_key (str): The key to search for.

    Returns:
        Optional[Any]: The value associated with the target key if found, else None.
    """
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                result = find_key_value(value, target_key)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = find_key_value(item, target_key)
            if result is not None:
                return result

    return None

def load_code_execution_config(code_execution_type: CodeExecutionConfigTypes, work_dir: str):
    """
    Load the code execution configuration based on the code execution type.

    :param code_execution_type: The code execution type.
    :param work_dir: The working directory to store code execution files.
    :return: The code execution configuration.

    """
    work_dir = Path(work_dir)
    work_dir.mkdir(exist_ok=True)
    executor = None
    if code_execution_type == CodeExecutionConfigTypes.local:
        executor = LocalCommandLineCodeExecutor(work_dir=work_dir)
    elif code_execution_type == CodeExecutionConfigTypes.docker:
        executor = DockerCommandLineCodeExecutor(work_dir=work_dir)
    elif code_execution_type == CodeExecutionConfigTypes.none:
        return False
    else:
        raise ValueError(f"Invalid code execution type: {code_execution_type}")
    code_execution_config = {
        "executor": executor,
    }
    return code_execution_config

def sanitize_model(model: Model):
    """
    Sanitize model dictionary to remove None values and empty strings and only keep valid keys.
    """
    if isinstance(model, Model):
        model = model.model_dump()
    valid_keys = ["model", "base_url", "api_key", "api_type", "api_version"]
    # only add key if value is not None
    sanitized_model = {k: v for k, v in model.items() if (v is not None and v != "") and k in valid_keys}
    return sanitized_model

def get_default_agent_config(work_dir: str, skills_suffix: str = "") -> AgentWorkFlowConfig:
    """
    Get a default agent flow config .
    """

    llm_config = LLMConfig(
        config_list=[{"model": "gpt-4"}],
        temperature=0,
    )

    USER_PROXY_INSTRUCTIONS = """If the request has been addressed sufficiently, summarize the answer and end with the word TERMINATE. Otherwise, ask a follow-up question.
        """

    userproxy_spec = AgentFlowSpec(
        type="userproxy",
        config=AgentConfig(
            name="user_proxy",
            human_input_mode="NEVER",
            system_message=USER_PROXY_INSTRUCTIONS,
            code_execution_config={
                "work_dir": work_dir,
                "use_docker": False,
            },
            max_consecutive_auto_reply=10,
            llm_config=llm_config,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        ),
    )

    assistant_spec = AgentFlowSpec(
        type="assistant",
        config=AgentConfig(
            name="primary_assistant",
            system_message=assistAgent.DEFAULT_SYSTEM_MESSAGE + skills_suffix,
            llm_config=llm_config,
        ),
    )

    flow_config = AgentWorkFlowConfig(
        name="default",
        sender=userproxy_spec,
        receiver=assistant_spec,
        type="default",
    )

    return flow_config

def extract_successful_code_blocks(messages: List[Dict[str, Any]]) -> List[str]:
    """
    Parses through a list of messages containing code blocks and execution statuses,
    returning the content of all messages where the role is 'user'.

    Parameters:
    messages (List[Dict[str, Any]]): A list of message dictionaries containing 'message' and 'role' keys.

    Returns:
    List[str]: A list containing the content of all messages with the role 'user'.
    """
    successful_code_blocks = []

    for i, message in enumerate(messages):
        if message["message"]["role"] == "user":
            successful_code_blocks.append(message["message"]["content"])

    return successful_code_blocks

class DBManager:
    def __init__(self, path: str):
        """
        Initilize the DBManager with the path to the SQLite database.

        path: File path to the SQLite database
        """
        self.path = path
        self.connection = None
    
    def connect(self):
        """Establish a connection to the SQLite database."""
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row # allows us to return rows as dictionaries

    def close(self):
        """Close the connection to the SQLite database."""
        if self.connection:
            self.connection.close()

    def create_tables(self):
        """Create the necessary data tables."""
        self.connect()
        cursor = self.connection.cursor()

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                root_msg_id TEXT,
                msg_id TEXT PRIMARY KEY,
                timestamp TEXT,
                personalize BOOLEAN DEFAULT 0,
                ra TEXT,
                code TEXT,
                metadata TEXT,
                session_id TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
        """)

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT NOT NULL,
                session_id TEXT PRIMARY KEY,
                timestamp TEXT,
                flow_config TEXT
            );
        """)

        # Create gallery table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gallery (
                id TEXT PRIMARY KEY,
                session TEXT NOT NULL,
                messages TEXT NOT NULL,
                tags TEXT,
                timestamp TEXT NOT NULL
            );
        """)

        self.connection.commit()
        self.close()

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        Execute a query and return the results. Performs RETRIEVAL.

        query: The SQL query to execute.
        params: A tuple of parameters to pass to the query.
        return -> A list of rows returned by the query.
        """
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        self.close()
        return results
    
    def execute_commit(self, query: str, params: Tuple = ()) -> None:
        """
        Execute a query that MODIFIES the database (e.g., INSERT, UPDATE, DELETE) and commit the changes.

        query: The SQL query to execute.
        params: A tuple of parameters to pass to the query.
        """
        print(query)
        print(params)
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        self.close()

def load_messages(user_id: str, 
                  session_id: str, 
                  dbmanager: DBManager) -> List[Message]:
    """
    Load messages from the database for a given user and session.

    user_id: The ID of the user whose messages are being loaded.
    session_id: The ID of the session from which messages are being loaded.
    dbmanager: The database manager to interact with the database.
    return -> A list of dictionaries, where each dictionary represents a message.
    """

    # Construct the query to retrieve messages for the given user and session
    query = """
        SELECT user_id, role, content, root_msg_id, msg_id, timestamp, personalize, ra, code, metadata, session_id
        FROM messages
        WHERE user_id = ? AND session_id = ?
        ORDER BY timestamp ASC
    """ # language is in SQL for sqlite3 database

    # Execute the query using dbmanager
    results = dbmanager.execute_query(query, (user_id, session_id)) # execute_query() should be a DBManager instance method

    # Process the results into a list of Message objects
    messages = []
    for row in results:
        message = Message(
            user_id=row["user_id"],
            role=row["role"],
            content=row["content"],
            root_msg_id=row["root_msg_id"] if row["root_msg_id"] else None,
            msg_id=row["msg_id"] if row["msg_id"] else None,
            timestamp=row["timestamp"] if row["timestamp"] else None, # no conversion if saving in isoformat already
            personalize=row["personalize"] if row["personalize"] is not None else False,
            ra=row["ra"] if row["ra"] else None,
            code=row["code"] if row["code"] else None,
            metadata=json.loads(row["metadata"]) if row["metadata"] else None, # no need for further conversion
            session_id=row["session_id"] if row["session_id"] else None,
        )
        messages.append(message)

    return messages

def save_message(message: Message, dbmanager: DBManager) -> None:
    """
    Save a message to the database.

    message: The Message object to save.
    dbmanager: The DBManager instance for database operations.
    return -> None
    """
    # Ensure the timestamp is in ISO format
    if message.timestamp is None:
        timestamp = None
    elif isinstance(message.timestamp, datetime):
        timestamp = message.timestamp.isoformat()
    else:
        timestamp = message.timestamp

    # SQL query to insert a new message into the messages table
    query = """
        INSERT INTO messages (user_id, role, content, root_msg_id, msg_id, timestamp, personalize, ra, code, metadata, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    # Prepare the parameters from the Message object
    params = (
        message.user_id,
        message.role,
        message.content,
        message.root_msg_id if message.root_msg_id else None,
        message.msg_id if message.msg_id else None,
        timestamp,
        message.personalize if message.personalize is not None else False,
        message.ra if message.ra else None,
        message.code if message.code else None,
        json.dumps(message.metadata) if message.metadata else None,
        message.session_id if message.session_id else None,
    )

    dbmanager.execute_commit(query, params)

def delete_message(user_id: str,
                   msg_id: Optional[str],
                   session_id: Optional[str],
                   dbmanager: DBManager,
                   delete_all: bool = False # when not specified, defaults to False
                   ):
    """
    Delete messages from the database.

    user_id: The ID of the user who messages are being deleted.
    msg_id: The ID of the specific message to delete (optional).
    session_id: The ID of the session from which messages are being deleted (optional).
    dbmanager: The DBManager instance for database operations.
    delete_all: If True, delete all messages for the given session_id.
    return -> A list of dictionaries representing the remaining messages.
    """
    # Base query for deletion
    if delete_all:
        # Delete all messages for the user in the given session
        query = "DELETE FROM messages WHERE user_id = ? and session_id = ?"
        params = (user_id, session_id)
    else:
        # Delete a specific message by msg_id within the session
        if not msg_id:
            raise ValueError("msg_id must be provided when delete_all is False")
        
        query = "DELETE FROM messages WHERE user_id = ? AND session_id = ? AND msg_id = ?"
        params = (user_id, session_id, msg_id)

    dbmanager.execute_commit(query, params)

    return []
    # Return remaining messages after deletion (or an empty list if all messages were deleted)
    # return load_messages(user_id=user_id, session_id=session_id, dbmanager=dbmanager)

def get_sessions(user_id: str,
                 dbmanager: DBManager) -> List[Session]:
    """
    Retrieve all sessions for a given user from the database and return them as Session objects.

    user_id: The ID of the user whose sessions are being retrieved.
    dbmanager: The DBManager instance for database operations.
    return -> A list of Session objects.
    """
    # SQL query to select sessions for the given user_id
    query = """
        SELECT user_id, session_id, timestamp, flow_config
        FROM sessions
        WHERE user_id = ?
        ORDER BY timestamp ASC
    """

    # Execute the query
    results = dbmanager.execute_query(query, (user_id,))

    # Process the results into a list of Session objects
    sessions = []
    for row in results:
        flow_config_data=json.loads(row["flow_config"]) if row["flow_config"] else None
        flow_config = None

        if flow_config_data:
            flow_config = AgentWorkFlowConfig(
                name=flow_config_data["name"],
                sender=AgentFlowSpec(
                    type=flow_config_data["sender"]["type"],
                    config=AgentConfig(**flow_config_data["sender"]["config"])
                ),
                receiver=[
                    AgentFlowSpec( # first option: list
                        type=receiver["type"],
                        config=AgentConfig(**receiver["config"])
                    ) for receiver in flow_config_data["receiver"]
                ] if isinstance(flow_config_data["receiver"], list) else
                AgentFlowSpec( # second option: single AgentConfig object
                    type=flow_config_data["receiver"]["type"],
                    config=AgentConfig(**flow_config_data["receiver"]["config"])
                ),
                type=flow_config_data.get("type", "default") # if key not found, set to default
            )

        session = Session(
            user_id = row["user_id"],
            session_id = row["session_id"] if row["session_id"] else None,
            timestamp = row["timestamp"] if row["timestamp"] else None,
            flow_config=flow_config,
        )
        sessions.append(session)

    return sessions

def create_session(user_id: str,
                   session: Session,
                   dbmanager: DBManager) -> List[Session]:
    """
    Create a new user session in the database and return the updated list of sessions for the user.

    user_id: The ID of the user whose session is being created.
    session: The Session object containing session details.
    dbmanager: The database manager to interact with the database.
    return -> A list of Session objects representing all sessions for the user.
    """
    # Convert the session to a dictionary and handle serialization
    session_data = session.dict()

    session_id = session_data["session_id"]
    timestamp = session_data["timestamp"]
    flow_config = json.dumps(session_data["flow_config"]) if session_data["flow_config"] else None

    # SQL query to insert the new session into the database
    query = """
        INSERT INTO sessions (user_id, session_id, timestamp, flow_config)
        VALUES (?, ?, ?, ?)
    """

    params = (user_id, session_id, timestamp, flow_config)

    print(f"Database Path: {dbmanager.path}")

    # Execute the query to insert the new session
    dbmanager.execute_commit(query, params)

    return get_sessions(user_id, dbmanager)

def delete_user_sessions(user_id: str,
                         session_id: str,
                         dbmanager: DBManager) -> List[Session]:
    """
    Delete a specific session from the database.

    user_id: The ID of the user whose session is being deleted.
    session_id: The ID of the specific session to delete.
    dbmanager: The DBManager instance for database operations.
    return -> A list of Session objects representing the deleted session.
    """
    # Retrieve the session that is about to be deleted
    sessions_to_delete = get_sessions(user_id = user_id, dbmanager=dbmanager)
    session_to_delete = [session for session in sessions_to_delete if session.session_id == session_id]

    if not session_to_delete:
        return []
        #raise ValueError(f"No session found with session_id: {session_id} for user_id: {user_id}")
    
    # Delete the session itself
    query = "DELETE FROM sessions WHERE user_id = ? AND session_id = ?"
    params = (user_id, session_id)
    dbmanager.execute_commit(query,params)

    return session_to_delete

def publish_session(session: Session,
                    tags: Optional[List[str]],
                    dbmanager: DBManager) -> Gallery:
    """
    Publish a user's session to the gallery.

    session: The session object to be published.
    tags: A list of tags associated with the session.
    dbmanager: The DBManager instance for database operations.
    return -> A dictionary representing the published gallery item.
    """
    print("HELLO")
    # Load messages associated with the session
    messages = load_messages(session.user_id, session.session_id, dbmanager)

    # Create a Gallery object
    gallery_item = Gallery(
        session=session,
        messages=messages,
        tags=tags or []
    ) # if not provided, generates a unique ID and sets timestamp to current time

    # SQL query to insert the gallery item into the gallery table
    query = """
        INSERT INTO gallery (session, messages, tags, id, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """

    params = (
        json.dumps(gallery_item.session.dict()),
        json.dumps([message.dict() for message in gallery_item.messages]),
        json.dumps(gallery_item.tags) if gallery_item.tags else None,
        gallery_item.id,
        gallery_item.timestamp.isoformat(),
    )

    # Execute the query to insert the gallery item
    dbmanager.execute_commit(query, params)

    return gallery_item

def get_gallery(gallery_id: Optional[str],
                dbmanager: DBManager) -> List[Gallery]:
    """
    Retrieve gallery items from the database and construct a list of Gallery objects.
    
    gallery_id: The ID of the specific gallery item to retrieve.
    dbmanager: The DBManager instance for database operations.
    return -> A list of Gallery objects.
    """
    if gallery_id is None:
        raise ValueError("gallery_id must be provided")
    
    # SQL query to retrieve the gallery item
    query = """
        SELECT session, messages, tags, id, timestamp
        FROM gallery
        WHERE id = ?
    """
    params = (gallery_id,)

    # Execute the query to retrieve the gallery item
    result = dbmanager.execute_query(query, params)

    if not result:
        raise ValueError(f"No gallery item found with id: {gallery_id}")
    
    # Extract the first result (assuming gallery_id is unique)
    row = result[0]

    # Convert JSON strings back to their respective objects
    session_data = json.loads(row["session"])
    session = Session(**session_data)

    messages_data = json.loads(row["messages"])
    messages = [Message(**msg) for msg in messages_data]

    tags = json.loads(row["tags"]) if row["tags"] else []

    # Create and return the Gallery object
    gallery_item = Gallery(
        session=session,
        messages=messages,
        tags=tags,
        id=row["id"],
        timestamp=row["timestamp"],
    )

    return gallery_item