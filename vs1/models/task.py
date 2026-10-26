# Enum is used to define fixed values like the possible states a task can be in
from enum import Enum                          

# uuid4 is used to generate unique IDs for tasks or sessions
from uuid import uuid4                         

# BaseModel is from Pydantic and lets me define structured data models
# Field is used to customize default values and behavior
from pydantic import BaseModel, Field          

from typing import Any, Literal, List          

# datetime is used for tracking when things happen like status changes
from datetime import datetime                  

# This model represents one "part" of a message. I am only supporting plain text.
class TextPart(BaseModel):
    type: Literal["text"] = "text"  # always text, helps with validation
    text: str  # the actual content of the message

# Alias just in case other types are added and I want to generalize the naming
Part = TextPart

# A full message, which can be from the user or the agent
class Message(BaseModel):
    role: Literal["user", "agent"]  # who sent the message
    parts: List[Part]  # list of parts (text blocks)

# Represents the current status of a task, including a timestamp
class TaskStatus(BaseModel):
    state: str  # state like submitted, completed, etc.
    timestamp: datetime = Field(default_factory=datetime.now)  # when the status was set

# The main task model used across everything in the system
class Task(BaseModel):
    id: str  # unique ID for this task
    status: TaskStatus  # current state + timestamp
    history: List[Message]  # all messages exchanged for this task

# Base parameters for identifying a task, used in several places
class TaskIdParams(BaseModel):
    id: str  # required task ID
    metadata: dict[str, Any] | None = None  # optional extra info

# Extended version of TaskIdParams, adding optional history length
class TaskQueryParams(TaskIdParams):
    historyLength: int | None = None  # how many recent messages I need to return

# Parameters needed to send a new task to an agent
class TaskSendParams(BaseModel):
    id: str  # task ID (usually I generated client-side)
    
    # session groups tasks under one logical interaction
    sessionId: str = Field(default_factory=lambda: uuid4().hex)

    # the message that started the task
    message: Message

    # optionally limit how much of the conversation history to return
    historyLength: int | None = None

    # optional metadata like user role or custom info
    metadata: dict[str, Any] | None = None

# All valid lifecycle states that a task can be in
class TaskState(str, Enum):
    SUBMITTED = "submitted"  # task received but not yet worked on
    WORKING = "working"  # agent is actively processing the task
    INPUT_REQUIRED = "input-required"  # agent is waiting for more input
    COMPLETED = "completed"  # task successfully finished
    CANCELED = "canceled"  # task was intentionally stopped
    FAILED = "failed"  # something went wrong during processing
    UNKNOWN = "unknown"  # fallback state if the real state ist known