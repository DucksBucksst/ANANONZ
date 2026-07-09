from gift_satellite_api import GiftSatelliteAPI
import sys


EXPECTED = "TELEGRAM: 5201g | MRKT: 6.500g | PORTALS: 4798g | TONNEL: 38865g | GETGEMS: 4800g"


def floor_for_market(api: GiftSatelliteAPI, collection: str, market: str) -> float:
    payload = api._search_listings(collection=collection, market=market)
    items = api._extract_listings(payload)
    prices = [api._extract_price(it) for it in items if api._extract_price(it) is not None]
    return float(min(prices)) if prices else 0.0


def fmt_mrkt(value: float) -> str:
    # Format 6500 -> 6.500 to match requested representation
    try:
        iv = int(round(value))
    except Exception:
        return str(value)
    s = f"{iv}"
    if len(s) > 3:
        return s[:-3] + "." + s[-3:]
    return s


def main():
    api = GiftSatelliteAPI()
    collection = "Plush Pepe"
    tg = int(floor_for_market(api, collection, "tg"))
    mrkt = floor_for_market(api, collection, "mrkt")
    portals = int(floor_for_market(api, collection, "portals"))
    tonnel = int(floor_for_market(api, collection, "tonnel"))
    getgems = int(floor_for_market(api, collection, "getgems"))

    formatted = f"TELEGRAM: {tg}g | MRKT: {fmt_mrkt(mrkt)}g | PORTALS: {portals}g | TONNEL: {tonnel}g | GETGEMS: {getgems}g"
    print("API returned:", formatted)
    print("Expected:", EXPECTED)
    if formatted == EXPECTED:
        print("Match: results are identical")
        return 0
    else:
        print("Mismatch: results differ")
        try:
            print("Detail prices:", {
                'TELEGRAM': tg,
                'MRKT': mrkt,
                'PORTALS': portals,
                'TONNEL': tonnel,
                'GETGEMS': getgems,
            })
        except Exception:
            pass
        return 2


if __name__ == '__main__':
    sys.exit(main())
