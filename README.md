# Gift Satellite Integration

This repository provides a lightweight Python client for Gift Satellite.
It is designed to let another developer or AI agent connect to a project in under two minutes.

## Why this repository

- Full listing retrieval via `get_listings_dto()` — nothing is skipped
- Marketplace floor price aggregation via `get_floor_by_collection()`
- Works with live Gift Satellite API and supports token configuration via environment or explicit parameter
- Minimal dependency: only `requests`

## Quick Integration

1. Clone or copy this repository into your project.
2. Install the runtime dependency.
3. Set `GIFT_SATELLITE_TOKEN`.
4. Import `GiftSatelliteAPI` and call the methods below.

```bash
python3 -m pip install requests
export GIFT_SATELLITE_TOKEN="your-token-here"
```

```python
from gift_satellite_api import GiftSatelliteAPI

api = GiftSatelliteAPI()

# Get the full raw listing set for the collection.
rows = api.get_listings_dto("B-Day Candle")
print(f"Found {len(rows)} listings")
for row in rows[:10]:
    print(row)

# Get marketplace floor prices for the collection.
print(api.get_floor_by_collection("B-Day Candle"))
print(api.get_floor_by_collection("Plush Pepe"))
print(api.get_floor_by_collection("Astral Shard"))
```

## Sample Floor Results

When running the live integration, these sample results reflect Gift Satellite data at the time of this check:

- `B-Day Candle`: `TELEGRAM: 5.71g | MRKT: 3.5g | PORTALS: 3.53g | TONNEL: 3.71g | GETGEMS: 3.5g`
- `Plush Pepe`: `TELEGRAM: 5201.85g | MRKT: 6500g | PORTALS: 4798g | TONNEL: 38865.96g | GETGEMS: 4800g`
- `Astral Shard`: `TELEGRAM: 129.85g | MRKT: 112.5g | PORTALS: 114.97g | TONNEL: 196.1g | GETGEMS: 125g`

> Note: marketplace prices are live and may move between requests, so exact values can change while the structure and coverage remain the same.

## Installation

Install the runtime dependency with pip:

```bash
python3 -m pip install -r requirements.txt
```

## Quick start

Run the client from the repository root after setting the token:

```bash
export GIFT_SATELLITE_TOKEN="your-token-here"
python3 -c "from gift_satellite_api import GiftSatelliteAPI; api = GiftSatelliteAPI(); print(api.get_floor_by_collection('B-Day Candle'))"
```

## Configuration

The client uses the standard environment variable:

```bash
export GIFT_SATELLITE_TOKEN="your-token-here"
```

Alternatively, pass the token explicitly:

```python
api = GiftSatelliteAPI(token="your-token-here")
```

## API Usage

### Full listing retrieval

Use `get_listings_dto()` to get every listing record returned by Gift Satellite.
This method returns a complete list of dictionaries, including the raw payload.

```python
from gift_satellite_api import GiftSatelliteAPI

api = GiftSatelliteAPI()
rows = api.get_listings_dto("B-Day Candle")
print(len(rows))
print(rows[0])
```

### Marketplace floor prices

Use `get_floor_by_collection()` for a consolidated floor-price summary across marketplaces.

```python
result = api.get_floor_by_collection("B-Day Candle")
print(result)
```

### Additional methods

- `get_floor_by_model(collection, model)` — best price for a specific model
- `get_listings(collection, model=None, backdrop=None)` — readable listing summary
- `get_listings_dto(collection, model=None, backdrop=None)` — full structured output

## Lovable / AI-agent usage guide

If your Lovable mini-app or another AI agent needs to search listings, the recommended mapping is:

- Collection only: "Artisan Brick"
- Collection + model: "Artisan Brick + Cash Roll"
- Collection + model + backdrop: "Artisan Brick + Cash Roll + Moonstone"

The API should translate those requests into these endpoint calls:

```bash
curl "https://<your-app>.railway.app/listings/artisan-brick"
curl "https://<your-app>.railway.app/listings/artisan-brick?model=Cash%20Roll"
curl "https://<your-app>.railway.app/listings/artisan-brick?model=Cash%20Roll&backdrop=Moonstone"
```

For floor price queries, use:

```bash
curl "https://<your-app>.railway.app/floor/artisan-brick"
```

Recommended rules for the mini-app:

- `collection` is required.
- `model` is optional and should be passed as the `model` query parameter.
- `backdrop` is optional and should be passed as the `backdrop` query parameter.
- Collection names may be passed with spaces or hyphens, for example `Artisan Brick` or `artisan-brick`.
- Use `/listings/<collection>` when you need full rows and `/floor/<collection>` when you need a market-summary floor price.

## Result format

`get_listings_dto()` returns items with the following fields:

- `marketplace`
- `number`
- `price`
- `price_text`
- `stars`
- `slug`
- `raw`

`get_floor_by_collection()` returns a formatted summary string and metadata in `.data`.

## Notes for integrators

- The client queries all five market routes: `tg`, `portals`, `mrkt`, `tonnel`, and `getgems`.
- `get_listings_dto()` returns the full listing set from every available route, so nothing is omitted.
- The repository is intentionally minimal and does not require packaging to use.
- Import `GiftSatelliteAPI` directly from `gift_satellite_api.py` in your project root.
- For production usage, keep `GIFT_SATELLITE_TOKEN` secret and do not commit it.

## Deploying to Railway

This repository is now Railway-ready.

1. Add a Railway secret named `GIFT_SATELLITE_TOKEN`.
2. Add a Railway secret named `GIFT_SATELLITE_BASE_URL` only if you use a custom API endpoint.
3. Ensure `Procfile` exists with:

```text
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

4. Ensure `requirements.txt` contains:

```text
flask
flask-cors
gunicorn
requests
```

5. Deploy the repository to Railway.

6. Use the `PORT` environment variable automatically provided by Railway.

### Example Railway health check

```bash
curl https://<your-app>.railway.app/health
```

### Example API calls

```bash
curl "https://<your-app>.railway.app/floor?collection=B-Day%20Candle"
curl "https://<your-app>.railway.app/listings?collection=Plush%20Pepe"
```

### Troubleshooting 502

If Railway returns `502`, check these points:
- `PORT` must be read from the environment in `app.py`.
- `Procfile` must contain `web: python app.py`.
- `requirements.txt` must list `flask` and `flask-cors`.
- `GIFT_SATELLITE_TOKEN` must be set in Railway secrets.
- Inspect Railway deployment logs for Python import errors or missing dependencies.
