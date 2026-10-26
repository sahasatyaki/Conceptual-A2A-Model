# I need uuid to make IDs if needed, asyncio for async stuff, and json to encode/decode data
import uuid, asyncio, json

from typing import Dict, List

# this helps me connect to other A2A agents like Labeler, Packer etc
from utilities.a2a.agent_connect import AgentConnector

# this helps me discover what agents are available by reading the registry file
from utilities.a2a.agent_discovery import DiscoveryClient

# this is the main logic class for the MerchantAgent
class MerchantAgent:
    
    def __init__(self):
        # this will be used to find available agents (like LabelerAgent etc)
        self.discovery = DiscoveryClient()

        # connector cache so we don't build a new connector every time for same agent
        self._connectors: dict[str, AgentConnector] = {}

    # this method helps me fetch (or cache) a connector for a given agent name
    async def _connector(self, agent_name: str) -> AgentConnector:
        # if we already have it cached, use it
        if agent_name not in self._connectors:
            # otherwise discover all agents
            cards = await self.discovery.list_agent_cards()

            # find the one that matches the name
            card  = next(c for c in cards if c.name == agent_name)

            # create and save the connector to that agent
            self._connectors[agent_name] = AgentConnector(agent_name, card.url)

        # return the connector (new or crashed)
        return self._connectors[agent_name]

    # this gets called when someone sends this agent a purchase order
    async def invoke(self, po: Dict) -> List[Dict]:
        
        # get the orderId from the input PO
        order_id = po["orderId"]

        # ---------- 1. Get shipping label from LabelerAgent ----------
        label_conn = await self._connector("LabelerAgent")  # connect to the label agent

        # send a task to generate label based on orderId and address
        label_task = await label_conn.send_task(
            json.dumps({"orderId": order_id, "address": po["address"]}),
            session_id=order_id  # reuse the same session for entire flow
        )

        # decode the response from the Labeler
        label_payload = json.loads(label_task.history[-1].parts[0].text)

        # ---------- 2. Wrap each item using WrapperAgent ----------
        wrapper_conn = await self._connector("WrapperAgent")  # connect to the wrapper

        wrapped_payloads = []  # I'll collect all wrapped items here

        for item in po["items"]:  # loop through each item in the order
            # send the item to wrapper agent
            wrap_task = await wrapper_conn.send_task(
                json.dumps({
                    "orderId": order_id,
                    "itemId":  item["itemId"],
                    "item":    item
                }),
                session_id=order_id
            )

            # decode and add to the list
            wrapped_payloads.append(
                json.loads(wrap_task.history[-1].parts[0].text)
            )

        # ---------- 3. Send wrapped items to PackerAgent ----------
        packer_conn = await self._connector("PackerAgent")  # connect to the packer

        packed_confirmations = []  # collect successful pack results here

        for wrapped in wrapped_payloads:
            # first send the label separately (I mean maybe the packer needs context?)
            await packer_conn.send_task(json.dumps(label_payload), session_id=order_id)

            # now send the wrapped item
            pack_task = await packer_conn.send_task(
                json.dumps(wrapped), session_id=order_id
            )

            # decode the result
            maybe_packed = json.loads(pack_task.history[-1].parts[-1].text)

            # only collect if packing actually succeeded
            if maybe_packed.get("status") == "packed":
                packed_confirmations.append(maybe_packed)

        # finally return all packed confirmations as the result
        return packed_confirmations