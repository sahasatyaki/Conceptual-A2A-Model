# I want to log important events from this script for debugging
import logging

# click is help to build command-line apps; I’ll use it to define host/port options
import click

# This is the core A2A web server that will host the agent and handle requests
from server.server import A2AServer

# I need the data models to describe what this agent can do
from models.agent import AgentCard, AgentCapabilities, AgentSkill

# This is the actual logic behind the agent basicaly how it handles tasks
from .agent import LabelerAgent

# This manages the lifecycle of each task (you know like create/update/complete)
from .task_manager import LabelerTaskManager

# This sets the logging level to show INFO and above (so I can see what’s going on)
logging.basicConfig(level=logging.INFO)

# This defines a CLI command using click. Basicaly me running the script.
@click.command()
@click.option("--host", default="localhost")  # Let me choose which host/IP to bind to (by default I am setting it to localhost)
@click.option("--port", default=10010)        # Let me change the port from CLI if needed
def main(host: str, port: int):
    # I kam declaring what features the agent supports.
    caps = AgentCapabilities(streaming=False)

    # This defines what this agent is capable of doing like creating shipping labels
    skill = AgentSkill(
        id="label",  # Unique skill ID
        name="Shipping Label Generator",  # I am giving a skill name
        description="Creates a shipping label for an address",  # I am providing a 1 liner description of what this agent can do.
        tags=["label", "shipping"],  # Keywords that describe the skill
        examples=["Generate label"]  # Sample command for users
    )

    # This is the public metadata about the agent — other agents can discover this
    card = AgentCard(
        name="LabelerAgent",  # What this agent is called
        description="Generates shipping labels",  # One-line pitch for what it does
        url=f"http://{host}:{port}/",  # The endpoint where it’s hosted
        version="1.0.0",  # Version helps clients know what features to expect
        capabilities=caps,  # Tells others what features I support (streaming, etc.)
        skills=[skill]  # I’m registering the skill I just defined
    )

    # I now instantiate the actual agent that does the work
    agent = LabelerAgent()

    # This will handle incoming tasks and store them in memory
    task_manager = LabelerTaskManager(agent)

    # Finally, I launch the A2A server with the metadata and task manager I just built
    A2AServer(
        host=host,
        port=port,
        agent_card=card,
        task_manager=task_manager
    ).start()  # This blocks and starts the web server

if __name__ == "__main__":
    main()