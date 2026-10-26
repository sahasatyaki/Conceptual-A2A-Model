# json is used to convert request and response data
import json

# uuid4 helps generate unique task IDs
from uuid import uuid4                                 

# httpx is the async HTTP client I use to talk to agents
import httpx                                

from httpx_sse import connect_sse           

# Any is used in the payload type hints to allow flexibility
from typing import Any                      

# models for sending and getting tasks in JSON-RPC style
from models.request import SendTaskRequest, GetTaskRequest  

# base class for JSON-RPC requests
from models.json_rpc import JSONRPCRequest

# Task model and input params needed when sending a task
from models.task import Task, TaskSendParams

# for initializing the client from a discovered agent card
from models.agent import AgentCard

# custom error if the HTTP response from agent fails
class A2AClientHTTPError(Exception):
    pass

# custom error for when response is not valid JSON
class A2AClientJSONError(Exception):
    pass

# this is the main client class for talking to any A2A agent
class A2AClient:
    def __init__(self, agent_card: AgentCard = None, url: str = None):
        # I programmed so that I can either init with an AgentCard or direct URL
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError("Must provide either agent_card or url")

    # this sends a new task to the agent.
    async def send_task(self, payload: dict[str, Any]) -> Task:
        # wrap the payload using the SendTaskRequest model
        request = SendTaskRequest(
            id=uuid4().hex,  # generate a random ID for this task
            params=TaskSendParams(**payload)  # unpack the payload into the model
        )

        # just printing the request being sent
        print("\n Sending JSON-RPC request:")
        print(json.dumps(request.model_dump(), indent=2))

        # send the request and wait for the reply
        response = await self._send_request(request)

        # convert the result back into a Task object
        return Task(**response["result"])  

    # this method is used to get the status or history of a previous task
    async def get_task(self, payload: dict[str, Any]) -> Task:
        # create the request model with task ID and optional history info
        request = GetTaskRequest(params=payload)

        # send the request and get the response
        response = await self._send_request(request)

        # return the task object from the result
        return Task(**response["result"])

    # this helper method actually sends the HTTP POST request to the agent
    async def _send_request(self, request: JSONRPCRequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                # send the request to the agent’s endpoint
                response = await client.post(
                    self.url,
                    json=request.model_dump(),  # serialize model to JSON
                    timeout=60  # waiting max 60 seconds for response
                )

                # raising error if HTTP response code is not 2xx
                response.raise_for_status()     

                # return the parsed JSON from the response
                return response.json()          

            # if server replied with an error code
            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e

            # if response wasn't valid JSON
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e