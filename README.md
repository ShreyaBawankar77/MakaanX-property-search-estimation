# GeoEstate AI (MakaanX) 🏡
### Multimodal Real Estate Valuation, Fairness Appraisal & Investment Intelligence Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF.svg)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-Academic%20PBL-green.svg)](#)

---

## 📌 1. Project Overview & Objectives

**GeoEstate AI (MakaanX)** is an end-to-end intelligent real estate valuation and property intelligence platform developed as a Project-Based Learning (PBL) solution. Traditional housing markets suffer from fragmented pricing, subjective broker estimates, and lack of transparency. 

### Core Objectives:
1. **Accurate Property Valuation:** Predict fair market property values across major Indian metropolitan areas using machine learning pipelines trained on real transaction data.
2. **Explainable AI (XAI):** Demystify predictions by surfacing exact feature weights and top price drivers (carpet area, locality tier, bedrooms, amenities).
3. **What-If Scenario Simulation:** Enable home buyers and sellers to simulate renovations, adding amenities, or resizing to quantify exact monetary value additions.
4. **Local Market Intelligence & Real Listings:** Browse and filter authentic real-world properties mapped to specific localities and cities with real-time median price benchmarks.
5. **Conversational Real-Estate AI Assistant:** Context-aware natural language assistant capable of parsing user queries (e.g., *"Find a 2 BHK in Andheri West under 1.5 Cr with a gym"*), automatically applying smart filters and suggesting budget trade-offs.

---

## 📊 2. Dataset Information

The application is powered by an extensive real-world Indian real estate dataset:
- **Location:** `geoestate-ai/backend/data/properties.csv`
- **Total Records:** **28,398 verified listings**
- **Metropolitan Coverage:**
  - **Mumbai:** 6,820 properties
  - **Kolkata:** 6,270 properties
  - **Bengaluru:** 5,438 properties
  - **Chennai:** 4,208 properties
  - **Delhi (NCR):** 3,859 properties
  - **Hyderabad:** 1,803 properties
- **Localities:** **1,776 unique neighborhoods** (e.g., Andheri West, Bandra, Whitefield, Koramangala, Gachibowli, Salt Lake, Anna Nagar, Dwarka).
- **Listing Attributes:**
  - `property_id`: Unique identifier
  - `city` & `locality`: Geographic identifiers
  - `bhk`: Number of bedrooms (1 to 5+ BHK)
  - `area_sqft`: Super built-up / carpet area
  - `listing_price`: Quoted price in INR
  - `actual_price`: Normalized closing/benchmark price
  - `resale`: Property classification (`0` = New construction, `1` = Resale)
  - `amenities`: Active amenity tags (`Gymnasium`, `SwimmingPool`, `CarParking`, `24X7Security`, `LiftAvailable`, `ClubHouse`, etc.)

> **Note on Real Location Display:** When a user selects a City and Locality in MakaanX, the platform queries and displays the actual listings from that locality in the dataset with real prices, sizes, and amenities. Representative architectural photography is mapped by city to complement the tabular records.

---

## 🛠️ 3. Tools, Technologies & Software Stack

| Layer | Technologies Used | Purpose |
|---|---|---|
| **Frontend** | React 19, Vite 8, JavaScript (ES2024), CSS3, Recharts, Leaflet, Lucide Icons | Responsive single-page application with interactive gauges, price charts, filters, and chat interface |
| **Backend API** | Python 3.13, FastAPI, Uvicorn, Pydantic v2 | High-throughput asynchronous REST API providing inference, search, and analytics |
| **Machine Learning** | Scikit-Learn, NumPy, Pandas, Joblib | Random Forest Regressor with OneHotEncoder pipeline, feature importance extractor |
| **Database** | SQLite, SQLAlchemy ORM | User authentication, saved favorites, and property records caching |
| **Explainability (XAI)**| Feature Importances, SHAP-inspired relative impact calculations | Transparent prediction justification |
| **Developer Tools** | Pyright / Pylance, PowerShell, Git | Static type checking and automated orchestrator scripts |

---

## 🚀 4. Step-by-Step Execution Guide

### Prerequisites
1. **Python 3.10 to 3.13** installed and added to `PATH`.
2. **Node.js 18+** and `npm` installed.

---

### Option A: Quick Start (Recommended on Windows)
Run the automated startup script from PowerShell:
```powershell
# From the project root directory
.\geoestate-ai\start-platform.ps1
```
This script automatically checks Python and Node environments, allocates optimized CPU thread limits, launches the FastAPI backend and Vite frontend, verifies health endpoints, and prints the access URLs.

---

### Option B: Manual Setup

