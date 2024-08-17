# autobots: AutoGen agent workflow design

## 🔁 Steps to Run
1. It is recommended to create a virtual environment using `python -m venv {newenv}`
2. Run `pip install -r requirements.txt`
3. Set `export PYTHONPATH=$(pwd)` (and if needed, `export PATH={which_python_path}`)
4. Set the OPENAI_API_KEY environment variable using `export OPENAI_API_KEY="your_api_key"`, then reload using `source ~/.bashrc`
5. Change configurations in the `src/web/config.json` file as needed
6. Ensure that Docker is installed
7. In one terminal, run `python src/__main__.py`
8. In another terminal, make post requests with test Python scripts in `src/web/testing/`, for example: `python src/web/testing/{test_name}.py`

## 🕵️ AutoGen Agents and Chat Management
### `autogenchat.py`
+ ```python
    class AutoGenChatManager
    ```
    + Handles the automated generation and management of chat interactions.
    + An `AutoGenChatManager` instance is initialized with a message queue that organizes the messages to be sent between assistant agents and the user proxy agent.
    + Initializes workflow managers based on incoming workflow configuration.
    + Outputs a summary of the conversation, including the user's and assistant agents' messages, token cost and usage, as well as the start and end time.
### `datamodel.py`
Provides the foundational data structures to be used by workflow managers and the chat manager. 

+ Dataclasses: used for storing data, such as the `Message`, `Session`, `Gallery`, and `AgentWorkFlowConfig` classes.
+ Pydantic Model Structures: handle data in APIs, applications, and configurations (e.g. `Agent`, `Workflow`).
+ Enum classes: define categories or options a variable can take, like `AgentType`, `CodeExecutionConfigTypes` (locally or via Docker container), and `WorkFlowType`.
+ Additional Functionality: `__post_init__` for additional initialization after the automatic `__init__` method and classes to convert between class instances, JSON, and dictionaries.

### `workflowmanager.py`
#### Autonomous vs. Sequential Workflow
+ `autonomous`: agents operate independently and simultaneously without waiting for other agents to complete their tasks.
+ `sequential`: agents operate in a specific pre-determined order, where each agent waits for the previous one to complete its task.
#### Assistant vs. User Proxy
+ `assistant`: acts as a helper or advisor to **answer queries** and perform tasks input by the user.
+ `userproxy`: acts as a proxy for a human user, responsible for **asking questions**.
#### Group Chat Setting
In the `groupchat` setting, multiple agents can commmunicate with each other aside from the user. The order in which agents answer the query is self-determined.

## 🗄 SQLite Database Operations
Autobots supports user message and session addition, retrieval, and deletion (including database clearing). When `app.py` (the file with API GET and POST endpoints) is run, a `database.sqlite` SQLite database is created with 3 tables: `messages`, `sessions`, and `gallery`. The `messages` table stores one entry for each user query and one entry for each combined assistant(s) response, and each message item is uniquely identified by its `msg_id`. Each message item belongs to a session uniquely identified in the `sessions` table by the `session_id`. A session can be published to the `gallery` table where each gallery item is uniquely identified by its `gallery_id`.

### Database functions (more details in `src/utils/utils.py` and `src/web/app.py`)
+ ```python
    load_messages(user_id: str, session_id: str, dbmanager: DBManager) -> List[Message]:
  ```
    + Load messages from the database for a given user and session specified by their IDs.
    + Used when retrieving user history or publishing a session to the gallery database.


+ ```python
    save_message(message: Message, dbmanager: DBManager) -> None:
    ```
    + Save a message to the database.
    + Used when adding a message to the database.


+ ```python
    delete_message(user_id: str, msg_id: Optional[str], session_id: Optional[str], dbmanager: DBManager, delete_all: bool) -> []:
    ```
    + Delete a message from the database. `delete_all` is set to True when clearing all messages belonging to a session.
    + Used when deleting an individual message or clearing the database.


+ ```python
    get_sessions(user_id: str, dbmanager: DBManager) -> List[Session]:
    ```
    + Retrieve all sessions for a given user from the database.
    + Used when creating a session, retrieving a session, or clearing the database.


+ ```python
    create_session(user_id: str, session: Session, dbmanager: DBManager) -> List[Session]:
    ```
    + Create a new user session in the database.


+ ```python
    delete_user_sessions(user_id: str, session_id: str, dbmanager: DBManager) -> List[Session]:
    ```
    + Delete a specific session from the database. 
    + Used when clearing the database.


+ ```python
    publish_session(session: Session, tags: Optional[List[str]], dbmanager: DBManager) -> Gallery:
    ```
    + Publish a user's session to the gallery.


+ ```python
    get_gallery(gallery_id: Optional[str], dbmanager: DBManager) -> List[Gallery]:
    ```
    + Retrieve gallery items from the database.

## 🧪 Testing
See the `src/web/testing/` folder to run API endpoint tests. Workflow configurations are outlined in the test files.

## 🚶‍♂️ Next Steps
One area to explore is adding skills to agents in order to enable external tool usage. More database functions, such as more gallery operations, can be added to existing utilities.

## 💡 References
Many thanks to [AutoGen](https://github.com/microsoft/autogen) for providing the framework.


