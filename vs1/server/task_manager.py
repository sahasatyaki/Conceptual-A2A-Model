# abstract base class lets me define method signatures that subclasses must implement
from abc import ABC, abstractmethod        

# Dict is used for storing tasks in memory by task ID
from typing import Dict                    

# asyncio is used to make things async and to safely lock access to task storage
import asyncio                             

# importing request and response models for sending/getting tasks
from models.request import (
    SendTaskRequest, SendTaskResponse,    
    GetTaskRequest, GetTaskResponse       
)

# importing task models like Task itself and supporting metadata
from models.task import (
    Task, TaskSendParams, TaskQueryParams,  
    TaskStatus, TaskState, Message          
)

# This is myabstract base class for any task manager
class TaskManager(ABC):
    
    # must be implemented to handle incoming task requests
    @abstractmethod
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        pass

    # must be implemented to handle task status/history requests
    @abstractmethod
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        pass

# in-memory implementation of the TaskManager (just for dev/testing)
class InMemoryTaskManager(TaskManager):
    
    def __init__(self):
        # store tasks in a dict with task ID as key
        self.tasks: Dict[str, Task] = {}   

        # lock makes sure multiple async calls ca ton mess with shared data
        self.lock = asyncio.Lock()         

    # either create a new task or update an existing one with a new message
    async def upsert_task(self, params: TaskSendParams) -> Task:
        async with self.lock:
            # check if task with given ID already exists
            task = self.tasks.get(params.id)  

            if task is None:
                # if not, create a new task with "submitted" status
                task = Task(
                    id=params.id,
                    status=TaskStatus(state=TaskState.SUBMITTED),
                    history=[params.message]
                )
                self.tasks[params.id] = task
            else:
                # if it already exists, just add the new message to history
                task.history.append(params.message)

            return task

    # this is meant to be overridden by specific agents
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        raise NotImplementedError("on_send_task() must be implemented in subclass")

    # handles requests to get task status or history by task ID
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        async with self.lock:
            query: TaskQueryParams = request.params

            # look up the task using the provided ID
            task = self.tasks.get(query.id)

            if not task:
                # if task doesn't exist, return an error response
                return GetTaskResponse(id=request.id, error={"message": "Task not found"})

            # copy the task so we can safely trim history if needed
            task_copy = task.model_copy()  

            if query.historyLength is not None:
                # returning only the last n messages
                task_copy.history = task_copy.history[-query.historyLength:]  
            else:
                # otherwise return the full history
                task_copy.history = task_copy.history

            # return the task with its current state and history
            return GetTaskResponse(id=request.id, result=task_copy)