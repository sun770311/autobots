import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal, Callable
from pydantic import BaseModel, field_validator, Field
from pydantic.dataclasses import dataclass
from dataclasses import asdict, field
from enum import Enum

@dataclass
class Message:
    user_id: str
    role: str
    content: str
    root_msg_id: Optional[str] = None
    msg_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    personalize: Optional[bool] = False
    ra: Optional[str] = None
    code: Optional[str] = None
    metadata: Optional[Any] = None
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.msg_id is None:
            self.msg_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def dict(self):
        result = asdict(self)
        result["timestamp"] = result["timestamp"].isoformat()
        return result
    
    def json(self):
        return json.dumps(self.dict())
    
class ModelTypes(str, Enum):
    openai = "openai"
    huggingface = "huggingface"
    custom = "custom"

class Model(BaseModel):
    id: Optional[int] = Field(default_factory=lambda: int(uuid.uuid4().int >> 64))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_type: ModelTypes = ModelTypes.openai
    api_version: Optional[str] = None
    description: Optional[str] = None
    agents: Optional[List[str]] = None  

    class Config:
        arbitrary_types_allowed = True

    def update_timestamp(self):
        self.updated_at = datetime.now()

    def dict(self, **kwargs):
        result = super().model_dump(**kwargs)
        result["created_at"] = self.created_at.isoformat()
        result["updated_at"] = self.updated_at.isoformat()
        return result

@dataclass
class ModelConfig:
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_type: Optional[str] = None
    api_version: Optional[str] = None

@dataclass
class LLMConfig:
    config_list: List[Any] = field(default_factory=List)
    temperature: float = 0
    cache_seed: Optional[Union[int, None]] = None
    timeout: Optional[int] = None

@dataclass
class AgentConfig:
    name: str
    llm_config: Optional[Union[LLMConfig, bool]] = False
    human_input_mode: str = "NEVER"
    max_consecutive_auto_reply: int = 10
    system_message: Optional[str] = None
    is_termination_msg: Optional[Union[bool, str, Callable]] = None
    code_execution_config: Optional[Union[bool, str, Dict[str, Any]]] = None

@dataclass
class AgentFlowSpec:
    type: Literal["assistant", "userproxy", "groupchat"]
    config: AgentConfig = field(default_factory=AgentConfig)

@dataclass
class AgentWorkFlowConfig:
    name: str
    sender: AgentFlowSpec
    receiver: Union[AgentFlowSpec, List[AgentFlowSpec]]
    type: Literal["default", "groupchat", "sequential", "autonomous"] = "default"
    agents: List[Dict[str, Any]] = field(default_factory=list)

    def dict(self):
        return asdict(self)

@dataclass
class Session:
    user_id: str
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    flow_config: AgentWorkFlowConfig = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())

    def dict(self):
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result

@dataclass
class Gallery:
    session: Session
    messages: List[Message]
    tags: List[str]
    id: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.id is None:
            self.id = str(uuid.uuid4())

    def dict(self):
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result

@dataclass
class ChatWebRequestModel:
    message: Message
    flow_config: AgentWorkFlowConfig

@dataclass
class DeleteMessageWebRequestModel:
    user_id: str
    msg_id: str
    session_id: Optional[str] = None

@dataclass
class DBWebRequestModel:
    user_id: str
    msg_id: Optional[str] = None
    session_id: Optional[str] = None
    session: Optional[Session] = None
    skills: Optional[Union[str, List[str]]] = None
    tags: Optional[List[str]] = None

class AgentType(str, Enum):
    assistant = "assistant"
    userproxy = "userproxy"
    groupchat = "groupchat"

class CodeExecutionConfigTypes(str, Enum):
    local = "local"
    docker = "docker"

class Agent(BaseModel):
    name: str
    type: AgentType
    config: Dict[str, Any]
    skills: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("config")
    def validate_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Config must be a dictionary")
        return v

    def model_dump(self, mode: str = "dict", **kwargs) -> Dict[str, Any]:
        data = super().model_dump(**kwargs)
        if mode == "json":
            return json.dumps(data, indent=4)
        return data

@dataclass
class SocketMessage:
    type: str
    data: Dict[str, Any]
    connection_id: str

    def __post_init__(self):
        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")
        
    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "connection_id": self.connection_id
        }
    
    def dict(self) -> Dict[str, Any]:
        return asdict(self)

class WorkFlowSummaryMethod(str, Enum):
    last = "last"
    llm = "llm"
    none = "none"

class WorkFlowType(str, Enum):
    autonomous = "autonomous"
    sequential = "sequential"

class Workflow(BaseModel):
    name: str
    type: WorkFlowType
    summary_method: WorkFlowSummaryMethod = WorkFlowSummaryMethod.last
    agents: List[Dict[str, Any]]

    @field_validator('type', mode='before')
    def validate_workflow_type(cls, v):
        if isinstance(v, str):
            return WorkFlowType(v)
        return v

    @field_validator('summary_method', mode='before')
    def validate_summary_method(cls, v):
        if isinstance(v, str):
            return WorkFlowSummaryMethod(v)
        return v

    def run_workflow(
        self,
        message: str,
        history: Optional[List[Message]] = None,
        connection_id: Optional[str] = None,
        send_message_function: Optional[callable] = None,
        work_dir: Optional[str] = None,
    ) -> Union[Any, Any]:  # Generic typing for managers
        from .workflowmanager import AutoWorkflowManager, SequentialWorkflowManager

        if self.type == WorkFlowType.autonomous:
            manager = AutoWorkflowManager(
                workflow=self.model_dump(),
                history=history,
                work_dir=work_dir,
                send_message_function=send_message_function,
                connection_id=connection_id,
            )
        elif self.type == WorkFlowType.sequential:
            manager = SequentialWorkflowManager(
                workflow=self.model_dump(),
                history=history,
                work_dir=work_dir,
                send_message_function=send_message_function,
                connection_id=connection_id,
            )
        else:
            raise ValueError(f"Unsupported workflow type: {self.type}")

        return manager.run(message=message, history=history)

    def model_dump(self, mode: str = "dict") -> Union[Dict, str]:
        data = super().model_dump()
        if mode == "json":
            return json.dumps(data, indent=4)
        return data
