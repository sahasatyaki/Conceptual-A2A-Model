# using asyncclick to build a command-line interface that supports async
import asyncclick as click        

# I needed for running async event loop and awaiting the agent response
import asyncio                    

# uuid4 is used to generate unique task/session ids
from uuid import uuid4            

# importing my A2A client that sends requests to the agent
from client.client import A2AClient

# Task model so I can read and parse what the agent sends back
from models.task import Task

# setup the CLI command with options --agent, --session, --history
@click.command()

# this lets me pick which agent URL to connect to (default I am = localhost:10002)
@click.option("--agent", default="http://localhost:10002", help="Base URL of the A2A agent server")

# if session == 0, I’ll generate a fresh ID; otherwise reuse the one provided
@click.option("--session", default=0, help="Session ID (use 0 to generate a new one)")

# if this flag is set, show the whole conversation history after agent replies
@click.option("--history", is_flag=True, help="Print full task history after receiving a response")

# this is the main CLI logic that runs in an async loop
async def cli(agent: str, session: str, history: bool):
    
    # create the A2AClient instance using the URL provided
    client = A2AClient(url=f"{agent}")

    # create or reuse session ID depending on session value
    session_id = uuid4().hex if str(session) == "0" else str(session)

    # I am keeping on asking prompts till user quits
    while True:
        
        # prompt the user to type something
        prompt = click.prompt("\nWhat do you want to send to the agent? (type ':q' or 'quit' to exit)")

        # if user types quit, I exit the loop
        if prompt.strip().lower() in [":q", "quit"]:
            break

        # build the JSON-RPC payload with task ID, session, and message
        payload = {
            "id": uuid4().hex,  # make a new unique ID for this task
            "sessionId": session_id,  # group related messages under same session
            "message": {
                "role": "user",  # this message comes from the user
                "parts": [{"type": "text", "text": prompt}]  # wrap the text input properly
            }
        }

        try:
            # send the message to the agent and wait for reply
            task: Task = await client.send_task(payload)

            # if the response contains messages, print the last one
            if task.history and len(task.history) > 1:
                reply = task.history[-1]  # As last entry in history is usually the reply
                print("\nAgent says:", reply.parts[0].text)  # printing out what agent replied
            else:
                print("\nNo response received.")  # fallback if no reply is there

            # if user passed --history flag, print entire convo
            if history:
                print("\n========= Conversation History =========")
                for msg in task.history:
                    print(f"[{msg.role}] {msg.parts[0].text}")  # show each message with its role (user/agent)

        except Exception as e:
            # if anything crashes (like agent not running), show error trace
            import traceback
            traceback.print_exc()
            
            print(f"\n Error while sending task: {e}")

if __name__ == "__main__":
    
    asyncio.run(cli())