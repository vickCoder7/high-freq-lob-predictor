# High-Frequency Limit Order Book (LOB) Predictor

An end-to-end quantitative research pipeline that ingests live cryptocurrency Limit Order Book data via WebSockets, applies high-frequency feature engineering, and predicts short-term micro-price movements using a PyTorch Long Short-Term Memory (LSTM) network.

This project simulates the rigorous pipeline of a quantitative research desk—from raw data acquisition to final strategy backtesting—incorporating real-world constraints such as market microstructure and Binance taker fees.

---

## Pipeline Architecture

### 1. Data Acquisition (`collect_data.py`)
Instead of relying on sanitized academic datasets, this project builds a custom ingestion engine.
* **WebSocket Streaming:** Connects to the Binance Live WebSocket API to capture the top 20 levels of the BTC/USDT Limit Order Book every 100 milliseconds.
* **I/O Optimization:** High-frequency data generates massive I/O bottlenecks. The script utilizes in-memory batching and serializes the data into Apache Parquet formats (`pyarrow`). This provides extreme disk compression and drastically speeds up I/O when loading into Pandas/PyTorch.
* **Resiliency:** Implements outer-loop `try/except` architecture to gracefully handle Binance's forced 24-hour disconnects, automatically resuming data collection without data corruption.

### 2. Feature Engineering (`feature_eng.ipynb`)
Raw bid/ask arrays are difficult for neural networks to interpret. We engineer microstructure features based on quantitative literature:
* **Mid-Price & Spread:** Extracts the true mid-price and the bid-ask spread.
* **Order Book Imbalance (OBI):** Calculates volume imbalances at Level 1 and Level 5 to detect buying/selling pressure.
* **Weighted Mid-Price:** A micro-price calculation factoring in the bid and ask volumes.
* **Z-Score Normalization:** Financial data is non-stationary. Features are strictly normalized using standard Z-scores to ensure stable gradient descent during backpropagation.

### 3. Model Development (`baseline.ipynb` & `02_deep_learning.ipynb`)
* **Baselines:** Establishes a floor performance using Logistic Regression and Random Forest algorithms.
* **Deep Learning (LSTM):** 
  * Extracted in `src/models.py`, the core model is a 2-Layer PyTorch LSTM.
  * Captures temporal dependencies by looking back at sliding sequences of length `T=50` ticks.
  * Includes a custom PyTorch `Dataset` (`src/dataset.py`) for efficient batch serving, and an early-stopping mechanism during training to prevent overfitting.

### 4. Strategy Simulation & Backtesting (`03_backtesting.ipynb`)
The ultimate test of a quantitative model is profitability. We built a custom backtester to simulate market execution.
* **Execution Engine:** Simulates Taker (Market) Orders, assuming execution at the prevailing Bid or Ask (crossing the spread).
* **Fee Structure:** Applies the standard 0.1% Binance Taker Fee to every executed transaction.

---

## Results & The Reality of HFT

**Backtest Output:**
* **Total Trades Executed:** 3,090
* **Strategy Return:** -95.24%
* **Buy & Hold Return:** +0.14%

**Why did the strategy lose 95% of its value?**
This is the most critical learning outcome of the project. A -95% return illustrates the brutal reality of High-Frequency Trading: **Trading Fees.**
At 3,090 trades, paying a 0.1% taker fee per trade resulted in the portfolio paying 309% of its value in fees to the exchange. The price jumps predicted by the model were simply not large enough to cover the Bid-Ask spread *plus* the Binance execution fee. 

**Future Optimizations:**
1. **Maker Orders:** Rewrite the execution engine to post Limit Orders (Maker), securing 0% fees or exchange rebates.
2. **Confidence Thresholding:** Apply class weights to the PyTorch Loss Function to penalize majority-class predictions, and enforce strict execution thresholding (only take a trade if the LSTM Softmax output is > 99% confident).

---

## 🛠️ Repository Structure
```
├── src/
│   ├── dataset.py               # PyTorch Sliding Window LOBDataset 
│   └── models.py                # PyTorch LSTM Architecture
├── collect_data.py              # WebSocket Parquet Ingestion Script
├── feature_eng.ipynb            # Microstructure features & Z-Score Norm
├── baseline.ipynb               # Sklearn Baselines
├── 02_deep_learning.ipynb       # PyTorch Training Loop & Evaluation
├── 03_backtesting.ipynb         # Fee-Adjusted Strategy Simulation
├── problems_and_solutions.md    # Developer logs for encountered roadblocks
└── requirements.txt
```

## How to Run

1. **Install dependencies:**
   `pip install -r requirements.txt`
2. **Collect Data:**
   Run `python collect_data.py` to stream live LOB data from Binance into `lob_data.parquet`.
3. **Train & Simulate:**
   Follow the Jupyter Notebooks in sequential order. The PyTorch training phase (`02_deep_learning.ipynb`) is highly recommended to be run on a CUDA-enabled GPU (e.g., Google Colab T4).
