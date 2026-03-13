import logging
import os

import requests
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from utils.logger import get_logger

logger = get_logger(__name__)


class ShopifyClient:
    """
    Client responsible for interacting with Shopify Admin GraphQL API.
    """

    def __init__(self, shop_url: str, token: str):
        """
        Initialize Shopify GraphQL client.

        Args:
            shop_url (str): Shopify store URL.
            token (str): Shopify Admin API access token.
        """

        api_version = os.getenv("SHOPIFY_API_VERSION", "2026-01")

        self.endpoint = f"{shop_url}/admin/api/{api_version}/graphql.json"
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": token,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _execute_query(
        self, query: str, variables: dict[str, str | None] | None = None
    ):

        payload = {"query": query, "variables": variables}
        response = requests.post(self.endpoint, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_orders(self):
        query = """
        query GetOrders($cursor: String) {
            orders(first: 10, after: $cursor) {
                edges {
                    node {
                        id
                        name
                        customer {
                            email
                        }
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
                    endCursor
                }
            }
        }
        """
        cursor = None
        while True:
            data = self._execute_query(query, variables={"cursor": cursor})
            edges = data["data"]["orders"]["edges"]

            for edge in edges:
                yield edge["node"]

            if not data["data"]["orders"]["pageInfo"]["hasNextPage"]:
                break

            cursor = data["data"]["orders"]["pageInfo"]["endCursor"]
