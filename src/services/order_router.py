from typing import Any, Dict, List

from utils import get_logger

logger = get_logger(__name__)


class OrderRouter:
    """
    Routes orders to the appropriate warehouse based on
    the order SKUs prefix rules.
    """

    def __init__(self, warehouse_clients: Dict[str, Any]) -> None:
        """
        Initialize router with warehouse client

        Args:
            warehouse_clients: Dictionary mapping warehouse codes to their respective clients
        """
        self.warehouse_clients = warehouse_clients

    def route_order(self, order: Dict[str, Any]) -> None:
        """
        Determine the appropriate warehouse for the given order.

        Args:
            order: Dictionary containing order details, including 'skus' which is a list of SKU strings
        """
        order_id = order.get("order_id")
        line_items = order.get("lineItems", {}).get("edges", [])
        skus = self._extract_skus(line_items)
        warehouse = self._determine_warehouse(skus)

        if not warehouse:
            logger.error(
                f"Order {order_id} could not be routed due to no valid SKU routing rules."
            )
            return

        logger.info(f"Routing order {order_id} to {warehouse}")

        client = self.warehouse_clients.get(warehouse)
        if not client:
            logger.error(
                f"No client found for warehouse {warehouse}. Order {order_id} cannot be routed."
            )
            return

        payload = self._build_payload(order, skus)
        client.send_order(payload)

    def _extract_skus(self, line_items: List[Dict[str, Any]]) -> List[str]:
        """
        Extract SKUs from shopift GraphQL line items.

        Args:
            line_items: Shopify GraphQL line items edges

        returns:
            List of SKU strings
        """
        skus = []
        for item in line_items:
            sku = item["node"].get("sku")
            if not sku:
                logger.warning(f"Line item {item['node'].get('id')} is missing SKU.")
            else:
                skus.append(sku)
        return skus

    def _determine_warehouse(self, skus: List[str]) -> str | None:
        """
        Determine the warehouse based on SKU prefixes.

        Rules:
        - SKUs starting with "EU-" go to EU Warehouse
        - SKUs starting with "US-" go to US Warehouse
        - Mixed SKUs starting with "EU-" and "US-" go to EU Warehouse
        - Unknow SKU prefiexes or empty SKU list result in no warehouse being assigned

        Args:
            skus: List of SKU strings

        returns:
            Warehouse code string or None if no matching warehouse is found
        """
        if not skus:
            logger.warning("No SKUs provided.")
            return None

        has_eu = any(sku.startswith("EU-") for sku in skus)
        has_us = any(sku.startswith("US-") for sku in skus)

        if has_eu and has_us:
            logger.info(
                f"Order contains mixed SKUs (EU and US). Routing to EU Warehouse. SKUs: {skus}"
            )
            return "EU_WAREHOUSE"

        if has_eu:
            return "EU_WAREHOUSE"

        if has_us:
            return "US_WAREHOUSE"

        logger.warning(f"No matching warehouse found for SKUs: {skus}")
        return None

    def _build_payload(self, order: Dict[str, Any], skus: List[str]) -> Dict[str, Any]:
        """
        Transform the order data into the format expected by the warehouse client.

        Args:
            order: Dictionary containing the original order data.
            skus: List of SKU strings associated with the order.

        Returns:
            Dictionary containing the transformed payload.
        """
        return {
            "order_id": order["id"],
            "skus": skus,
            "customer": order.get("customer", {}),
        }
