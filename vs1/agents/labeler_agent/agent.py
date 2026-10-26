# need to generate current timestamp for the label
from datetime import datetime

# I am giving a indication since mypayload is be a dictionary.
from typing import Dict

# This is my agent class, handles the label generating logic
class LabelerAgent:

    # These are the types of inputs my agent can deal with (basically plain text or json)
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "application/json"]

    # This function gets called when someone sends the agent a task
    async def invoke(self, payload: Dict) -> Dict:
        # I grab the orderId from the payload json
        order_id = payload["orderId"]

        # Same, I get the address to return it back along with the label
        address  = payload["address"]

        # here i am building the label using order id and timestamp
        label    = f"LABEL-{order_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # finally I return everything in a dict (order, address, generated label)
        return {
            "orderId": order_id,
            "address": address,
            "label":   label
        }
