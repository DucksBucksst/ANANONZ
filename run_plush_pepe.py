from gift_satellite_api import GiftSatelliteAPI


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class DummySession:
    def __init__(self):
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append((url, headers, params, timeout))
        # history endpoint returns a list of market price entries
        if "/history/collection-offers" in url:
            return DummyResponse([
                {"mrkt": {"normalizedPrice": 2.5}},
                {"portals": {"normalizedPrice": 3.0}},
                {"getgems": {"normalizedPrice": 2.8}},
            ])

        # search endpoints per market
        if "/search/mrkt" in url:
            return DummyResponse({"items": [{"marketplace": "Mrkt", "normalizedPrice": 2.5}]})
        if "/search/portals" in url:
            return DummyResponse({"items": [{"marketplace": "Portals", "normalizedPrice": 3.0}]})
        if "/search/tonnel" in url:
            # no price data from Tonnel in this dummy
            return DummyResponse({"items": [{"marketplace": "Tonnel", "name": "Plush Pepe #1"}]})
        if "/search/getgems" in url:
            return DummyResponse({"items": [{"marketplace": "Getgems", "normalizedPrice": 2.8}]})

        # fallback
        return DummyResponse({"items": []})


def main():
    api = GiftSatelliteAPI(session=DummySession())
    result = api.get_floor_by_collection("Plush Pepe")
    print(result)
    # print structured metadata
    try:
        print(result.data)
    except Exception:
        pass


if __name__ == "__main__":
    main()
