# 🏠 Kőbánya-Újhegy Real Estate Analysis Project

## 📊 Project Overview

This is a comprehensive real estate market analysis project focused on the **Kőbánya-Újhegy** residential area in Budapest, Hungary. The project combines web scraping, data analysis, and interactive visualization to provide deep insights into the local property market.

## 🚀 Key Features

### 🔍 Web Scraping Engine
- **Anti-detection scraping** with hybrid Chrome CDP connection
- **Cloudflare bypass** capabilities
- **Comprehensive data extraction** from individual property pages
- **Advertiser type classification** system
- **Floor detection** with XPath-based selectors

### 📈 Advanced Analytics Dashboard
- **Interactive Streamlit dashboard** with professional visualizations
- **Semantic text analysis** of property descriptions
- **Price-text correlation** analysis
- **Comprehensive statistical metrics** (mean, median, mode, standard deviation)
- **Investment analysis** with scoring algorithms
- **Market segmentation** by condition, floor, advertiser type

### 🤖 AI-Powered Features
- **Automated listing text generation** with market data optimization
- **Smart filtering** across multiple categories
- **Personalized seller recommendations** for specific properties
- **Market positioning analysis** for property owners

## 🛠 Technical Stack

- **Python 3.11+**
- **Web Scraping**: Playwright, Chrome DevTools Protocol
- **Data Analysis**: Pandas, NumPy
- **Visualization**: Streamlit, Plotly, Seaborn
- **Text Processing**: Regular expressions, semantic analysis

## 📁 Project Structure

```
real_agent_2/
├── 🕷️ Web Scraping
│   ├── scrape_property_details.py      # Enhanced property scraper
│   ├── ingatlan_list_scraper_refactored.py  # List scraper
│   └── scrape_ads_*.py                 # Various scraping approaches
├── 📊 Data Analysis
│   ├── ingatlan_dashboard_advanced.py  # Main interactive dashboard
│   ├── kobanyi_lakotelepek_elemzes.py  # Market analysis engine
│   ├── fill_advertiser_type.py        # Advertiser classification
│   └── remove_duplicates.py           # Data cleaning utilities
├── 🗄️ Data Files
│   ├── ingatlan_reszletes_*.csv        # Enhanced property datasets
│   ├── ingatlan_final_clean_*.csv      # Cleaned datasets
│   └── ads.db                          # SQLite database
└── 📚 Documentation
    ├── HIBRID_UTMUTATO.md             # Hybrid scraping guide
    └── IP_BLOKK_MEGOLDAS.md           # IP blocking solutions
```

## 🎯 Use Cases

### For Property Investors 💼
- **Investment scoring** algorithm for property evaluation
- **Market trend analysis** and price predictions
- **Comparative market analysis** (CMA) tools
- **ROI calculations** and risk assessment

### For Property Sellers 🏡
- **Automated listing text generation** with SEO optimization
- **Competitive pricing recommendations**
- **Market positioning analysis**
- **Optimal selling strategy** suggestions

### For Market Researchers 📈
- **Comprehensive market statistics**
- **Semantic analysis** of property descriptions
- **Advertiser behavior patterns**
- **Price correlation studies**

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.11+
Git
Chrome Browser (for scraping)
```

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd real_agent_2

# Create virtual environment
python -m venv ingatlan_agent_env
source ingatlan_agent_env/Scripts/activate  # Windows
# or
source ingatlan_agent_env/bin/activate      # macOS/Linux

# Install dependencies
pip install streamlit plotly pandas numpy seaborn playwright

# Install Playwright browsers
playwright install
```

### Running the Dashboard
```bash
# Activate virtual environment
source ingatlan_agent_env/Scripts/activate

# Launch the interactive dashboard
streamlit run ingatlan_dashboard_advanced.py
```

### Web Scraping
```bash
# Start Chrome in debug mode (Windows)
start chrome --remote-debugging-port=9222 --user-data-dir=chrome_debug

# Run the enhanced property scraper
python scrape_property_details.py
```

## 📊 Dashboard Features

### 🏠 Property Analysis
- **Market overview** with key metrics
- **Price distribution** analysis
- **Floor-based** pricing patterns
- **Condition impact** on property values

### 📝 Semantic Analysis
- **Keyword frequency** analysis
- **Price-text correlation** studies
- **Marketing strategy** insights
- **Description optimization** recommendations

### 🎯 Investment Tools
- **Property scoring** algorithm
- **Comparative analysis** tables
- **Risk assessment** metrics
- **ROI calculations**

### 🤖 AI Features
- **Smart property filtering**
- **Automated listing generation**
- **Market recommendations**
- **Personalized insights**

## 📈 Sample Analysis Results

Based on **57 properties** in Kőbánya-Újhegy:
- **Average price**: ~900,000-1,200,000 HUF/m²
- **Property conditions**: 42.1% from real estate agencies, 33.3% private sellers
- **Floor premium**: Higher floors typically command 5-15% price premium
- **Investment opportunities**: Identified through comprehensive scoring algorithm

## 🔧 Configuration

### Scraping Settings
- **Chrome debug port**: 9222
- **Rate limiting**: Human-like delays
- **Error handling**: Comprehensive retry mechanisms

### Dashboard Settings
- **Caching**: Streamlit data caching for performance
- **Responsive design**: Multi-column layouts
- **Export options**: CSV data export functionality

## 🚨 Important Notes

### Legal Compliance
- **Respect robots.txt** and website terms of service
- **Rate limiting** implemented to avoid server overload
- **Personal use** only - commercial use may require permission

### Data Privacy
- **No personal data** storage from listings
- **Public information** only
- **GDPR compliant** data handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect website terms of service and local regulations when scraping data.

## 🆘 Troubleshooting

### Common Issues
- **Chrome connection failed**: Ensure Chrome is running with debug flags
- **Module not found**: Check virtual environment activation
- **Data loading errors**: Verify CSV file formats and encoding

### Support
Create an issue in the repository with:
- Error messages
- System information
- Steps to reproduce

## 🎉 Acknowledgments

- **ingatlan.com** for providing property data
- **Streamlit community** for the amazing dashboard framework
- **Playwright team** for robust web scraping tools

---

**⚡ Built with Python | 🏠 Focused on Real Estate | 📊 Powered by Data Science**
