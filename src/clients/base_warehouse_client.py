from abc import ABC

import requests

from src.utils import get_logger

logger = get_logger(__name__)


class BaseWarehouseClient(ABC):
    """
    Abstract base class for warehouse clients.
    Subclasses should define the warehouse endpoint and
    may override the payload transformation logic if required.
    """

    ENDPOINT: str | None = None
    WAREHOUSE_NAME: str | None = "Generic Warehouse"

    def send_order(self, order):
        """
        Send order payload to the warehouse endpoint.

        Args:
            order (dict): The order data to be sent to the warehouse.
        """
        if not self.ENDPOINT:
            raise NotImplementedError("Warehouse endpoint not defined")

        payload = self._build_payload(order)

        logger.debug(f"Payload for {self.WAREHOUSE_NAME}: {payload}")
        logger.info(f"Sending order {order['id']} to {self.WAREHOUSE_NAME}")

        response = requests.post(self.ENDPOINT, json=payload)
        if response.status_code == 200:
            logger.info(
                f"Order {order['id']} successfully routed to {self.WAREHOUSE_NAME}"
            )
        else:
            logger.error(
                f"Failed to route order {order['id']} to {self.WAREHOUSE_NAME}: {response.text}"
            )

        return response.status_code == 200

    def _build_payload(self, order: dict) -> dict:
        """
        Build the payload to be sent to the warehouse.
        Subclasses can override this method to implement custom payload transformations.

        Args:
            order (dict): The original order data.

        Returns:
            dict: The transformed payload to be sent to the warehouse.
        """
        items = [
            {"sku": edge["node"].get("sku"), "quantity": edge["node"].get("quantity")}
            for edge in order.get("lineItems", {}).get("edges", [])
        ]

        return {
            "order_id": order["id"],
            "items": items,
        }
