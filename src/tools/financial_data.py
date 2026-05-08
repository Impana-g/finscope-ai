import yfinance as yf
COMPANY_TICKERS = { 
    "infosys": "INFY", 
    "tcs": "TCS", "tata consultancy": "TCS", 
    "wipro": "WIT", 
    "hcl": "HCLTECH", 
    "hcl technologies": "HCLTECH",
    "tech mahindra": "TECHM", 
    "sun pharma": "SUNPHARMA",
    "sun pharmaceutical": "SUNPHARMA", 
    "dr reddy": "DRREDDY", 
    "dr reddys": "DRREDDY", 
    "cipla": "CIPLA", 
    "biocon": "BIOCON",
}
def get_company_ticker(company_name: str) -> str:
    name_lower = company_name.lower().strip() 
    for key, ticker in COMPANY_TICKERS.items(): 
        if key in name_lower: 
            return ticker
    return company_name
def format_number(value) -> str:
        if value is None: 
            return "N/A" 
        value = float(value)
        if value >= 1_000_000_000_000: 
            return f"${value / 1_000_000_000_000:.2f}T" 
        elif value >= 1_000_000_000: 
            return f"${value / 1_000_000_000:.2f}B" 
        elif value >= 1_000_000: 
            return f"${value / 1_000_000:.2f}M" 
        elif value >= 1_000: 
            return f"${value / 1_000:.2f}K" 
        else: 
            return f"${value:.2f}"

    
def get_stock_data(ticker: str) -> dict:
    # Try different formats
    formats_to_try = [ 
        ticker, 
        f"{ticker}.NS",
        f"{ticker}.BO" 
        ]
    for t in formats_to_try: 
        try: 
            print(f" Trying ticker: {t}...") 
            stock = yf.Ticker(t) 
            info = stock.info
            # Check if we got real data
            price = info.get("regularMarketPrice") or info.get("currentPrice") 
            if not info or not price: 
                print(f" No data for {t}, trying next...") 
                continue
            # Build clean result
            return { "success": True, 
                    "ticker_used": t, 
                    "company_name": info.get("longName", "Unknown"), 
                    "current_price": price, 
                    "currency": info.get("currency", "USD"),
                    "market_cap": info.get("marketCap"),
                    "market_cap_readable":
format_number(info.get("marketCap")), 
                "pe_ratio": info.get("trailingPE"), 
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue"), 
                "revenue_readable": format_number(info.get("totalRevenue")), 
                "profit_margin_pct": round( (info.get("profitMargins") or 0) * 100, 2 
                ),
                "dividend_yield_pct": round
                ( (info.get("dividendYield") or 0) * 100, 2 
                ),
                "week_52_high": info.get("fiftyTwoWeekHigh"), 
                "week_52_low": info.get("fiftyTwoWeekLow"), 
                "analyst_rating": info.get("recommendationKey", "N/A"), 
                "sector": info.get("sector", "N/A"), 
                "industry": info.get("industry", "N/A"),
                "country": info.get("country", "N/A"), 
                "employees": info.get("fullTimeEmployees"), 
                }
        except Exception as e:
             print(f" Error for {t}: {e}") 
             continue
        return { 
            "success": True, 
            "ticker": ticker, 
            "error": 
            ( f"Could not find stock data for '{ticker}'. " 
              f"Please check the company name or ticker symbol." 
            ) 
            }
    
if __name__ == "__main__": 
    print("=" * 50) 
    print("Testing Financial Data Tool") 
    print("=" * 50) 
    print("\n1. Ticker lookup test:") 
    print(f" Infosys → {get_company_ticker('Infosys')}") 
    print(f" Sun Pharma → {get_company_ticker('Sun Pharma')}") 
    print(f" TCS → {get_company_ticker('TCS')}") 
    print("\n2. Stock data test (Infosys):") 
    result = get_stock_data("INFY") 
    if result["success"]: 
        print(f" Company: {result['company_name']}") 
        print(f" Price: {result['current_price']} {result['currency']}") 
        print(f" Market Cap: {result['market_cap_readable']}") 
        print(f" P/E Ratio: {result['pe_ratio']}") 
        print(f" Profit Margin: {result['profit_margin_pct']}%") 
        print(f" Analyst Rating: {result['analyst_rating']}") 
    else: 
        print(f" Error: {result['error']}") 
    print("\n3. Format number test:") 
    print(f" {format_number(82_000_000_000)}") 
    print(f" {format_number(1_500_000_000_000)}") 
    print("\n Financial data tests done!")