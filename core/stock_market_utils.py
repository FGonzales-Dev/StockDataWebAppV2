
STOCK_MARKETS = {
    "New York Stock Exchange": "XNYS",
    "Nasdaq": "XNAS",
    "NYSE American": "XASE",
    "Toronto Stock Exchange": "XTSE",
    "TSX Venture Exchange": "XTSX",
    "Mexico Stock Exchange (BMV)": "XMEX",
    "London Stock Exchange": "XLON",
    "Euronext Amsterdam": "XAMS",
    "Euronext Paris": "XPAR",
    "Deutsche Börse Xetra": "XETR",
    "SIX Swiss Exchange": "XSWX",
    "Borsa Italiana (Milan)": "XMIL",
    "Madrid Stock Exchange (BME)": "XMAD",
    "Oslo Børs": "XOSL",
    "Irish Stock Exchange (Euronext Dublin)": "XDUB",
    "Warsaw Stock Exchange": "XWAR",
    "Nasdaq Stockholm": "XSTO",
    "Nasdaq Copenhagen": "XCSE",
    "Nasdaq Helsinki": "XHEL",
    "Euronext Lisbon": "XLIS",
    "Euronext Brussels": "XBRU",
    "Tokyo Stock Exchange": "XTKS",
    "Hong Kong Stock Exchange": "XHKG",
    "Shanghai Stock Exchange": "XSHG",
    "Shenzhen Stock Exchange": "XSHE",
    "National Stock Exchange of India": "XNSE",
    "BSE (Bombay Stock Exchange)": "XBOM",
    "Singapore Exchange": "XSES",
    "Australian Securities Exchange": "XASX",
    "New Zealand Exchange": "XNZE",
    "Korea Exchange": "XKRX",
    "Taiwan Stock Exchange": "XTAI",
    "Stock Exchange of Thailand (SET)": "XBKK",
    "Indonesia Stock Exchange (IDX)": "XIDX",
    "Bursa Malaysia": "XKLS",
    "Philippine Stock Exchange": "XPHS",
    "Ho Chi Minh Stock Exchange (HOSE)": "XSTC",
    "Saudi Exchange (Tadawul)": "XSAU",
    "Abu Dhabi Securities Exchange": "XADS",
    "Dubai Financial Market": "XDFM",
    "Nasdaq Dubai": "DIFX",
    "Tel-Aviv Stock Exchange": "XTAE",
    "Egyptian Exchange": "XCAI",
    "Johannesburg Stock Exchange": "XJSE"
}

def get_market_id(market_name):
    return STOCK_MARKETS.get(market_name)

def get_market_name(market_id):
    for name, id in STOCK_MARKETS.items():
        if id == market_id:
            return name
    return None

def get_all_markets():
    return [(name, market_id) for name, market_id in STOCK_MARKETS.items()]

def get_market_choices():
    return [(market_id, f"{name} ({market_id})") for name, market_id in STOCK_MARKETS.items()]

def search_markets(query):
    query = query.lower()
    results = []
    
    for name, market_id in STOCK_MARKETS.items():
        if query in name.lower() or query in market_id.lower():
            results.append((name, market_id))
    
    return results
