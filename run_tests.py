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
        if "/history/collection-offers" in url:
            return DummyResponse({
                "items": [
                    {"marketplace": "Portals", "normalizedPrice": 5.0, "model": "Cyberpunk"},
                    {"marketplace": "Mrkt", "normalizedPrice": 3.5, "model": "Cyberpunk"},
                    {"marketplace": "Getgems", "normalizedPrice": 6.1, "model": "Cyberpunk"},
                    {"marketplace": "Portals", "normalizedPrice": 7.8},
                    {"marketplace": "Mrkt", "normalizedPrice": 7.0},
                ]
            })
        return DummyResponse({
            "items": [
                {"marketplace": "Portals", "name": "Nightstone A"},
                {"marketplace": "mrkt", "name": "Nightstone B"},
                {"marketplace": "tonnel", "name": "Nightstone C"},
            ]
        })


def main():
    api = GiftSatelliteAPI(session=DummySession())

    print("Floor by model:")
    print(api.get_floor_by_model("Heroic Helmet", "Cyberpunk"))
    print()

    print("Floor by collection:")
    print(api.get_floor_by_collection("Nail Bracelet"))
    print()

    print("Listings (case 1):")
    print(api.get_listings("Ion Gem", model="Nightstone"))
    print()

    print("Listings (case 2):")
    print(api.get_listings("Ion Gem"))


if __name__ == "__main__":
    main()
