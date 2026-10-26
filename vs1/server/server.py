# Starlette is the web framework I used to create the agent server
from starlette.applications import Starlette            
from starlette.responses import JSONResponse            
from starlette.requests import Request                  

# Importing the agent metadata model
from models.agent import AgentCard                      

# Request model (SendTaskRequest) and the base request type
from models.request import A2ARequest, SendTaskRequest  

# Models for standard JSON-RPC responses and internal error reporting
from models.json_rpc import JSONRPCResponse, InternalError  

# task_manager handles the logic for storing and updating task state
from server import task_manager              

# json is used to log the incoming payload for my debugging
import json                                              

# logging to capture exceptions and info messages
import logging                                            
logger = logging.getLogger(__name__)                     

# datetime is used for custom JSON serialization
from datetime import datetime

# this function helps convert models with datetime into JSON-serializable objects
from fastapi.encoders import jsonable_encoder

# fallback JSON serializer for objects like datetime
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# The main server class that starts and handles incoming agent requests
class A2AServer:
    def __init__(self, host="0.0.0.0", port=5000, agent_card: AgentCard = None, task_manager: task_manager = None):
        # storing the host and port for the server
        self.host = host
        self.port = port

        # storing the agent metadata and the task manager handler
        self.agent_card = agent_card
        self.task_manager = task_manager

        # initializing the Starlette web application
        self.app = Starlette()

        # route to accept task requests via POST to "/"
        self.app.add_route("/", self._handle_request, methods=["POST"])

        # route to serve agent discovery metadata as GET to "/.well-known/agent.json"
        self.app.add_route("/.well-known/agent.json", self._get_agent_card, methods=["GET"])

    # I am starting the server using uvicorn
    def start(self):
        # making sure both metadata and task manager are provided
        if not self.agent_card or not self.task_manager:
            raise ValueError("Agent card and task manager are required")

        # running the server using uvicorn
        import uvicorn
        uvicorn.run(self.app, host=self.host, port=self.port)

    # handler for agent metadata route — used in discovery
    def _get_agent_card(self, request: Request) -> JSONResponse:
        # return the agent card as JSON (excluding any None fields)
        return JSONResponse(self.agent_card.model_dump(exclude_none=True))

    # main request handler that deals with task-related POST requests
    async def _handle_request(self, request: Request):
        try:
            # parse the request JSON body
            body = await request.json()
            print("\n Incoming JSON:", json.dumps(body, indent=2))

            # validating the structure of the JSON-RPC request
            json_rpc = A2ARequest.validate_python(body)

            # if it's a SendTaskRequest, deligatig it to the task manager
            if isinstance(json_rpc, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc)
            else:
                # unknown request type — raise an error
                raise ValueError(f"Unsupported A2A method: {type(json_rpc)}")

            # send the response back as JSON
            return self._create_response(result)

        except Exception as e:
            logger.error(f"Exception: {e}")

            # return a structured error response with HTTP 400
            return JSONResponse(
                JSONRPCResponse(id=None, error=InternalError(message=str(e))).model_dump(),
                status_code=400
            )

    # helper function to convert the result model to a JSON response
    def _create_response(self, result):
        if isinstance(result, JSONRPCResponse):
            # jsonable_encoder handles datetime, UUIDs, etc.
            return JSONResponse(content=jsonable_encoder(result.model_dump(exclude_none=True)))
        else:
            raise ValueError("Invalid response type")