import asyncio
import hashlib
import hmac
import json
import os
import time
from typing import Any

import databento as db
import httpx

DATASET = "GLBX.MDP3"
SYMBOLS = {
    "NQ.n.0": "NQ",
    "ES.n.0": "ES",
    "CL.n.0": "CL",
    "GC.n.0": "GC",
    "SI.n.0": "SI",
    "6J.n.0": "6J",
}

DATABENTO_API_KEY = os.environ["DATABENTO_API_KEY"].strip()
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
INGEST_URL = f"{SUPABASE_URL}/functions/v1/databento-live-ingest"

latest: dict[str, dict[str, Any]] = {}
dirty: set[str] = set()
instrument_to_code: dict[int, str] = {}


def _price(record: Any) -> float | None:
    p = getattr(record, "pretty_price", None)
    try:
        if p is not None:
            f = float(p)
            if f > 0:
                return f
    except Exception:
        pass
    raw = getattr(record, "price", None)
    try:
        f = float(raw) / 1_000_000_000
        return f if f > 0 else None
    except Exception:
        return None


def _market_ms(record: Any) -> int:
    ns = getattr(record, "ts_event", None)
    try:
        return int(ns) // 1_000_000
    except Exception:
        return int(time.time() * 1000)


def on_record(record: Any) -> None:
    if isinstance(record, db.SymbolMappingMsg):
        code = SYMBOLS.get(str(record.stype_in_symbol))
        if code:
            instrument_to_code[int(record.instrument_id)] = code
        return

    if not isinstance(record, db.TradeMsg):
        return

    code = instrument_to_code.get(int(record.instrument_id))
    if not code:
        return

    p = _price(record)
    if p is None:
        return

    latest[code] = {
        "code": code,
        "symbol": next(k for k, v in SYMBOLS.items() if v == code),
        "price": p,
        "bid": None,
        "ask": None,
        "volume": int(getattr(record, "size", 0) or 0),
        "market_ts": _market_ms(record),
        "provider": "databento_live",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    dirty.add(code)


def _signed_headers(body: str) -> dict[str, str]:
    ts = str(int(time.time() * 1000))
    payload = f"{ts}.{body}".encode()
    signature = hmac.new(DATABENTO_API_KEY.encode(), payload, hashlib.sha256).hexdigest()
    return {
        "Content-Type": "application/json",
        "x-veltro-ts": ts,
        "x-veltro-signature": signature,
    }


async def flush_loop() -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            await asyncio.sleep(0.25)
            if not dirty:
                continue
            codes = list(dirty)
            rows = [latest[c] for c in codes if c in latest]
            if not rows:
                continue
            body = json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
            try:
                r = await client.post(INGEST_URL, headers=_signed_headers(body), content=body.encode())
                r.raise_for_status()
                for c in codes:
                    dirty.discard(c)
            except Exception as exc:
                print(f"[live-bridge] flush failed: {exc}", flush=True)


async def stream_once() -> None:
    client = db.Live(key=DATABENTO_API_KEY, heartbeat_interval_s=10)
    client.subscribe(
        dataset=DATASET,
        schema="trades",
        symbols=list(SYMBOLS.keys()),
        stype_in="continuous",
    )
    async for record in client:
        on_record(record)


async def stream_loop() -> None:
    backoff = 1
    while True:
        try:
            instrument_to_code.clear()
            await stream_once()
            backoff = 1
        except Exception as exc:
            print(f"[live-bridge] stream failed: {exc}", flush=True)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)


async def main() -> None:
    await asyncio.gather(stream_loop(), flush_loop())


if __name__ == "__main__":
    asyncio.run(main())
