import json
import os
import queue
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..datamodel import (
    ChatWebRequestModel,
    DBWebRequestModel,
    DeleteMessageWebRequestModel,
    Message,
    Session
)
from ..utils import (
    load_messages,
    save_message,
    delete_message,
    get_sessions,
    create_session,
    delete_user_sessions,
    publish_session,
    get_gallery,
    DBManager,
)

from ..autogenchat import AutoGenChatManager


app = FastAPI()

# Allow cross-origin requests for testing on localhost:800* ports only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://localhost:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

root_file_path = os.path.dirname(os.path.abspath(__file__))

api = FastAPI(root_path="/api")
app.mount("/api", api)

db_path = os.path.join(root_file_path, "database.sqlite")
dbmanager = DBManager(path=db_path)
dbmanager.create_tables()  # Create necessary tables in the database if they don't exist

message_queue = queue.Queue()
chatmanager = AutoGenChatManager(message_queue=message_queue)  # Manage calls to autogen

with open("src/web/config.json") as config_file:
    config = json.load(config_file)

default_gallery_id = config.get("default_gallery_id")
default_user_id = config.get("default_user_id")
default_session_id = config.get("default_session_id")
default_connection_id = config.get("default_connection_id")


@api.post("/messages")
async def add_message(req: ChatWebRequestModel):
    """Works as intended (processes a new message and saves records to database)"""
    message = Message(**req.message.dict())
    user_history = load_messages(user_id=message.user_id, session_id=req.message.session_id, dbmanager=dbmanager)

    # Save incoming message to db
    save_message(message=message, dbmanager=dbmanager)

    # Load skills, append to chat
    skills_prompt = """"""

    try:
        work_dir = "work_dir"
        dest_dir = "dest_dir"
        response_message: Message = chatmanager.chat(
            message=message,
            history=user_history,
            work_dir=work_dir,  
            dest_dir=dest_dir,  
            skills_prompt=skills_prompt,
            workflow=req.flow_config.dict(),
            connection_id=default_connection_id
        )

        # Save assistant response to db
        save_message(message=response_message, dbmanager=dbmanager)
        response = {
            "status": True,
            "message": response_message.content,
            "metadata": json.loads(response_message.json()),
        }
        return response
    except Exception as ex_error:
        print(traceback.format_exc())
        return {
            "status": False,
            "message": "Error occurred while processing message: " + str(ex_error),
        }


@api.get("/messages")
def get_messages(user_id: str = None, session_id: str = None):
    """Works as intended (retrieves all messages associated with a user's session)"""
    if user_id is None:
        user_id = default_user_id
    if session_id is None:
        session_id = default_session_id
    try:
        user_history = load_messages(user_id=user_id, session_id=session_id, dbmanager=dbmanager)
        return {
            "status": True,
            "data": user_history,
            "message": "Messages retrieved successfully",
        }
    except Exception as ex_error:
        print(ex_error)
        return {
            "status": False,
            "message": "Error occurred while retrieving messages: " + str(ex_error),
        }


@api.get("/gallery")
def get_gallery_items(gallery_id: str = None):
    """Works as intended."""
    try:
        if gallery_id is None:
            gallery_id = default_gallery_id
        gallery = get_gallery(gallery_id=gallery_id, dbmanager=dbmanager)
        return {
            "status": True,
            "data": gallery,
            "message": "Gallery items retrieved successfully",
        }
    except Exception as ex_error:
        print(ex_error)
        return {
            "status": False,
            "message": "Error occurred while retrieving messages: " + str(ex_error),
        }


@api.get("/sessions")
def get_user_sessions(user_id: str = None):
    """Works as intended. (Return a list of all sessions for a user)"""
    if user_id is None:
        user_id = default_user_id

    try:
        user_sessions = get_sessions(user_id=user_id, dbmanager=dbmanager)
        return {
            "status": True,
            "data": user_sessions,
            "message": "Sessions retrieved successfully",
        }
    except Exception as ex_error:
        print(ex_error)
        return {
            "status": False,
            "message": "Error occurred while retrieving sessions: " + str(ex_error),
        }


@api.post("/sessions")
async def create_user_session(req: DBWebRequestModel):
    """Works as intended (Create a new session for a user)"""
    try:
        session = Session(user_id=req.session.user_id, flow_config=req.session.flow_config)
        user_sessions = create_session(user_id=req.user_id, session=session, dbmanager=dbmanager)
        return {
            "status": True,
            "message": "Session created successfully",
            "data": user_sessions,
        }
    except Exception as ex_error:
        print(ex_error)
        return {
            "status": False,
            "message": "Error occurred while creating session: " + str(ex_error),
        }


@api.post("/sessions/publish")
async def publish_user_session_to_gallery(req: DBWebRequestModel):
    """Works as intended (Create a new gallery for a user)"""
    try:
        session = Session(user_id=req.session.user_id, session_id=req.session.session_id, flow_config=req.session.flow_config)
        gallery_item = publish_session(session, tags=req.tags, dbmanager=dbmanager)
        return {
            "status": True,
            "message": "Session successfully published",
            "data": gallery_item,
        }
    except Exception as ex_error:
        print(traceback.format_exc())
        return {
            "status": False,
            "message": "Error occurred while publishing session: " + str(ex_error),
        }


@api.post("/messages/delete")
async def remove_message(req: DeleteMessageWebRequestModel):
    """Works as intended. (Delete a message from the database)"""
    try:
        messages = delete_message(
            user_id=req.user_id, msg_id=req.msg_id, session_id=req.session_id, dbmanager=dbmanager
        )
        return {
            "status": True,
            "message": "Message deleted successfully",
            "data": messages,
        }
    except Exception as ex_error:
        print(ex_error)
        return {
            "status": False,
            "message": "Error occurred while deleting message: " + str(ex_error),
        }


@api.post("/cleardb")
async def clear_db(req: DBWebRequestModel):
    """Works as intended. (Clear user conversation history database and files)"""
    try:
        delete_message(
            user_id=req.user_id, msg_id=None, session_id=req.session_id, dbmanager=dbmanager, delete_all=True
        )
        sessions = delete_user_sessions(user_id=req.user_id, session_id=req.session_id, dbmanager=dbmanager)
        return {
            "status": True,
            "data": {"sessions": sessions},
            "message": "Messages and files cleared successfully",
        }
    except Exception as ex_error:
        print(ex_error)
        return {
            "status": False,
            "message": "Error occurred while deleting message: " + str(ex_error),
        }


for route in api.routes:
    print(route.path)
