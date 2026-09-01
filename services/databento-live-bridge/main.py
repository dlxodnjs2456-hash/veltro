import asyncio
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
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"].strip()

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


async def flush_loop() -> None:
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    url = f"{SUPABASE_URL}/rest/v1/market_live_quotes?on_conflict=code"
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            await asyncio.sleep(0.25)
            if not dirty:
                continue
            codes = list(dirty)
            rows = [latest[c] for c in codes if c in latest]
            if not rows:
                continue
            try:
                r = await client.post(url, headers=headers, json=rows)
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
