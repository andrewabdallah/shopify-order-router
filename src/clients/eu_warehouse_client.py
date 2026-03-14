from src.clients import BaseWarehouseClient


class EUWarehouseClient(BaseWarehouseClient):
    """
    Client responsible for sending orders to the EU warehouse for fulfillment.
    """

    ENDPOINT = "https://developer.shipbob.com/api/channels/get-channels"
    WAREHOUSE_NAME = "EU Warehouse"
