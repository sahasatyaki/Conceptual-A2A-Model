# used for type annotations and pattern matching for request types
from typing import Annotated, Union, Literal       

# Field lets me customize model fields (like default values or metadata)
from pydantic import Field                         

# TypeAdapter is used to dynamically parse different request types based on "method"
from pydantic.type_adapter import TypeAdapter      

# importing the base JSON-RPC request and response models
from models.json_rpc import JSONRPCRequest, JSONRPCResponse

# importing task-related models for sending and handling tasks
from models.task import Task, TaskSendParams

# this one's used when querying for task history or status
from models.task import TaskQueryParams

# this model is used when a user sends a new task (like wrap item)
class SendTaskRequest(JSONRPCRequest):
    # must be this exact method string for it to match properly
    method: Literal["tasks/send"] = "tasks/send"    

    # the actual payload for the task (includes message, sessionId, etc.)
    params: TaskSendParams                          

# this is used to get status/history of a task that was already sent
class GetTaskRequest(JSONRPCRequest):
    # again, method must be this for my parsing to work correctly
    method: Literal["tasks/get"] = "tasks/get"      

    # params here include task ID and optional historyLength
    params: TaskQueryParams                         

# this lets me automatically parse incoming request based on "method" field
A2ARequest = TypeAdapter(
    Annotated[
        Union[  # supported request types go here
            SendTaskRequest,
            GetTaskRequest,

        ],
        Field(discriminator="method")  # tells pydantic to look at "method" to decide which model to use
    ]
)

# this is the response model sent back when task is successfully accepted/handled
class SendTaskResponse(JSONRPCResponse):
    result: Task | None = None                      

# similar to above, but used when someone queries task status
class GetTaskResponse(JSONRPCResponse):
    result: Task | None = None                      