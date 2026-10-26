# I need json to parse the PO, and logging to print debug info
import json, logging

# using the shared in-memory task manager to track and store task progress
from server.task_manager import InMemoryTaskManager

# request/response models that wrap the task input and output
from models.request import SendTaskRequest, SendTaskResponse

# models for the actual task content (messages, text, status etc)
from models.task import Message, TextPart, TaskStatus, TaskState

# importing the actual agent logic that does the work
from .agent import MerchantAgent

# set up a logger just for this file so I can log POs when they come in
logger = logging.getLogger(__name__)

# this task manager connects the A2A JSON-RPC server to the MerchantAgent logic
class MerchantTaskManager(InMemoryTaskManager):

    # constructor just stores the agent instance and sets up parent
    def __init__(self, agent: MerchantAgent):
        super().__init__()  # setup base memory + lock
        self.agent = agent  # savinge my merchant agent so I can call it in invoke

    # this method gets called when someone sends a PO task to the merchant agent
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        # I print the order ID just to track which PO I'm handling
        logger.info(f"Merchant received PO → {request.params.id}")

        # store or update the task in memory
        task = await self.upsert_task(request.params)

        # grab the PO from the message text I saw it it comes in as raw JSON
        po = json.loads(request.params.message.parts[0].text)

        # now I pass the PO to my agent to process it (label, wrap, pack)
        packed_list = await self.agent.invoke(po)

        # wrap the reply into a message so it can be added to task history
        reply = Message(
            role="agent",  # this message is from the agent (not user)
            parts=[TextPart(text=json.dumps(packed_list, indent=2))]  # I indent it so it's easier to read
        )

        # I use a lock here so nothing else can change this task while I update it
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)  # mark it done
            task.history.append(reply)  # save the agent's reply

        # finally I return a structured JSON-RPC response with the updated task
        return SendTaskResponse(id=request.id, result=task)