# using json to parse incoming messages and logging to trace stuff in terminal
import json, logging

# base class that stores tasks in memory and manages locking etc
from server.task_manager import InMemoryTaskManager

# models for handling JSON-RPC style requests and responses
from models.request import SendTaskRequest, SendTaskResponse

# task structure: messages, task state, status etc.
from models.task import Message, TextPart, TaskStatus, TaskState

# this is the actual wrapping logic that selects bubble wrap or paper
from .agent import WrapperAgent

# setup a logger for this file to print out task IDs and status
logger = logging.getLogger(__name__)

# task manager that connects the A2A server to the WrapperAgent logic
class WrapperTaskManager(InMemoryTaskManager):

    # I pass in the agent instance and store it for later use
    def __init__(self, agent: WrapperAgent):
        super().__init__()  # call parent to setup lock + memory
        self.agent = agent  # save agent so I can call invoke on it

    # this is called whenever the wrapper receives a new task to process
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        # log the task ID for my understanding
        logger.info(f"Wrapper received → {request.params.id}")

        # store the task in memory or update it if already exists
        task = await self.upsert_task(request.params)

        # extract the actual payload sent from the user/merchant
        incoming = json.loads(request.params.message.parts[0].text)

        # call the agent to process the item and choose a wrapping
        reply_payload = await self.agent.invoke(incoming)

        # wrap the reply into a proper Message object with agent role
        reply = Message(
            role="agent",
            parts=[TextPart(text=json.dumps(reply_payload))]  # send back as formatted JSON string
        )

        # I am locking before updating the task to avoid concurrency issues
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)  # mark as done
            task.history.append(reply)  # add the reply to the task history

        # return the final result back to the caller
        return SendTaskResponse(id=request.id, result=task)