#### Step 1: Backend Setup
```bash
# 1. Navigate to the project root
cd PBL-PROJECT

# 2. Activate virtual environment (or create one: python -m venv .venv)
.\.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On macOS/Linux

# 3. Install Python dependencies
pip install -r geoestate-ai/requirements.txt

# 4. Start the FastAPI backend server
cd geoestate-ai
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
Backend will be live at `http://127.0.0.1:8000` (Health Check: `http://127.0.0.1:8000/api/health`).

#### Step 2: Frontend Setup
Open a new terminal window:
```bash
# 1. Navigate to the frontend directory
cd PBL-PROJECT/geoestate-ai/frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite development server
npm run dev -- --host 0.0.0.0 --port 5175
```
Frontend will be live at `http://localhost:5175`.

---

## 🌐 5. Key System Features & Modules

1. **AI Valuation Engine (`/api/predict`):**
   - Inputs: City, Locality, BHK, Area (sq.ft), Resale status, and Amenities.
   - Outputs: Fair predicted price, 80% confidence interval, price per sq.ft, and fairness rating (`UNDERPRICED`, `FAIRLY PRICED`, or `OVERPRICED`).

2. **What-If Scenario Simulator (`/api/predict/what-if`):**
   - Live interactive sliders to test: *"What if I add a swimming pool?"*, *"What if the property was 200 sq.ft larger?"*.
   - Instant calculation of price delta ($\Delta$ Price).

3. **Locality Market Intelligence (`/api/location/analyze` & `/api/trends`):**
   - Locality average vs median price per sq.ft benchmarks.
   - Multi-year price trends (2021–2024) and 6/12/24-month forecast models.

4. **Authentic Property Listings (`/api/properties`):**
   - Live filters by city, locality, price ceiling, bedrooms, and amenities.
   - Smart Budget Coach suggesting nearby alternatives if exact criteria are over-budget.

5. **Conversational AI Assistant (`/api/assistant/chat`):**
   - Parses unstructured natural language property search queries into structured filters and answers with matching listings.

6. **Image Quality & Room Analysis (`/api/analyze-image`):**
   - Evaluates listing photos for lighting, sharpness, and spatial aesthetic scores.

---

## 📈 6. Machine Learning Model Performance

| Metric | Random Forest Model (Trained on 28k+ Properties) |
|---|---|
| **Dataset Size** | 28,398 listings across 6 metro cities |
| **Train/Test Split** | 80% Train (22,718), 20% Test (5,680) |
| **Key Features** | City, Locality, Area (sq.ft), BHK, Resale, 6 Key Amenities |
| **R² Score** | **~0.85+** |
| **Top Price Drivers** | Area (sq.ft) (44.5%), Locality (25.8%), City Tier (11.5%), BHK (9.9%) |

---

## 📂 7. Project Directory Structure

```text
geoestate-ai/
├── backend/
│   ├── data/
│   │   └── properties.csv        # 28,398 real Indian property listings
│   ├── ml/
│   │   ├── house_price_model.py  # Production Random Forest pipeline & caching
│   │   ├── model.py              # ML facade interface
│   │   ├── explainability.py     # Feature attribution & importance calculation
│   │   ├── preprocess.py         # Data normalization & imputation
│   │   └── feature_engineering.py# Spatial context & locality metrics
│   ├── routes/
│   │   ├── prediction.py         # /api/predict & /api/predict/what-if
│   │   ├── properties.py         # /api/properties & /api/budget/coach
│   │   ├── location.py           # /api/location/analyze
│   │   ├── trends.py             # /api/trends
│   │   ├── assistant.py          # /api/assistant/chat (NLP search)
│   │   ├── auth.py               # Authentication & profiles
│   │   └── image_analysis.py     # Listing photo quality scoring
│   ├── saved_models/             # Serialized joblib model bundles
│   ├── database.py               # SQLite / SQLAlchemy connection
│   ├── models.py                 # DB schemas
│   ├── schemas.py                # Pydantic request/response schemas
│   └── main.py                   # FastAPI application entrypoint
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Primary application UI & dashboard
│   │   ├── main.jsx              # React root renderer
│   │   └── index.css             # Tailwind & theme styles
│   ├── package.json              # NPM dependencies
│   └── vite.config.js            # Vite bundler & reverse proxy configuration
├── scripts/
│   └── import_property_dataset.py# Data ingestion & normalization utility
├── requirements.txt              # Python package requirements
├── start-platform.ps1            # One-click Windows orchestrator
├── Project_Poster.html           # Full graphical conference project poster (HTML)
├── Project_Poster.png            # High-resolution printable poster graphic
└── README.md                     # Project documentation & instructions
```

---

## 👥 8. Submission Details

- **Project:** PBL (Project-Based Learning) Academic Submission
- **Domain:** Artificial Intelligence / Machine Learning / Web Applications
- **Submission Form:** [Google Form Link](https://forms.gle/tXwo7o8ZkqihAzQB8)
- **Deadline:** 10th November 2026
- **Status:** Complete, fully operational, 0 syntax/typing errors.

