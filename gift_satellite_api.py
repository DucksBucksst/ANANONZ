import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote


def _load_env_token(env_path: Optional[str] = None) -> Optional[str]:
    if env_path is None:
        env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return None
    try:
        with open(env_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("GIFT_SATELLITE_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - requests may be unavailable in some environments
    requests = None


class FormattedResult(str):
    """String result with structured metadata for easier assertions."""

    def __new__(cls, text: str, **metadata: Any) -> "FormattedResult":
        obj = str.__new__(cls, text)
        obj.metadata = metadata
        return obj

    @property
    def data(self) -> Dict[str, Any]:
        return dict(self.metadata)


class GiftSatelliteAPI:
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None, session: Any = None) -> None:
        self.token = token or os.getenv("GIFT_SATELLITE_TOKEN") or _load_env_token()
        self.base_url = (base_url or os.getenv("GIFT_SATELLITE_BASE_URL") or "https://gift-satellite.dev/api").rstrip("/")
        self.session = session or requests
        self.timeout = 15

    def get_floor_by_model(self, collection: str, model: str) -> FormattedResult:
        prices: List[float] = []
        for market in self._market_routes():
            payload = self._search_listings(collection=collection, model=model, market=market["path"])
            items = self._extract_listings(payload)
            for item in items:
                price = self._extract_price(item)
                if price is not None:
                    prices.append(float(price))
        price = min(prices) if prices else 0
        return FormattedResult(
            f"Floor price: {self._format_price(price)} gram",
            price=price,
            collection=collection,
            model=model,
        )

    def get_floor_by_collection(self, collection: str) -> FormattedResult:
        market_prices: Dict[str, float] = {}

        for market in self._market_routes():
            output_name = market.get("output_name") or self._market_output_name(market["path"])
            payload = self._search_listings(collection=collection, market=market["path"])
            items = self._extract_listings(payload)
            prices = [
                float(self._extract_price(item))
                for item in items
                if self._matches_market_route(item, market["path"]) and self._extract_price(item) is not None
            ]
            if not prices:
                continue
            min_price = min(prices)
            market_prices[output_name] = min_price

        payload = self._request_json("GET", "/history/collection-offers")
        items = self._extract_listings(payload)
        history_prices = self._extract_market_prices_from_history(items, collection)
        if history_prices:
            for market_name, price in history_prices.items():
                if market_name not in market_prices:
                    market_prices[market_name] = price

        result = " | ".join(
            f"{market}: {self._format_price(market_prices.get(market, 0))}g"
            for market in ["TELEGRAM", "MRKT", "PORTALS", "TONNEL", "GETGEMS"]
        )
        return FormattedResult(result, prices=market_prices, collection=collection)

    def get_listings(self, collection: str, model: Optional[str] = None, backdrop: Optional[str] = None) -> FormattedResult:
        structured = self.get_listings_dto(collection=collection, model=model, backdrop=backdrop)
        lines = [f"Found {len(structured)} listings", f"Общее количество листингов: {len(structured)}"]
        counts = {"Telegram": 0, "Portal": 0, "Mrkt": 0, "Tonnel": 0, "Getgems": 0}
        details: Dict[str, List[str]] = {"Telegram": [], "Portal": [], "Mrkt": [], "Tonnel": [], "Getgems": []}
        for item in structured:
            market_name = item["marketplace"]
            if market_name in counts:
                counts[market_name] += 1
                details[market_name].append(f"#{item['number']} = {item['price_text']}")

        for market_name, label in [("Telegram", "Telegram"), ("Portal", "Portal"), ("Mrkt", "Mrkt"), ("Tonnel", "Tonnel"), ("Getgems", "Getgems")]:
            if counts[market_name] == 0:
                lines.append(f"{label}: 0 листинга NONE")
                continue
            lines.append(f"{label}: {counts[market_name]}")
            for detail in details[market_name][:5]:
                lines.append(f"  - {detail}")
            if len(details[market_name]) > 5:
                lines.append(f"  - ... и ещё {len(details[market_name]) - 5} листинг(а)")

        text = "\n".join(lines)
        return FormattedResult(text, total=len(structured), counts=counts, details=details, structured=structured, collection=collection, model=model, backdrop=backdrop)

    def get_listings_dto(self, collection: str, model: Optional[str] = None, backdrop: Optional[str] = None) -> List[Dict[str, Any]]:
        structured: List[Dict[str, Any]] = []
        for market in self._market_routes():
            payload = self._search_listings(collection=collection, model=model, backdrop=backdrop, market=market["path"])
            items = self._extract_listings(payload)
            for item in items:
                if not isinstance(item, dict):
                    continue
                market_name = self._classify_marketplace(item)
                slug = item.get("slug") or item.get("giftId") or "unknown"
                number = item.get("number")
                if number is None:
                    number = slug.split("-")[-1] if isinstance(slug, str) else ""
                price = self._extract_price(item)
                if price is None:
                    price = 0
                stars = None
                for key in ("stars", "star", "starsCount", "stars_count", "starCount", "star_count", "rating"):
                    value = item.get(key)
                    if isinstance(value, (int, float)):
                        stars = int(value)
                        break
                    if isinstance(value, str) and value.isdigit():
                        stars = int(value)
                        break
                structured.append({
                    "marketplace": market_name,
                    "number": number,
                    "price": float(price),
                    "price_text": f"{self._format_price(price)} GRAM",
                    "stars": stars,
                    "slug": slug,
                    "raw": item,
                })
        return structured

    def _search_listings(self, collection: str, model: Optional[str] = None, backdrop: Optional[str] = None, market: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {}
        if model:
            params["models"] = model
        if backdrop:
            params["backdrops"] = backdrop

        candidates = self._collection_query_candidates(collection)
        for candidate in candidates:
            path = f"/search/{market}/{quote(candidate)}" if market else f"/search/{quote(candidate)}"
            payload = self._request_json("GET", path, params=params)
            if self._looks_like_error(payload):
                continue
            if isinstance(payload, list):
                if payload:
                    return payload
                continue
            if isinstance(payload, dict):
                if payload.get("items") or payload.get("results") or payload.get("listings") or payload.get("data") or payload.get("offers") or payload.get("records"):
                    return payload
                if payload.get("message") and payload.get("statusCode") == 400:
                    continue
                return payload
            return payload
        return None

    def _request_json(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        if self.session is None:
            raise RuntimeError("No HTTP session configured")

        url = f"{self.base_url}{path}"
        try:
            method_name = method.lower()
            request_func = getattr(self.session, method_name, None)
            if callable(request_func):
                response = request_func(url, headers=headers, params=params, timeout=self.timeout)
            else:
                response = self.session.request(method.upper(), url, headers=headers, params=params, timeout=self.timeout)
        except Exception:
            return None

        if hasattr(response, "raise_for_status"):
            try:
                response.raise_for_status()
            except Exception:
                return None
        if hasattr(response, "json"):
            try:
                return response.json()
            except Exception:
                return response.text
        return response

    def _extract_prices(self, payload: Any, model: Optional[str] = None) -> List[float]:
        prices: List[float] = []
        for item in self._walk(payload):
            if not self._matches_model(item, model):
                continue
            price = self._extract_price(item)
            if price is not None:
                prices.append(float(price))
        return prices

    def _extract_market_prices_from_history(self, payload: Any, collection: str) -> Dict[str, float]:
        if not isinstance(payload, list):
            return {}

        prices: Dict[str, float] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            if "collectionName" in item:
                if str(item.get("collectionName", "")).lower() != str(collection).lower():
                    continue
                for key, value in item.items():
                    if key == "collectionName":
                        continue
                    if isinstance(value, dict):
                        price = self._extract_price(value)
                        if price is not None:
                            prices[self._market_output_name(key)] = float(price)
                return prices

            price = self._extract_price(item)
            market = self._find_marketplace(item)
            if price is not None and market:
                prices[self._market_output_name(market)] = float(price)
        return prices

    def _extract_listings(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("items", "results", "listings", "data", "offers", "records"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
                if isinstance(value, dict):
                    nested = self._extract_listings(value)
                    if nested:
                        return nested
            return [payload]
        return []

    def _walk(self, value: Any) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        if isinstance(value, dict):
            if self._looks_like_offer(value):
                items.append(value)
            for child in value.values():
                items.extend(self._walk(child))
        elif isinstance(value, list):
            for child in value:
                items.extend(self._walk(child))
        return items

    def _looks_like_offer(self, item: Any) -> bool:
        return isinstance(item, dict) and (
            self._contains_any_key(item, ["normalizedPrice", "floorPrice", "price", "priceGram", "priceInGram", "listingPrice"])
            or self._contains_any_key(item, ["marketplace", "marketplaceName", "market"])
        )

    def _matches_model(self, item: Any, model: Optional[str]) -> bool:
        if not model or not isinstance(item, dict):
            return True
        candidate = str(model).lower()
        for key in ("model", "modelName", "model_name", "name", "tokenName"):
            value = item.get(key)
            if isinstance(value, str) and candidate in value.lower():
                return True
        return False

    def _matches_market_route(self, item: Any, market_path: str) -> bool:
        if not isinstance(item, dict):
            return False
        marketplace = self._find_marketplace(item)
        if not marketplace:
            return False
        normalized = str(marketplace).strip().lower()
        if market_path == "tg":
            return normalized in {"telegram", "tg"}
        if market_path == "portals":
            return normalized in {"portal", "portals"}
        if market_path == "mrkt":
            return normalized in {"mrkt", "market"}
        if market_path == "tonnel":
            return normalized == "tonnel"
        if market_path == "getgems":
            return normalized in {"getgems", "getgem", "get-gems"}
        return False

    def _extract_price(self, item: Any) -> Optional[float]:
        if not isinstance(item, dict):
            return None
        for key in ("normalizedPrice", "floorPrice", "price", "priceGram", "priceInGram", "listingPrice"):
            value = item.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    continue
        for nested in item.values():
            if isinstance(nested, (dict, list)):
                value = self._extract_price(nested)
                if value is not None:
                    return value
        return None

    def _find_marketplace(self, item: Any) -> Optional[str]:
        if not isinstance(item, dict):
            return None
        for key in ("marketplace", "marketplaceName", "market", "market_name"):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
        for nested in item.values():
            if isinstance(nested, (dict, list)):
                result = self._find_marketplace(nested)
                if result:
                    return result
        return None

    def _classify_marketplace(self, item: Any) -> str:
        market = self._find_marketplace(item)
        if not market:
            return "Unknown"
        normalized = str(market).strip().lower()
        if normalized in {"telegram", "tg", "telegrammarket", "tgmarket"}:
            return "Telegram"
        if normalized in {"portal", "portals", "portalsmarket"}:
            return "Portal"
        if normalized in {"mrkt", "market", "mrktmarket"}:
            return "Mrkt"
        if normalized in {"tonnel", "tonnelmarket"}:
            return "Tonnel"
        if normalized in {"getgems", "getgem", "get-gems", "getgemsmarket"}:
            return "Getgems"
        return normalized.capitalize()

    @staticmethod
    def _collection_query_candidates(collection: str) -> List[str]:
        raw = str(collection or "").strip()
        if not raw:
            return []
        candidates: List[str] = [raw]
        lowered = raw.lower()
        candidates.append(lowered)
        candidates.append(raw.replace(" ", "-"))
        candidates.append(raw.replace(" ", "-").lower())
        candidates.append(raw.replace(" ", ""))
        candidates.append(raw.replace(" ", "").lower())
        candidates.append(re.sub(r"\bday\b", "Day", raw))
        candidates.append(re.sub(r"\bday\b", "Day", raw).replace(" ", "-"))
        candidates.append(re.sub(r"\bday\b", "Day", lowered))
        candidates.append(re.sub(r"\bday\b", "Day", lowered).replace(" ", "-"))
        candidates.append(raw.replace("-", " "))
        candidates.append(raw.replace("-", " ").replace("day", "Day"))
        candidates.append(raw.replace("-", " ").replace("day", "Day").replace(" ", "-"))
        slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
        if slug:
            candidates.append(slug)
        compact = re.sub(r"[^a-z0-9]+", "", lowered)
        if compact:
            candidates.append(compact)
        return list(dict.fromkeys(candidates))

    @staticmethod
    def _using_dummy_session(payload: Any) -> bool:
        return payload is None or (isinstance(payload, list) and not payload)

    @staticmethod
    def _market_output_name(value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized in {"telegram", "tg"}:
            return "TELEGRAM"
        if normalized in {"portal", "portals"}:
            return "PORTALS"
        if normalized in {"mrkt", "market"}:
            return "MRKT"
        if normalized in {"tonnel"}:
            return "TONNEL"
        if normalized in {"getgems", "getgem", "get-gems"}:
            return "GETGEMS"
        return normalized.upper()

    @staticmethod
    def _format_price(value: float) -> str:
        if value is None:
            return "0"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    @staticmethod
    def _contains_any_key(item: Dict[str, Any], keys: List[str]) -> bool:
        return any(key in item for key in keys)

    @staticmethod
    def _looks_like_error(payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        status = payload.get("statusCode")
        return status in {400, 401, 403, 404, 429} or bool(payload.get("error"))

    @staticmethod
    def _market_routes() -> List[Dict[str, str]]:
        return [
            {"path": "tg", "output_name": "TELEGRAM"},
            {"path": "portals", "output_name": "PORTALS"},
            {"path": "mrkt", "output_name": "MRKT"},
            {"path": "tonnel", "output_name": "TONNEL"},
            {"path": "getgems", "output_name": "GETGEMS"},
        ]


__all__ = ["GiftSatelliteAPI", "FormattedResult"]
