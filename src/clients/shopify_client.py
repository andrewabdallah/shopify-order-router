import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.logger import get_logger

logger = get_logger(__name__)


class ShopifyClient:
    """
    Client responsible for interacting with Shopify Admin GraphQL API.
    """

    API_VERSION = "2026-01"

    def __init__(self, shop_url: str, token: str):
        """
        Initialize Shopify GraphQL client.

        Args:
            shop_url (str): Shopify store URL.
            token (str): Shopify Admin API access token.
        """

        self.shop_url = f"{shop_url}/admin/api/{self.API_VERSION}/graphql.json"
        self.token = token

        @retry(stop=stop_after_attempt(3), wait=wait_exponential())
        def execute_query(query, variables=None):
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.token,
            }
            payload = {"query": query, "variables": variables}
            response = requests.post(self.shop_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

        def get_orders(self):
            query = """
            query GetOrders($cursor: String) {
                orders(first: 10, after: $cursor) {
                    edges {
                        cursor
                        node {
                            id
                            name
                            lineItems(first: 10) {
                                edges {
                                    node {
                                        sku
                                        quantity
                                    }
                                }
                            }
                        }
                    }
                    pageInfo {
                        hasNextPage
                    }
                }
            }
            """
            cursor = None
            orders = []

            while True:
                data = self.execute_query(query, variables={"cursor": cursor})
                edges = data["data"]["orders"]["edges"]

                for edge in edges:
                    orders.append(edge["node"])

                if not data["data"]["orders"]["pageInfo"]["hasNextPage"]:
                    break

                cursor = edges[-1]["cursor"]

            logger.info(f"Fetched {len(orders)} orders from Shopify")

            return orders
