# click is used for handling command-line args like --host and --port
import logging, click

# this is the A2A server that runs the agent and exposes it on HTTP
from server.server import A2AServer

# I'm importing the models that describe the agent and its skill/capabilities
from models.agent import AgentCard, AgentCapabilities, AgentSkill

# my actual business logic lives in WrapperAgent
from .agent import WrapperAgent

# task manager handles incoming task requests and routes them to the agent
from .task_manager import WrapperTaskManager

# I want to see logs at INFO level when the agent starts or receives tasks
logging.basicConfig(level=logging.INFO)

# setting up this function as a command-line app
@click.command()
@click.option("--host", default="localhost")  # default host is local machine
@click.option("--port", default=10011)        # port for WrapperAgent
def main(host: str, port: int):
    # defining what this agent is, how others can talk to it, and what it does
    card = AgentCard(
        name="WrapperAgent",  # name shown in discovery
        description="Applies suitable wrapping to items",  # what this agent does
        url=f"http://{host}:{port}/",  # where the agent is hosted
        version="1.0.0",  # version info
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="wrap", name="Wrapping Tool",  # ID and name of the skill
            description="Selects wrapping for an item",  # explains the skill's purpose
            tags=["wrap"], examples=["Wrap fragile vase"]  # tags + sample input so UIs can suggest things
        )]
    )

    # now I start the server and give it the agent + task manager
    A2AServer(
        host=host,
        port=port,
        agent_card=card,
        task_manager=WrapperTaskManager(WrapperAgent())  # connecting logic + task routing
    ).start()

if __name__ == "__main__":
    main()
