# I need asyncio to use async locks and prevent race conditions
import asyncio

from typing import Dict, DefaultDict

# this one helps me build a dict with default values.
from collections import defaultdict

# this is the class that handles logic for packing orders
class PackerAgent:
    
    def __init__(self):
        # stores labels for each order, key = orderId, value = full label payload
        self._labels: Dict[str, Dict] = {}

        # stores wrapped items, key is a tuple (orderId, itemId)
        self._wrapped: Dict[tuple, Dict] = {}

        # I use a lock to make sure multiple tasks don’t mess up shared dicts
        self._lock = asyncio.Lock()

    # this method is called when a label arrives — I save it based on orderId
    async def receive_label(self, payload: Dict):
        async with self._lock:
            self._labels[payload["orderId"]] = payload

    # this one gets called when a wrapped item arrives — I store it using order+item ID
    async def receive_wrapped(self, payload: Dict):
        async with self._lock:
            self._wrapped[(payload["orderId"], payload["itemId"])] = payload

    # this method tries to pack — only succeeds if both label and wrapped item are present
    async def try_pack(self, order_id: str, item_id: str) -> Dict | None:
        async with self._lock:
            # get the saved label and wrapped item if they exist
            label = self._labels.get(order_id)
            wrapped = self._wrapped.get((order_id, item_id))

            # if both exist, we pack and return a confirmation
            if label and wrapped:
                return {
                    "orderId": order_id,
                    "itemId":  item_id,
                    "wrapping": wrapped["wrapping"],  # take wrapping info from payload
                    "label":    label["label"],        # take label info from payload
                    "status":   "packed"               # confirm that it's packed
                }

            # if either one is missing, return nothing
            return None