import os

from dotenv import load_dotenv

from src.clients import EUWarehouseClient, ShopifyClient, USWarehouseClient
from src.services import OrderRouter
from src.utils import get_logger

load_dotenv()  # Load environment variables from .env file
logger = get_logger(__name__)


def main():
    logger.info("Starting Shopify Order Router")

    # Load configuration from environment variables
    shop_url = os.getenv("SHOPIFY_SHOP_URL")
    token = os.getenv("SHOPIFY_ACCESS_TOKEN")

    if not shop_url or not token:
        raise ValueError(
            "Both SHOP_URL and SHOPIFY_ACCESS_TOKEN environment variables must be set."
        )

    shopify_client = ShopifyClient(shop_url, token)

    eu_client = EUWarehouseClient()
    us_client = USWarehouseClient()

    router = OrderRouter(
        {
            "EU": eu_client,
            "US": us_client,
        }
    )

    logger.info("Fetching orders from Shopify")
    for order in shopify_client.get_orders():
        try:
            router.route_order(order)
        except Exception as e:
            logger.error(f"Failed to route order {order['id']}: {e}")

    logger.info("Shopify Order Router finished processing orders")


if __name__ == "__main__":
    main()
