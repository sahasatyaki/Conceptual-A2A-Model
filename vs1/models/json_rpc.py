# Any = any data type, Literal = restricts allowed values
from typing import Any, Literal               

# uuid4 used to generate unique request IDs
from uuid import uuid4                       

# BaseModel helps define strict data models; Field used to add defaults
from pydantic import BaseModel, Field        

# base class for every JSON-RPC message (used in both requests and responses)
class JSONRPCMessage(BaseModel):
    
    jsonrpc: Literal["2.0"] = "2.0"

    # every message has an ID so requests and responses can be matched
    id: int | str | None = Field(default_factory=lambda: uuid4().hex)

# this I am defining what a request to an agent looks like
class JSONRPCRequest(JSONRPCMessage):
    
    # method name, like "tasks/send" or "tasks/get"
    method: str

    # optional parameters to send with the method (usually I do a dict)
    params: dict[str, Any] | None = None

# this describes an error object that can be sent back in a response
class JSONRPCError(BaseModel):
    
    # numeric error code
    code: int

    # short description of what went wrong
    message: str

    # extra context
    data: Any | None = None

# this is the response from an agent — could be a result or an error
class JSONRPCResponse(JSONRPCMessage):
    
    # the successful result (if no error)
    result: Any | None = None

    # if something went wrong, this will be filled instead of result
    error: JSONRPCError | None = None

# special version of JSONRPCError for when agent crashes or fails unexpectedly
class InternalError(JSONRPCError):
    
    # fixed error code used for internal errors in JSON-RPC
    code: int = -32603

    # default message when something goes wrong inside the agent
    message: str = "Internal error"

    # tracbacks
    data: Any | None = None