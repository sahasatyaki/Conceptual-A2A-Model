# I use Dict for type hints so it's easier to understand payload structure
from typing import Dict

# this is the main class that decides what wrapping to apply to an item
class WrapperAgent:

    # I only accept JSON input from other agents (not plain text or anything else)
    SUPPORTED_CONTENT_TYPES = ["application/json"]

    # this function gets called when someone sends me an item to wrap
    async def invoke(self, payload: Dict) -> Dict:
        # I grab the item details from the payload
        item = payload["item"]

        # if the item name has the word 'fragile' in it, use bubble-wrap, otherwise just use paper
        wrapping = "bubble-wrap" if "fragile" in item["name"].lower() else "paper"

        # return a new dict with the original info and also the wrapping I selected
        return {
            "orderId":  payload["orderId"],  # keep the order ID from original request
            "itemId":   payload["itemId"],   # also keep the item ID
            "item":     item,                # including full item info back
            "wrapping": wrapping             # this is the wrapping I selected
        }