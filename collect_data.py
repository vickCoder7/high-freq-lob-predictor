import asyncio
# pyrefly: ignore [missing-import]
import websockets
import json
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Define your parameters
SYMBOL = "btcusdt"
LEVELS = 20
UPDATE_SPEED = "100ms"
URI = f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth{LEVELS}@{UPDATE_SPEED}"
OUTPUT_FILE = "lob_data.parquet"
BATCH_SIZE = 1000  # Number of rows to collect before writing to disk

async def collect_lob_data():
    # Create headers: timestamp, bid1_price, bid1_qty, ..., ask1_price, ask1_qty, ...
    headers = ['timestamp']
    for i in range(1, LEVELS + 1):
        headers.extend([f'bid{i}_price', f'bid{i}_qty', f'ask{i}_price', f'ask{i}_qty'])
        
    parquet_writer = None
    
    # Connect to the WebSocket
    print(f"Connecting to {URI}...")
    async with websockets.connect(URI) as websocket:
        batch_data = [] # In-memory list to accumulate rows
        print("Connected! Listening for order book updates...")
            
        try:
            # Listen for messages indefinitely
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                # Parse the data
                # data['bids'] and data['asks'] are lists of [price, quantity]
                row = [datetime.now().isoformat()]
                
                for i in range(LEVELS):
                    # Bids
                    row.append(data['bids'][i][0]) # Price
                    row.append(data['bids'][i][1]) # Quantity
                    # Asks
                    row.append(data['asks'][i][0]) # Price
                    row.append(data['asks'][i][1]) # Quantity
                    
                # Append row to the batch
                batch_data.append(row)
                
                # If batch is full, convert to Parquet and flush to disk
                if len(batch_data) >= BATCH_SIZE:
                    # Convert the batch to a pandas DataFrame
                    df = pd.DataFrame(batch_data, columns=headers)
                    
                    # Make sure numerical columns are floats, not strings
                    for col in headers[1:]:
                        df[col] = df[col].astype(float)
                        
                    # Convert to PyArrow Table
                    table = pa.Table.from_pandas(df)
                    
                    # Initialize writer on the first batch when schema is known
                    if parquet_writer is None:
                        parquet_writer = pq.ParquetWriter(OUTPUT_FILE, table.schema)
                        
                    # Write the batch table to the Parquet file
                    parquet_writer.write_table(table)
                    
                    print(f"[{datetime.now().time()}] Written batch of {BATCH_SIZE} rows to {OUTPUT_FILE}")
                    batch_data.clear() # Reset the batch
                    
        except websockets.ConnectionClosed:
            print("Connection closed by the server.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Ensure the parquet file is safely closed when the script is stopped
            if parquet_writer is not None:
                if len(batch_data) > 0:
                    df = pd.DataFrame(batch_data, columns=headers)
                    for col in headers[1:]:
                        df[col] = df[col].astype(float)
                    table = pa.Table.from_pandas(df)
                    parquet_writer.write_table(table)
                parquet_writer.close()
                print(f"\nSafely closed the Parquet file {OUTPUT_FILE}.")

# Run the async loop
if __name__ == "__main__":
    asyncio.run(collect_lob_data())
