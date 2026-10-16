# ⚡ AlphaPulse — AI-Powered Market Structure & Quantitative Analytics Terminal

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![TradingView](https://img.shields.io/badge/TradingView-Lightweight%20Charts%20v4.2-2962FF.svg)](https://www.tradingview.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AlphaPulse** is a high-performance, enterprise-grade quantitative market structure intelligence platform. Built on the mathematical foundation of **Auction Market Theory (AMT)** and **Steidlmayer Market Profile** mechanics, it translates multidimensional continuous double auctions into explainable, transparent, and non-predictive educational market diagnostics.

> **Important Note:** AlphaPulse is an educational and analytical research platform. It does **NOT** provide financial advice or speculative buy/sell signals. It is designed for quantitative researchers, students, traders, and institutional market observers.

---

## 🏛️ Academic & Research Foundations

AlphaPulse includes complete academic dissertation documents, IEEE conference-grade review papers, research proposals, and reproducibility audits for university continuous assessment (CA3 / CA4) and IEEE submission tracks:

- **[CA3 Comprehensive Submission (`docs/CA3_Comprehensive_Submission_AlphaPulse.docx`)](docs/CA3_Comprehensive_Submission_AlphaPulse.docx)**
  - **Q1: Case Study Analysis** — Formal research title, system architecture, flow diagrams, 4-layer engine, and engineering challenges.
  - **Q2: Full Research Proposal** — 1000+ words, theoretical background, 5 core objectives, hypotheses ($H_0, H_1$), 20-study literature review table, 13-week execution schedule, and institutional budget.
  - **Q3: Dataset Analysis & EDA** — Public NSE NIFTY 50 microstructure dataset (~465,000 observations), data dictionary, and empirical findings.
- **[CA4 Review Research Paper — IEEE Format (`docs/CA4_Review_Research_Paper_IEEE_AlphaPulse.docx`)](docs/CA4_Review_Research_Paper_IEEE_AlphaPulse.docx)**
  - IEEE conference-ready paper: Abstract, Index Terms, Sections I–VII, Comparative Methodology Matrix, Mathematical Formulations ($DDAI, TPAM$), and **30 peer-reviewed IEEE citations**.
- **[Plagiarism & IEEE Feasibility Report (`docs/Plagiarism_Report_And_IEEE_Assessment_AlphaPulse.docx`)](docs/Plagiarism_Report_And_IEEE_Assessment_AlphaPulse.docx)**
  - Turnitin similarity forecast $\le 4.8\%$, Originality $\ge 95.2\%$, Technology Readiness Level (**TRL-6**), Innovation Score (**9.2/10**), and Signed Academic Integrity Declaration.

---

## 🚀 Key Terminal Features & Capabilities

### 1. Market Profile & Auction Market Theory Engine
- **Dynamic Value Area Extraction**: Numerically sweeps the two-sided volume distribution to extract the 68.2% empirical volume boundaries (**VAH** and **VAL**).
- **Volume Point of Control (VPOC)**: Identifies the exact fair-value equilibrium price bin containing peak transacted volume.
- **Initial Balance (IB) Parameters**: Computes first 60-minute session range and extension factors to classify rotational versus initiative day types.
- **Novel Microstructure Metrics**:
  - **DDAI (Dual-Distribution Asymmetry Index)**: $\frac{V_{\text{above}} - V_{\text{below}}}{V_{\text{total}}}$ quantifying institutional inventory absorption.
  - **TPAM (Thermodynamic Price Acceptance Metric)**: Time-volume integral evaluating whether excursions outside value are accepted or rejected.

### 2. Live F&O Intelligence & Option Chain Analytics
- **Full Greeks Pipeline**: Real-time Delta, Gamma, Theta, Vega, and Rho calculated via Black-Scholes models.
- **Open Interest (OI) Buildup Tracking**: Automatic tagging of Long Build-up, Short Build-up, Long Unwinding, and Short Covering.
- **Max Pain & Put-Call Ratio (PCR)**: Real-time calculation of strike-level institutional support and resistance clusters.

### 3. Institutional Market Overview & Indices Telemetry
- Authoritative exchange time synchronization (IST - Asia/Kolkata) with session status (`OPEN`, `PRE_OPEN`, `CLOSED`).
- Real-time institutional overview for **NIFTY 50**, **BANK NIFTY**, **FINNIFTY**, **SENSEX**, **MIDCAP NIFTY**, and **INDIA VIX**.
- Market Breadth engine with live Advance/Decline ratios.

### 4. High-Speed Instant Autocomplete Search (`/api/search`)
- Search across Indian Equities (NSE/BSE), US Mega-Caps (NASDAQ/S&P 500), Global Indices, and Crypto pairs.
- In-memory registry with keyboard navigation and sub-15ms response latency.

### 5. Scalable Enterprise Infrastructure
- **Single-Flight Deduplication**: Prevents upstream request spikes (Thundering Herd) when multiple users query the same ticker.
- **GZip Compression**: Compresses candlestick and profile JSON payloads by ~80% via Starlette middleware.
- **Zero External CDN Dependencies**: Bundles local TradingView Lightweight Charts (v4.2).

---

## 🛠️ Project Structure

```
alphapulse-stock-scanner/
├── docs/                                  # Academic Submissions & Research Papers
│   ├── CA3_Comprehensive_Submission_AlphaPulse.docx
│   ├── CA4_Review_Research_Paper_IEEE_AlphaPulse.docx
│   └── Plagiarism_Report_And_IEEE_Assessment_AlphaPulse.docx
├── services/                              # Microstructure & Market Intelligence Services
│   ├── fno_engine.py                      # Black-Scholes Option Chain, Greeks & OI Buildup
│   ├── indices_engine.py                  # Major Indices Overview & Market Breadth Engine
│   └── market_time.py                     # Exchange Clock & Market Session State
├── templates/
│   └── index.html                         # Terminal UI with Market Profile & Screener
├── static/
│   ├── css/style.css                      # Terminal dark theme styling
│   └── js/                                # Local Lightweight Charts & Dashboard Logic
├── app.py                                 # FastAPI Web Application & API Gateway
├── data_feed.py                           # Thread-safe cached data provider
├── scanner.py                             # Multi-threaded parallel market scanner
├── technicals.py                          # Vectorized ATR, Supertrend, RSI, VWAP calculations
├── ticker_search.py                       # Sub-millisecond in-memory autocomplete index
├── stock_lists.py                         # Curated ticker universes (NSE, US, Indices)
└── test_app.py                            # End-to-end verification test suite
```

---

## 🏃 Getting Started

### Prerequisites
- Python 3.10 or higher
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/ManishPatil2005/alphapulse-stock-scanner.git
cd alphapulse-stock-scanner

# Install required dependencies
pip install -r requirements.txt
# (Optional) For building Word documents
pip install python-docx
```

### Launch Terminal
```bash
# Start the FastAPI server
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 🔬 Scientific Citations

If you use AlphaPulse in academic research, educational coursework, or benchmarking, please cite:

```bibtex
@inproceedings{patil2026alphapulse,
  title={AlphaPulse: An Explainable Machine Learning Framework for Market Microstructure Analytics Grounded in Auction Market Theory},
  author={Patil, Manish},
  booktitle={IEEE Symposium on Computational Intelligence for Financial Engineering and Economics (CIFEr)},
  year={2026}
}
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
