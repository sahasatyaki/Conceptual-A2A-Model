# I'm using logging to print stuff like task ids and also json cause payloads come in as text
import logging, json, asyncio

# importing the in-memory task manager which handles storing tasks
from server.task_manager import InMemoryTaskManager

# request and response models used to handle task messages
from models.request import SendTaskRequest, SendTaskResponse

# task data structures like status and messages
from models.task    import Message, TextPart, TaskStatus, TaskState

# importing my agent class that generates the shipping label
from .agent import LabelerAgent

# setting up a logger for this file
logger = logging.getLogger(__name__)

# This is the main task manager for the labeler agent
class LabelerTaskManager(InMemoryTaskManager):

    # I pass the agent to this so that I can call its invoke function later
    def __init__(self, agent: LabelerAgent):
        super().__init__()  # setting up the base class stuff
        self.agent = agent  # store the agent so I can call it later

    # this gets called whenever a task is sent to the agent
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        # just printing out the task id so I know what request came in
        logger.info(f"Labeler received → {request.params.id}")

        # I either create a new task or update an existing one
        task = await self.upsert_task(request.params)

        # this is the user message, I expect it to be a JSON string so I parse it
        incoming = json.loads(request.params.message.parts[0].text)

        # I call the agent to actually generate the label and get back a dict
        reply_payload = await self.agent.invoke(incoming)

        # now I wrap the response into a Message so it can be added to task history
        reply = Message(
            role="agent",  # reply is coming from the agent
            parts=[TextPart(text=json.dumps(reply_payload))]  # convert dict to json string
        )

        # locking so that no two things modify the task at once
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)  # mark it done
            task.history.append(reply)  # save the agent's reply in task history

        # I return the final response to the caller with the updated task
        return SendTaskResponse(id=request.id, result=task)
