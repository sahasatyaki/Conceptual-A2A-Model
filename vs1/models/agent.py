# BaseModel lets me create data models with built-in validation
from pydantic import BaseModel

# List is for type hinting lists of things like skills, tags, etc
from typing import List

# this class defines what the agent is capable of doing
class AgentCapabilities(BaseModel):
    
    # if True, the agent can send intermediate streaming results
    streaming: bool = False

    # if True, the agent supports push-based updates (like webhooks)
    pushNotifications: bool = False

    # if True, the agent will keep track of all state transitions.
    stateTransitionHistory: bool = False

# this class describes 1 single skill the agent knows how to do
class AgentSkill(BaseModel):
    
    # unique skill ID like "wrap" or "label"
    id: str

    # human-friendly name for the skill
    name: str

    # optional description to explain what this skill does
    description: str | None = None

    # optional list of tags like "packing", "shipping"
    tags: List[str] | None = None

    # optionalk examples of what kind of input the skill responds to
    examples: List[str] | None = None

    # optional list of input types it supports like "text" or "json"
    inputModes: List[str] | None = None

    # optional list of output formats this skill can return
    outputModes: List[str] | None = None

# this is the full "profile" of the agent — shown in discovery
class AgentCard(BaseModel):
    
    # agent's name (like WrapperAgent, LabelerAgent etc.)
    name: str

    # short description of what this agent does
    description: str

    # the URL where the agent is hosted and reachable
    url: str

    # version of the agent
    version: str

    # capabilities tell other agents what the agent supports (streaming)
    capabilities: AgentCapabilities

    # list of skills this agent provides
    skills: List[AgentSkill]