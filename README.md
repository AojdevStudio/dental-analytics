# Dental Analytics Dashboard

**Multi-location dental practice KPI dashboard with real-time Google Sheets integration**

📊 Version: 2.1.0 | 📄 License: MIT | 🏥 Requirements: Python 3.10+

---

## Description

Dental Analytics Dashboard is a **full-stack analytics platform** designed to **automate KPI tracking and reporting for dental practices**. It goes beyond **static spreadsheet analysis** by enabling **real-time multi-location data visualization** to support **dental practice management and performance optimization**.

### Use Cases
- **Daily KPI Monitoring**: Track production, collection rates, and patient metrics across locations
- **Multi-Location Management**: Unified dashboard for multiple dental office locations
- **Historical Analysis**: Time-series trending with operational date logic and weekend fallbacks
- **Performance Reporting**: Automated calculation of 5 core dental practice KPIs

Dental Analytics Dashboard helps achieve **data-driven practice management** through **provider-based architecture with alias mapping and YAML configuration**.

⭐ If you find this project helpful, please give it a star to support development and receive updates.

---

## Key Highlights

### 🏗️ **Multi-Location Provider Architecture**
Sophisticated data provider system with YAML-based alias mapping that unifies access to multiple Google Sheets across dental office locations with comprehensive error handling and logging.

### 📈 **Real-Time KPI Dashboard**
Streamlit-powered web interface with customizable brand styling that displays 5 core metrics (Production, Collection Rate, New Patients, Treatment Acceptance, Hygiene Reappointment) with automatic refresh and graceful error handling.

Dental Analytics Dashboard is designed to address challenges such as **manual KPI calculation**, **multi-location data fragmentation**, and **time-consuming reporting workflows**—delivering **automated data collection**, **unified multi-location views**, and **real-time performance insights** through **provider-based architecture with historical data management**.

📘 [Read the Full Guide](docs/guides/developer-workflow-guide.md)

---

## Quick Navigation

