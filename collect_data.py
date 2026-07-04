import asyncio
# pyrefly: ignore [missing-import]
import websockets
import json
import csv
from datetime import datetime

# Define your parameters
SYMBOL = "btcusdt"
LEVELS = 20
UPDATE_SPEED = "100ms"
URI = f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth{LEVELS}@{UPDATE_SPEED}"
OUTPUT_FILE = "lob_data.csv"

async def collect_lob_data():
    # Open the CSV file and write the headers
    with open(OUTPUT_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Create headers: timestamp, bid1_price, bid1_qty, ..., ask1_price, ask1_qty, ...
        headers = ['timestamp']
        for i in range(1, LEVELS + 1):
            headers.extend([f'bid{i}_price', f'bid{i}_qty', f'ask{i}_price', f'ask{i}_qty'])
        writer.writerow(headers)

        # Connect to the WebSocket
        print(f"Connecting to {URI}...")
        async with websockets.connect(URI) as websocket:
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
                        
                    # Write to CSV and flush to disk
                    writer.writerow(row)
                    file.flush() 
                    
            except websockets.ConnectionClosed:
                print("Connection closed by the server.")
            except Exception as e:
                print(f"An error occurred: {e}")

# Run the async loop
if __name__ == "__main__":
    asyncio.run(collect_lob_data())
