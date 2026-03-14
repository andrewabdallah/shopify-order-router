from src.clients import BaseWarehouseClient


class USWarehouseClient(BaseWarehouseClient):
    """
    Client responsible for sending orders to the US warehouse for fulfillment.
    """

    ENDPOINT = "https://api.dclcorp.com/"
    WAREHOUSE_NAME = "US Warehouse"
