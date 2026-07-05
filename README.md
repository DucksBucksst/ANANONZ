# TESTGIFTANALIZ

## Installation

Install the runtime dependency for HTTP requests:

```bash
pip install requests
```

If you want to call the live Gift Satellite API, export your token before running the module:

```bash
export GIFT_SATELLITE_TOKEN="your-token-here"
```

## Usage

The module exposes `GiftSatelliteAPI` for integration into NoNvmeHub.

```python
from gift_satellite_api import GiftSatelliteAPI

api = GiftSatelliteAPI(token="your-token")

floor_by_model = api.get_floor_by_model("Heroic Helmet", "Cyberpunk")
print(floor_by_model)

floor_by_collection = api.get_floor_by_collection("Nail Bracelet")
print(floor_by_collection)

listings = api.get_listings("Ion Gem", model="Nightstone")
print(listings)
```

## Available Methods

### 1. `get_floor_by_model(collection, model)`
Returns the minimum price found for a specific model across marketplaces.

```python
result = api.get_floor_by_model("Heroic Helmet", "Cyberpunk")
print(result)
```

### 2. `get_floor_by_collection(collection)`
Returns a compact summary of the best price per marketplace for the collection.

```python
result = api.get_floor_by_collection("Nail Bracelet")
print(result)
```

### 3. `get_listings(collection, model=None, backdrop=None)`
Returns a human-readable summary with total count and marketplace breakdown.

```python
result = api.get_listings("Scared Cat", model="Salem")
print(result)
```

### 4. `get_listings_dto(collection, model=None, backdrop=None)`
Returns a structured list of plain dictionaries that are easy to serialize or pass into your project UI.

```python
rows = api.get_listings_dto("Scared Cat", model="Salem")
for row in rows[:3]:
    print(row)
```

## Data Format

The methods accept collection and model names, then normalize the API payloads into a usable format:

- `get_floor_by_model` extracts the lowest `normalizedPrice` and returns a human-readable string.
- `get_floor_by_collection` aggregates the best price per marketplace and formats it as a single summary line.
- `get_listings` produces a readable report and also stores structured metadata in `.data`.
- `get_listings_dto` returns a list of objects with fields:
  - `marketplace`
  - `number`
  - `price`
  - `price_text`
  - `stars`
  - `slug`
  - `raw`

## Project Integration

If you want to forward data to your application, the most convenient option is:

```python
from gift_satellite_api import GiftSatelliteAPI

api = GiftSatelliteAPI(token="your-token")
rows = api.get_listings_dto("Scared Cat", model="Salem")
```

These rows are already suitable for:
- JSON serialization
- UI rendering
- filtering and sorting
- sending to a backend service

## API Endpoints

The implementation uses the following Gift Satellite endpoints:

- `GET /history/collection-offers`
- `GET /search/tg/{collection}`
- `GET /search/portals/{collection}`
- `GET /search/mrkt/{collection}`
- `GET /search/tonnel/{collection}`
- `GET /search/getgems/{collection}`
