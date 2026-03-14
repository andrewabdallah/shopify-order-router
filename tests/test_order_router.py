from unittest.mock import Mock

from pytest import raises

from src.services import OrderRouter


def test_extract_skus():
    """
    Test that SKUs are correctly extracted from Shopify GraphQL line items.
    """
    router = OrderRouter({})

    line_items = {
        "edges": [
            {"node": {"sku": "EU-123"}},
            {"node": {"sku": "US-456"}},
            {"node": {"sku": "X-789"}},
        ]
    }

    skus = router._extract_skus(line_items["edges"])
    assert skus == ["EU-123", "US-456", "X-789"]


def test_determine_warehouse():
    """
    Test that the correct warehouse is determined based on SKU prefixes.
    """
    router = OrderRouter({})

    # Test EU warehouse determination
    assert router._determine_warehouse(["EU-123", "EU-456"]) == "EU_WAREHOUSE"
    # Test US warehouse determination
    assert router._determine_warehouse(["US-123", "US-456"]) == "US_WAREHOUSE"
    # Test mixed SKUs go to EU
    assert router._determine_warehouse(["EU-123", "US-456"]) == "EU_WAREHOUSE"
    # Test unknown SKU prefix
    assert router._determine_warehouse(["XX-123"]) is None
    # Test empty SKU list
    assert router._determine_warehouse([]) is None


def test_route_to_eu():
    """
    Test that SKUs are correctly extracted and routed to the EU warehouse.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {"id": "ord-1", "lineItems": {"edges": [{"node": {"sku": "EU-123"}}]}}

    router.route_order(order)

    assert eu_client.send_order.call_count == 1
    sent_payload = eu_client.send_order.call_args[0][0]
    assert sent_payload["order_id"] == "ord-1"
    assert sent_payload["skus"] == ["EU-123"]


def test_route_to_us():
    """
    Test that SKUs are correctly extracted and routed to the US warehouse.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {"id": "ord-2", "lineItems": {"edges": [{"node": {"sku": "US-1"}}]}}

    router.route_order(order)

    assert us_client.send_order.call_count == 1
    sent_payload = us_client.send_order.call_args[0][0]
    assert sent_payload["order_id"] == "ord-2"
    assert sent_payload["skus"] == ["US-1"]


def test_mixed_routes_go_to_eu():
    """
    Test that mixed SKUs are correctly routed to the EU warehouse.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {
        "id": "ord-3",
        "lineItems": {"edges": [{"node": {"sku": "EU-1"}}, {"node": {"sku": "US-1"}}]},
    }

    router.route_order(order)

    assert eu_client.send_order.call_count == 1
    assert us_client.send_order.call_count == 0


def test_no_skus_does_not_route():
    """
    Test that orders with no SKUs do not get routed.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {"id": "ord-4", "lineItems": {"edges": []}}

    router.route_order(order)

    assert eu_client.send_order.call_count == 0
    assert us_client.send_order.call_count == 0


def test_null_and_empty_skus_do_not_route():
    eu = Mock()
    us = Mock()
    router = OrderRouter({"EU_WAREHOUSE": eu, "US_WAREHOUSE": us})

    order = {
        "id": "ord-null",
        "lineItems": {"edges": [{"node": {"sku": None}}, {"node": {"sku": ""}}]},
    }
    router.route_order(order)

    assert eu.send_order.call_count == 0
    assert us.send_order.call_count == 0


def test_missing_order_id_raises_keyerror():
    eu = Mock()
    us = Mock()
    router = OrderRouter({"EU_WAREHOUSE": eu, "US_WAREHOUSE": us})

    # Has EU SKU so will attempt to build payload and access order['id']
    order = {"lineItems": {"edges": [{"node": {"sku": "EU-1"}}]}}

    with raises(KeyError):
        router.route_order(order)


def test_missing_client_results_in_no_send():
    """
    Test that orders are not sent if the required client is missing.
    """
    eu_client = Mock()

    # only EU client provided but router will request US for this order
    router = OrderRouter({"EU_WAREHOUSE": eu_client})

    order = {"id": "ord-5", "lineItems": {"edges": [{"node": {"sku": "US-1"}}]}}

    router.route_order(order)

    # EU client should not have been called
    assert eu_client.send_order.call_count == 0


def test_orderrouter_build_payload_includes_customer():
    router = OrderRouter({})

    order = {
        "id": "o1",
        "lineItems": {"edges": [{"node": {"sku": "EU-1", "quantity": 1}}]},
        "customer": {"email": "a@example.com"},
    }

    payload = router._build_payload(order, ["EU-1"])

    assert payload["order_id"] == "o1"
    assert payload["skus"] == ["EU-1"]
    assert payload["customer"]["email"] == "a@example.com"
