import asyncio
# pyrefly: ignore [missing-import]
import websockets
import json
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ── Configuration ──────────────────────────────────────────────────────────────
SYMBOL       = "btcusdt"
LEVELS       = 20
UPDATE_SPEED = "100ms"
URI          = f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth{LEVELS}@{UPDATE_SPEED}"
OUTPUT_FILE  = "lob_data.parquet"
BATCH_SIZE   = 1000      # Rows to accumulate in memory before writing to disk
MAX_ROWS     = 500_000   # Stop after this many rows (~14 hrs at 10 ticks/sec)
RECONNECT_WAIT = 5       # Seconds to wait before reconnecting after a drop
# ──────────────────────────────────────────────────────────────────────────────

async def collect_lob_data():
    # Build column headers
    headers = ['timestamp']
    for i in range(1, LEVELS + 1):
        headers.extend([f'bid{i}_price', f'bid{i}_qty', f'ask{i}_price', f'ask{i}_qty'])

    parquet_writer = None
    rows_collected = 0

    def flush_batch(batch_data):
        """Convert a batch list to a Parquet table and write it."""
        nonlocal parquet_writer
        df = pd.DataFrame(batch_data, columns=headers)
        for col in headers[1:]:
            df[col] = df[col].astype(float)
        table = pa.Table.from_pandas(df)
        if parquet_writer is None:
            parquet_writer = pq.ParquetWriter(OUTPUT_FILE, table.schema)
        parquet_writer.write_table(table)

    try:
        # ── Outer loop: reconnects automatically on any disconnect ─────────────
        while rows_collected < MAX_ROWS:
            try:
                print(f"Connecting to {URI}...")
                async with websockets.connect(URI) as websocket:
                    batch_data = []
                    print(f"Connected! Resuming from {rows_collected:,} / {MAX_ROWS:,} rows.\n")

                    # ── Inner loop: receive ticks ──────────────────────────────
                    while rows_collected < MAX_ROWS:
                        response = await websocket.recv()
                        data = json.loads(response)

                        # Parse the snapshot into a flat row
                        row = [datetime.now().isoformat()]
                        for i in range(LEVELS):
                            row.append(data['bids'][i][0])  # Bid price
                            row.append(data['bids'][i][1])  # Bid qty
                            row.append(data['asks'][i][0])  # Ask price
                            row.append(data['asks'][i][1])  # Ask qty

                        batch_data.append(row)
                        rows_collected += 1

                        # Flush to disk when batch is full
                        if len(batch_data) >= BATCH_SIZE:
                            flush_batch(batch_data)
                            batch_data.clear()
                            print(f"[{datetime.now().time()}] Saved batch — "
                                  f"total rows: {rows_collected:,} / {MAX_ROWS:,}")

                    # Flush any remaining rows after the inner loop exits
                    if batch_data:
                        flush_batch(batch_data)
                        batch_data.clear()

            except websockets.ConnectionClosed:
                # ── Binance closes connections every 24h — reconnect gracefully ─
                print(f"\n[{datetime.now().time()}] Connection closed by server "
                      f"at {rows_collected:,} rows. "
                      f"Reconnecting in {RECONNECT_WAIT}s...")
                await asyncio.sleep(RECONNECT_WAIT)
                continue  # Go back to the outer while loop

            except Exception as e:
                print(f"\nUnexpected error: {e}. Reconnecting in {RECONNECT_WAIT * 2}s...")
                await asyncio.sleep(RECONNECT_WAIT * 2)
                continue

        print(f"\nTarget of {MAX_ROWS:,} rows reached. Collection complete!")

    finally:
        # Always close the Parquet file safely, even if the script is Ctrl+C'd
        if parquet_writer is not None:
            parquet_writer.close()
            print(f"Parquet file '{OUTPUT_FILE}' safely closed "
                  f"({rows_collected:,} total rows).")


# Run the async loop
if __name__ == "__main__":
    asyncio.run(collect_lob_data())
