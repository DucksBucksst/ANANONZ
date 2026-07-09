import os
import tempfile
import unittest
from gift_satellite_api import GiftSatelliteAPI


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class DummySession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append((url, headers, params, timeout))
        if isinstance(self.responses, dict):
            for key, payload in self.responses.items():
                if key in url:
                    return DummyResponse(payload)
            if "default" in self.responses:
                return DummyResponse(self.responses["default"])
            return DummyResponse([])

        index = len(self.calls) - 1
        if index < len(self.responses):
            payload = self.responses[index]
        else:
            payload = self.responses[-1]
        return DummyResponse(payload)


class GiftSatelliteAPITests(unittest.TestCase):
    def test_floor_by_model(self):
        payload = {
            "items": [
                {"marketplace": "Portals", "normalizedPrice": 5.0, "model": "Alpha"},
                {"marketplace": "Mrkt", "normalizedPrice": 3.5, "model": "Alpha"},
                {"marketplace": "Tonnel", "normalizedPrice": 4.2, "model": "Beta"},
            ]
        }
        api = GiftSatelliteAPI(session=DummySession([payload]))
        result = api.get_floor_by_model("Collection", "Alpha")
        self.assertEqual(str(result), "Floor price: 3.5 gram")
        self.assertEqual(result.data["price"], 3.5)

    def test_floor_by_collection(self):
        payload = {
            "items": [
                {"marketplace": "Portals", "normalizedPrice": 8.0},
                {"marketplace": "Mrkt", "normalizedPrice": 7.0},
                {"marketplace": "Getgems", "normalizedPrice": 6.5},
            ]
        }
        api = GiftSatelliteAPI(session=DummySession([payload]))
        result = api.get_floor_by_collection("Collection")
        self.assertEqual(str(result), "TELEGRAM: 0g | MRKT: 7g | PORTALS: 8g | TONNEL: 0g | GETGEMS: 6.5g")

    def test_floor_by_collection_uses_market_routes_for_output(self):
        history_payload = []
        market_payloads = [
            {"items": [{"marketplace": "telegram", "normalizedPrice": 4.0}]},
            {"items": [{"marketplace": "portals", "normalizedPrice": 3.0}]},
            {"items": [{"marketplace": "mrkt", "normalizedPrice": 2.0}]},
            {"items": [{"marketplace": "tonnel", "normalizedPrice": 1.0}]},
            {"items": [{"marketplace": "getgems", "normalizedPrice": 0.5}]},
        ]
        api = GiftSatelliteAPI(session=DummySession([history_payload, *market_payloads]))
        result = api.get_floor_by_collection("Collection")
        self.assertEqual(str(result), "TELEGRAM: 4g | MRKT: 2g | PORTALS: 3g | TONNEL: 1g | GETGEMS: 0.5g")

    def test_floor_by_collection_prefers_search_results_over_history(self):
        history_payload = [{"collectionName": "Collection", "portals": {"price": 5.32}}]
        search_payload = {"items": [{"marketplace": "portals", "normalizedPrice": 5.74}]}
        api = GiftSatelliteAPI(session=DummySession([history_payload, search_payload]))
        result = api.get_floor_by_collection("Collection")
        self.assertIn("PORTALS: 5.74g", str(result))
        self.assertTrue(str(result).startswith("TELEGRAM: 0g |"))

    def test_listings_grouping(self):
        api = GiftSatelliteAPI(session=DummySession({
            "/search/tg/Collection": {"items": [{"marketplace": "telegram", "normalizedPrice": 1.0, "name": "TG"}]},
            "/search/portals/Collection": {"items": [{"marketplace": "Portals", "normalizedPrice": 2.0, "name": "A"}]},
            "/search/mrkt/Collection": {"items": [{"marketplace": "Mrkt", "normalizedPrice": 3.0, "name": "B"}]},
            "/search/tonnel/Collection": {"items": [{"marketplace": "Tonnel", "normalizedPrice": 4.0, "name": "C"}]},
            "/search/getgems/Collection": {"items": [{"marketplace": "Getgems", "normalizedPrice": 5.0, "name": "D"}]},
        }))
        result = api.get_listings("Collection")
        self.assertIn("Found 5 listings", str(result))
        self.assertIn("Telegram: 1", str(result))
        self.assertIn("Portal: 1", str(result))
        self.assertIn("Mrkt: 1", str(result))
        self.assertIn("Tonnel: 1", str(result))
        self.assertIn("Getgems: 1", str(result))

    def test_listings_scared_cat_azuki_siam(self):
        api = GiftSatelliteAPI(session=DummySession({
            "/search/portals/Scared%20Cat": {
                "items": [
                    {
                        "marketplace": "Portals",
                        "normalizedPrice": 4.5,
                        "model": "Azuki Siam",
                        "slug": "scared-cat-azuki-siam",
                    }
                ]
            },
            "default": {"items": []},
        }))
        result = api.get_listings("Scared Cat", model="Azuki Siam")
        self.assertIn("Found 1 listings", str(result))
        self.assertEqual(result.data["collection"], "Scared Cat")
        self.assertEqual(result.data["model"], "Azuki Siam")
        self.assertEqual(result.data["total"], 1)

    def test_listings_voodoo_doll_disco_doll(self):
        api = GiftSatelliteAPI(session=DummySession({
            "/search/mrkt/Voodoo%20Doll": {
                "items": [
                    {
                        "marketplace": "Mrkt",
                        "normalizedPrice": 3.2,
                        "model": "Disco Doll",
                        "slug": "voodoo-doll-disco-doll",
                    }
                ]
            },
            "default": {"items": []},
        }))
        dto = api.get_listings_dto("Voodoo Doll", model="Disco Doll")
        self.assertEqual(len(dto), 1)
        self.assertEqual(dto[0]["marketplace"], "Mrkt")
        self.assertEqual(dto[0]["price"], 3.2)
        self.assertEqual(dto[0]["slug"], "voodoo-doll-disco-doll")

    def test_reads_token_from_dotenv_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w", encoding="utf-8") as handle:
                handle.write("GIFT_SATELLITE_TOKEN=from-dotenv\n")
            previous_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                api = GiftSatelliteAPI(session=DummySession([{"items": []}]))
            finally:
                os.chdir(previous_cwd)
            self.assertEqual(api.token, "from-dotenv")


if __name__ == "__main__":
    unittest.main()
