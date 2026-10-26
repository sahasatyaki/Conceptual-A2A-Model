# uuid is used to generate unique task IDs
import uuid                           

# logging helps me track when tasks are sent and received
import logging                        

# A2AClient handles sending tasks to another agent over HTTP
from client.client import A2AClient

# Task model is used to structure the result we get back from agent
from models.task import Task

# set up logger specific to this file/module
logger = logging.getLogger(__name__)

# this class wraps an A2AClient and connects to a remote agent
class AgentConnector:
    
    def __init__(self, name: str, base_url: str):
        # store the name of the agent
        self.name = name
        
        # I am creating a client that talks to the agent's HTTP endpoint
        self.client = A2AClient(url=base_url)
        
        # log that is stating this connector is now ready to be used
        logger.info(f"AgentConnector: initialized for {self.name} at {base_url}")

    # this sends a text message to the agent and waits for a response
    async def send_task(self, message: str, session_id: str) -> Task:
        # create a unique ID for this task
        task_id = uuid.uuid4().hex
        
        # build the task payload in the required format
        payload = {
            "id": task_id,
            "sessionId": session_id,
            "message": {
                "role": "user",  # always from user side
                "parts": [       # wrap the message inside a list of parts
                    {"type": "text", "text": message}
                ]
            }
        }

        # actually send the task and wait for the agent's reply
        task_result = await self.client.send_task(payload)
        
        # log that we got a response from the agent
        logger.info(f"AgentConnector: received response from {self.name} for task {task_id}")
        
        # return the full Task object from the response
        return task_result
