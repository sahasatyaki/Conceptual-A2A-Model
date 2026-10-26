# click lets me pass host and port from the command line
import click, logging

# this is the A2A server class that serves the agent on a port
from server.server import A2AServer

# I'm importing models to define metadata about this agent
from models.agent import AgentCard, AgentCapabilities, AgentSkill

# my actual business logic for merchant operations is here
from .agent import MerchantAgent

# this handles the task processing part
from .task_manager import MerchantTaskManager

# I want to see info-level logs printed while testing or running
logging.basicConfig(level=logging.INFO)

# I'm making this a command-line script with host/port flags
@click.command()
@click.option("--host", default="localhost")  # set default host
@click.option("--port", default=10013)        # default port for this agent
def main(host: str, port: int):
    # this creates the agent's metadata so other agents know what it does
    card = AgentCard(
        name="MerchantAgent",  # name used in discovery
        description="Originates purchase orders and orchestrates logistics flow",  # like a brief summary
        url=f"http://{host}:{port}/",  # where this agent will run
        version="1.0.0",  # just a version tag
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="purchase", name="Purchase-Order Handler",  # skill ID and name
            description="Takes a purchase order and returns packed confirmations",  # what it does
            tags=["merchant"], examples=["Handle PO"]  # searchable tags and example prompts
        )]
    )

    # this sets up and runs the server for the MerchantAgent
    A2AServer(
        host=host, port=port, agent_card=card,
        task_manager=MerchantTaskManager(MerchantAgent())  # connects logic + task handling
    ).start()

# makes sure the main() func only runs when I execute this script directly
if __name__ == "__main__":
    main()