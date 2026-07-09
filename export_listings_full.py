import json
import sys
from pathlib import Path
from gift_satellite_api import GiftSatelliteAPI


def export_full(collection: str, model: str, out_dir: str = "exports") -> Path:
    api = GiftSatelliteAPI()
    dto = api.get_listings_dto(collection=collection, model=model)
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    out_file = p / f"{collection.replace(' ', '_')}_{model.replace(' ', '_')}_full.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)
    return out_file


def main(argv):
    if len(argv) < 3:
        print("Usage: python export_listings_full.py <collection> <model>")
        return 2
    collection = argv[1]
    model = argv[2]
    out = export_full(collection, model)
    print(f"Exported {collection} / {model} -> {out}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
