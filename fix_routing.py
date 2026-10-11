import re

with open('data_feed.py', 'r', encoding='utf-8') as f:
    code = f.read()

replacement = '''    # 3. Leader fetches from upstream
    try:
        # Priority 1: Institutional Provider Layer (Delta Exchange for Crypto, Angel One for Indian Equities)
        is_crypto = any(term in symbol for term in ("USDT", "BTC", "ETH", "SOL", "XRP", "PERP"))
        is_indian = symbol.endswith(".NS") or symbol.endswith(".BO") or symbol.endswith(".MCX")
        
        if is_crypto or is_indian:
            try:
                import asyncio
                from services.normalizer import PriceNormalizer
                
                async def _get_inst_data():
                    if is_crypto:
                        from providers.delta_exchange import DeltaExchangeProvider
                        provider = DeltaExchangeProvider()
                    else:
                        from providers.angel_one import AngelOneProvider
                        provider = AngelOneProvider()
                        
                    await provider.initialize()
                    # Map timeframe "1d" to "D"
                    tf_map = {"1d": "D", "1wk": "1W", "1mo": "1M"}
                    mapped_tf = tf_map.get(interval, "D")
                    bars = await provider.get_candles(symbol, timeframe=mapped_tf, count=150)
                    if hasattr(provider, "disconnect"):
                        await provider.disconnect()
                    return bars

                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            bars = pool.submit(asyncio.run, _get_inst_data()).result()
                    else:
                        bars = loop.run_until_complete(_get_inst_data())
                except Exception:
                    bars = asyncio.run(_get_inst_data())

                if bars:
                    clean_bars, diag = PriceNormalizer.validate_and_normalize_candles(bars)
                    if clean_bars:
                        records = []
                        for b in clean_bars:
                            try:
                                t_epoch = int(pd.to_datetime(b.timestamp).timestamp())
                            except Exception:
                                t_epoch = int(time.time())
                            records.append({
                                "time": t_epoch,
                                "open": b.open,
                                "high": b.high,
                                "low": b.low,
                                "close": b.close,
                                "volume": b.volume
                            })
                        df = pd.DataFrame(records).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
                        meta = {
                            "symbol": symbol,
                            "currency": "$" if is_crypto else "₹",
                            "exchange": "DELTA" if is_crypto else "NSE/BSE",
                            "shortName": symbol,
                            "regularMarketPrice": float(df["close"].iloc[-1])
                        }
                        with _CACHE_LOCK:
                            _CACHE[cache_key] = (time.time(), df, meta)
                        return df.copy(), meta
            except Exception as e:
                logger.warning(f"Institutional feed fetch failed for {symbol}: {e}")

        # Priority 2: Direct Yahoo v8 API'''

code = re.sub(
    r'    # 3\. Leader fetches from upstream\s+try:\s+# Priority 1.*?# Priority 2: Direct Yahoo v8 API',
    replacement,
    code,
    flags=re.DOTALL
)

with open('data_feed.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Done")
