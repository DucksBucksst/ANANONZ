import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from gift_satellite_api import GiftSatelliteAPI

app = Flask(__name__)
CORS(app)
api = GiftSatelliteAPI()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def _normalize_collection_name(collection_name: str) -> str:
    text = str(collection_name or "").replace("-", " ").strip()
    return text.title() if text else ""


@app.route("/floor", methods=["GET"])
@app.route("/floor/<collection_name>", methods=["GET"])
def floor(collection_name: str | None = None):
    collection = collection_name and _normalize_collection_name(collection_name) or request.args.get("collection")
    if not collection:
        return jsonify({"error": "collection query parameter is required"}), 400

    # Allow optional fallback to history via ?fallback=true
    fallback = str(request.args.get("fallback", "false")).lower() in ("1", "true", "yes")

    result = api.get_floor_by_collection(collection)

    response = {
        "collection": collection,
        "floor": str(result),
        "data": result.data,
    }

    if fallback:
        # Explicitly include history-derived prices
        payload = api._request_json("GET", "/history/collection-offers")
        items = api._extract_listings(payload)
        history_prices = api._extract_market_prices_from_history(items, collection)
        response["history_prices"] = history_prices

    return jsonify(response)


@app.route("/listings", methods=["GET"])
@app.route("/listings/<collection_name>", methods=["GET"])
def listings(collection_name: str | None = None):
    collection = collection_name and _normalize_collection_name(collection_name) or request.args.get("collection")
    if not collection:
        return jsonify({"error": "collection query parameter is required"}), 400

    model = request.args.get("model")
    backdrop = request.args.get("backdrop")
    rows = api.get_listings_dto(collection=collection, model=model, backdrop=backdrop)
    return jsonify(
        {
            "collection": collection,
            "model": model,
            "backdrop": backdrop,
            "count": len(rows),
            "rows": rows,
        }
    )


@app.route("/history/<collection_name>", methods=["GET"])
def history(collection_name: str):
    """Return raw history entries and extracted history prices for the collection."""
    collection = _normalize_collection_name(collection_name)
    payload = api._request_json("GET", "/history/collection-offers")
    items = api._extract_listings(payload)
    # Extract structured history prices
    history_prices = api._extract_market_prices_from_history(items, collection)
    # Raw entries matching the collection name
    raw_entries = [it for it in items if isinstance(it, dict) and str(it.get("collectionName", "")).lower() == collection.lower()]
    return jsonify({"collection": collection, "prices": history_prices, "raw": raw_entries})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
