import pandas as pd

# Path to the collected data
PARQUET_FILE = "lob_data.parquet"

try:
    # Read the parquet file into a Pandas DataFrame
    df = pd.read_parquet(PARQUET_FILE)
    
    # Display the shape of the data (rows, columns)
    print(f"Data Shape: {df.shape}")
    
    # Display the first 5 rows
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Display the last 5 rows
    print("\nLast 5 rows:")
    print(df.tail())
    
    # Check data types and missing values
    print("\nData Info:")
    df.info()

except FileNotFoundError:
    print(f"Error: {PARQUET_FILE} not found. Run collect_data.py first to generate some data.")
except Exception as e:
    print(f"An error occurred: {e}")
