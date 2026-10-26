# click lets me run this from terminal with --host and --port options
import click, logging

# this is the actual web server that runs the agent
from server.server import A2AServer

# models to describe the agent’s name, abilities, and tools/skills
from models.agent import AgentCard, AgentCapabilities, AgentSkill

# this is the class that does the packing logic
from .agent import PackerAgent

# task manager handles incoming task requests for the packer
from .task_manager import PackerTaskManager

# enable info-level logging so I can see when the server starts, etc
logging.basicConfig(level=logging.INFO)

# make this a CLI command so I can start it.
@click.command()
@click.option("--host", default="localhost")  # by default the agent runs on localhost
@click.option("--port", default=10012)        # this is the port number for this agent
def main(host: str, port: int):
    # this block builds the agent’s metadata, so others know what it does
    card = AgentCard(
        name="PackerAgent",  # name used in discovery or UI
        description="Correlates labels & wrapped items, then packs",  # short summary of the agent
        url=f"http://{host}:{port}/",  # base url for others to talk to it
        version="1.0.0",  # just a simple version for info
        capabilities=AgentCapabilities(streaming=False), 
        skills=[AgentSkill(
            id="pack", name="Packing Tool",  # name and ID for this agens main skill
            description="Packs when both label and wrapped item exist",  # what this tool does
            tags=["pack"], examples=["Pack order"]  # searchable tags + sample input
        )]
    )

    # now I create the server using the metadata + the task logic
    A2AServer(
        host=host, port=port, agent_card=card,
        task_manager=PackerTaskManager(PackerAgent())  # this wraps my logic class
    ).start()  # starts the actual web server (runs until stopped)

if __name__ == "__main__":
    main()