- [🚀 Quick Start](#quick-start)
- [⚙️ Configuration](#configuration)
- [🏗️ Architecture](#architecture)
- [📊 Dashboard Features](#dashboard-features)
- [🔧 Development](#development)
- [🧪 Testing](#testing)
- [📚 Documentation](#documentation)
- [🤝 Contributing](#contributing)

---

## Setup and Updates

### Recommended Installation
```bash
# Primary installation (new setups)
uv sync && uv run streamlit run apps/frontend/app.py

# Alternative (existing setups)
pip install -r requirements.txt && streamlit run apps/frontend/app.py
```

### Installation Features
- ✅ **Fast dependency resolution** with uv package manager
- ✅ **Automatic Google Sheets API configuration** via service account credentials
- ✅ **Multi-location alias mapping** through YAML configuration
- ✅ **Brand-themed Streamlit dashboard** with custom styling

### Quick Start Options

#### **Dashboard Mode**
1. **Install dependencies**: `uv sync`
2. **Configure credentials**: Place service account JSON in `config/credentials.json`
3. **Start dashboard**: `uv run streamlit run apps/frontend/app.py`
4. **Access interface**: Navigate to http://localhost:8501
5. **Select location**: Choose your location from dashboard

#### **Development Mode**
1. **Clone repository**:
   ```bash
   git clone https://github.com/your-org/dental-analytics.git
   ```
2. **Install with dev tools**:
   ```bash
   uv sync --dev && uv run pre-commit install
   ```

### Modular Features
Dental Analytics Dashboard can be extended to support use cases such as:
- **Multi-practice franchise management** with centralized reporting
- **Patient satisfaction tracking** through form response integration
- **Financial forecasting** using historical trend analysis
- **Staff performance metrics** with appointment and treatment data
- **Inventory management** integration with practice management systems

🧩 The provider architecture enables easy addition of new data sources and KPI calculations.

---

## Configuration

### Prerequisites ✅ Complete
1. ✅ Google Cloud project with Sheets API enabled
2. ✅ Service account credentials configured
3. ✅ Multi-sheet configuration in `config/sheets.yml`
4. ✅ Target spreadsheet access configured with appropriate permissions

### Data Source Mapping
```yaml
# config/sheets.yml
sheets:
  location_a_eod:
    spreadsheet_id: "YOUR_SPREADSHEET_ID_HERE"
    range: "EOD - Location A Billing!A:AG"
    description: "Location A end-of-day billing data"
  location_b_eod:
    spreadsheet_id: "YOUR_SPREADSHEET_ID_HERE"
    range: "EOD - Location B Billing!A:AG"
    description: "Location B end-of-day billing data"
  location_a_front:
    spreadsheet_id: "YOUR_SPREADSHEET_ID_HERE"
    range: "Location A Front KPIs Form responses!A:Z"
    description: "Location A front office KPI data"
  location_b_front:
    spreadsheet_id: "YOUR_SPREADSHEET_ID_HERE"
    range: "Location B Front KPIs Form responses!A:Z"
    description: "Location B front office KPI data"

locations:
  location_a:
    eod: "location_a_eod"
    front: "location_a_front"
  location_b:
    eod: "location_b_eod"
    front: "location_b_front"

provider_config:
  credentials_path: "config/credentials.json"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets.readonly"
```

---

## Architecture

### Core Technology Stack
- **Python 3.10+**: Modern typing with union syntax
- **Streamlit 1.30+**: Web dashboard framework
- **pandas 2.1+**: Data processing and analysis
- **Google Sheets API v4**: Real-time data retrieval
- **uv**: Fast dependency management

### Project Structure
```
dental-analytics/
├── apps/
│   ├── frontend/app.py              # Streamlit dashboard
│   └── backend/
│       ├── data_providers.py        # Multi-location provider system
│       ├── metrics.py               # KPI calculation functions
│       ├── historical_data.py       # Time-series data management
│       └── chart_data.py            # Chart data processing
├── config/
│   ├── credentials.json             # Google API credentials
│   └── sheets.yml                   # Multi-sheet configuration
├── docs/stories/                    # User story documentation
├── tests/                           # Comprehensive test suite
└── scripts/                         # Development automation
```

### Data Flow Architecture
```
Google Sheets → DataProvider → Metrics Calculator → Streamlit UI
     ↓              ↓              ↓               ↓
Multi-Location   Alias Mapping   KPI Objects    Dashboard
   Raw Data      Configuration   with History   Visualization
```

---

## Dashboard Features

- **5 Core KPIs**: Production Total, Collection Rate, New Patients, Treatment Acceptance, Hygiene Reappointment
- **Multi-Location Support**: Seamless location switching between offices
- **Brand Styling**: Customizable colors (Navy #142D54, Teal #007E9E)
- **Real-time Data**: Live Google Sheets integration with automatic refresh
- **Historical Analysis**: Time-series data with operational date logic
- **Error Handling**: Graceful degradation with "Data Unavailable" displays
- **Performance**: <3 second load time with optimized data calls

---

## Development

### CLI Tools
```bash
# Print KPIs for testing
uv run python scripts/print_kpis.py --location location_a
uv run python scripts/print_kpis.py --location both --json

# Quality checks
./scripts/quality-check.sh    # Comprehensive validation
./scripts/quick-test.sh       # Fast verification

# Code formatting
uv run black apps/ tests/
uv run ruff check apps/ tests/
```

### Code Quality
- **Black**: Code formatting
- **Ruff**: Modern Python linting
- **MyPy**: Type checking
- **Pre-commit hooks**: Automated quality gates

---

## Testing

### Test Suite Structure
```bash
# Unit tests
uv run pytest tests/test_metrics.py
uv run pytest tests/test_data_providers.py

# Integration tests
uv run pytest tests/test_historical_data.py
uv run pytest tests/test_location_switching.py

# Manual validation
uv run python test_calculations.py
```

### Coverage Goals
- **90%+ coverage** for backend business logic
- **Provider mocking** for Google Sheets API calls
- **Comprehensive error scenarios** testing

---

## Resources

### Documentation
- [📖 User Stories](docs/stories/)
- [🏗️ Architecture Overview](docs/architecture/)
- [🚀 Development Guide](docs/guides/developer-workflow-guide.md)
- [🧑‍💻 API Reference](docs/api/)

### Support and Community
- [💬 Discussions](https://github.com/your-org/dental-analytics/discussions)
- [🐞 Bug Reports](https://github.com/your-org/dental-analytics/issues)
- [🗨️ Feature Requests](https://github.com/your-org/dental-analytics/issues/new?template=feature_request.md)

---

## Contributing

We welcome all contributions!

📋 See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started.

---

## License

**MIT** - See [LICENSE](LICENSE) for details.
