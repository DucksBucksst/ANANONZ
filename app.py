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


@app.route("/floor", methods=["GET"])
def floor():
    collection = request.args.get("collection")
    if not collection:
        return jsonify({"error": "collection query parameter is required"}), 400

    result = api.get_floor_by_collection(collection)
    return jsonify(
        {
            "collection": collection,
            "floor": str(result),
            "data": result.data,
        }
    )


@app.route("/listings", methods=["GET"])
def listings():
    collection = request.args.get("collection")
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
