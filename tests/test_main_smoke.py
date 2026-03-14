def test_main_smoke(monkeypatch):
    # Set required env vars
    monkeypatch.setenv("SHOPIFY_SHOP_URL", "https://example")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", "token")

    # Patch ShopifyClient to avoid network calls
    class FakeShopify:
        def __init__(self, url, token):
            pass

        def get_orders(self):
            return []

    monkeypatch.setattr("src.main.ShopifyClient", FakeShopify)

    # Patch warehouse clients to avoid network calls
    class FakeClient:
        def __init__(self):
            pass

    monkeypatch.setattr("src.main.EUWarehouseClient", FakeClient)
    monkeypatch.setattr("src.main.USWarehouseClient", FakeClient)

    # Import and run main
    from src import main

    main.main()
