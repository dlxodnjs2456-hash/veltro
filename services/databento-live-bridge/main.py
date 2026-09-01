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


def _raw_price(raw: Any) -> float | None:
    try:
        f = float(raw) / 1_000_000_000
        return f if 0 < f < 1_000_000_000 else None
    except Exception:
        return None


def _event_price(record: Any) -> float | None:
    p = getattr(record, "pretty_price", None)
    try:
        if p is not None:
            f = float(p)
            if f > 0:
                return f
    except Exception:
        pass
    return _raw_price(getattr(record, "price", None))


def _market_ms(record: Any) -> int:
    ns = getattr(record, "ts_event", None)
    try:
        return int(ns) // 1_000_000
    except Exception:
        return int(time.time() * 1000)


def _action(record: Any) -> str:
    value = getattr(record, "action", "")
    value = getattr(value, "value", value)
    text = str(value or "").upper()
    if text in {"T", "TRADE", "ACTION.TRADE"} or text.endswith(".T"):
        return "T"
    return text


def _level0(record: Any) -> tuple[float | None, float | None, int, int]:
    try:
        levels = getattr(record, "levels", None)
        if not levels:
            return None, None, 0, 0
        level = levels[0]
        bid = _raw_price(getattr(level, "bid_px", None))
        ask = _raw_price(getattr(level, "ask_px", None))
        bid_sz = int(getattr(level, "bid_sz", 0) or 0)
        ask_sz = int(getattr(level, "ask_sz", 0) or 0)
        return bid, ask, bid_sz, ask_sz
    except Exception:
        return None, None, 0, 0


def on_record(record: Any) -> None:
    if isinstance(record, db.SymbolMappingMsg):
        code = SYMBOLS.get(str(record.stype_in_symbol))
        if code:
            instrument_to_code[int(record.instrument_id)] = code
        return

    mbp1_type = getattr(db, "MBP1Msg", None)
    if mbp1_type is None or not isinstance(record, mbp1_type):
        return

    code = instrument_to_code.get(int(record.instrument_id))
    if not code:
        return

    prev = latest.get(code, {})
    bid, ask, bid_sz, ask_sz = _level0(record)
    last_price = prev.get("price")
    volume = int(prev.get("volume") or 0)

    if _action(record) == "T":
        trade_price = _event_price(record)
        if trade_price is not None:
            last_price = trade_price
        volume = int(getattr(record, "size", 0) or 0)

    if last_price is None:
        return

    latest[code] = {
        "code": code,
        "symbol": next(k for k, v in SYMBOLS.items() if v == code),
        "price": float(last_price),
        "bid": bid if bid is not None else prev.get("bid"),
        "ask": ask if ask is not None else prev.get("ask"),
        "bid_size": bid_sz,
        "ask_size": ask_sz,
        "volume": volume,
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
        schema="mbp-1",
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
            latest.clear()
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
