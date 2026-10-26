# I use json to decode the incoming messages, and logging to trace stuff
import json, logging

# base task manager class — handles in-memory task storage and locking
from server.task_manager import InMemoryTaskManager

# models for the JSON-RPC requests and responses
from models.request import SendTaskRequest, SendTaskResponse

# task-related stuff like message history, statuses, state labels
from models.task import Message, TextPart, TaskStatus, TaskState

# this is where the actual packing logic is implemented
from .agent import PackerAgent

# setting up logger for this file so I can trace packing steps if needed
logger = logging.getLogger(__name__)

# task manager connects A2A server to the PackerAgent logic
class PackerTaskManager(InMemoryTaskManager):
    
    # constructor that stores reference to the packer agent
    def __init__(self, agent: PackerAgent):
        super().__init__()  # sets up internal task store + lock
        self.agent = agent  # save the agent so I can call its methods later

    # this is called when someone sends a task to the PackerAgent
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        # first I grab the text payload and parse it as JSON
        payload = json.loads(request.params.message.parts[0].text)

        # depending on the payload type, I store either a label or wrapped item
        if "label" in payload:
            await self.agent.receive_label(payload)  # store label under orderId
        elif "wrapping" in payload:
            await self.agent.receive_wrapped(payload)  # store wrapped item with (orderId, itemId)

        # try to pack using whatever is available maybe it succeed or maybe not yet
        packed = await self.agent.try_pack(payload["orderId"],
                                           payload.get("itemId", ""))  # itemId might be missing from label payload

        # either create or update the task record
        task = await self.upsert_task(request.params)

        # if packing succeeded, I return a reply message with the result
        if packed:
            reply = Message(
                role="agent",
                parts=[TextPart(text=json.dumps(packed))]  # wrap packed dict as a text message
            )
            async with self.lock:
                task.status = TaskStatus(state=TaskState.COMPLETED)  # task done
                task.history.append(reply)  # save the agent reply to the history

        else:
            # if packing didn't happen (maybe label or item is still missing)
            async with self.lock:
                task.status = TaskStatus(state=TaskState.WORKING)  # still waiting for the other part

        # always return the task back so that you know like the caller can check if it's done or not
        return SendTaskResponse(id=request.id, result=task)