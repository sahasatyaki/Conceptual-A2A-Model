# os is used for handling file paths and locating the registry file
import os                            

# json is used to parse the registry file which is just in my case a list of URLs
import json                          

import logging                       

# List is used to type-hint functions that return lists
from typing import List             

# httpx is an async HTTP client I use to send GET requests to agents
import httpx                         

# importing AgentCard which is basically the model that stores agent metadata
from models.agent import AgentCard   

# create a logger just for this file so I can see discovery-related messages
logger = logging.getLogger(__name__)

# this class helps me load agent URLs and fetch their metadata
class DiscoveryClient:
    
    def __init__(self, registry_file: str = None):
        # if a registry file path is given, use that
        if registry_file:
            self.registry_file = registry_file
        else:
            # otherwise look for agent_registry.json in the same folder as this file
            self.registry_file = os.path.join(
                os.path.dirname(__file__),
                "agent_registry.json"
            )

        # load the list of base URLs from the file
        self.base_urls = self._load_registry()

    # internal function that reads and parses the registry JSON file
    def _load_registry(self) -> List[str]:
        try:
            # try opening the file in read mode
            with open(self.registry_file, "r") as f:
                # parse the file contents as JSON
                data = json.load(f)

            # make sure it's a list of URLs, not a dict or something else. Otherwise I have a problem to deal with.
            if not isinstance(data, list):
                raise ValueError("Registry file must contain a JSON list of URLs.")
            return data

        except FileNotFoundError:
            # if the file doesn't exist, just warning and return empty list
            logger.warning(f"Registry file not found: {self.registry_file}")
            return []

        except (json.JSONDecodeError, ValueError) as e:
            # if the JSON is invalid or not a list, log an error and return empty list
            logger.error(f"Error parsing registry file: {e}")
            return []

    # this fetches the actual agent cards by calling each agent's discovery endpoint
    async def list_agent_cards(self) -> List[AgentCard]:
        cards: List[AgentCard] = []  # will store all valid agent cards

        # create a single async HTTP client to reuse for all requests
        async with httpx.AsyncClient() as client:
            # I am going through each base URL in the registry
            for base in self.base_urls:
                # build the discovery endpoint URL
                url = base.rstrip("/") + "/.well-known/agent.json"
                try:
                    # send GET request to the agent's discovery endpoint
                    response = await client.get(url, timeout=5.0)
                    
                    # raise error if status code is not 200
                    response.raise_for_status()
                    
                    # parse the response into an AgentCard object
                    card = AgentCard.model_validate(response.json())
                    
                    # add it to the list of discovered cards
                    cards.append(card)

                except Exception as e:
                    # if any request fails, I log it
                    logger.warning(f"Failed to discover agent at {url}: {e}")
        
        # return all successfully parsed agent cards
        return cards