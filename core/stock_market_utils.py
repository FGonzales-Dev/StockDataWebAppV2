"""
Stock Market Utilities

This module contains utilities for handling stock market data,
including mappings between market names and their identifiers.
"""

# Stock market mapping: Market Name -> Market ID
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
    """
    Get the market ID for a given market name.
    
    Args:
        market_name (str): The name of the stock market
        
    Returns:
        str: The market ID if found, None otherwise
    """
    return STOCK_MARKETS.get(market_name)

def get_market_name(market_id):
    """
    Get the market name for a given market ID.
    
    Args:
        market_id (str): The market ID
        
    Returns:
        str: The market name if found, None otherwise
    """
    for name, id in STOCK_MARKETS.items():
        if id == market_id:
            return name
    return None

def get_all_markets():
    """
    Get all stock markets as a list of tuples (name, id).
    
    Returns:
        list: List of tuples containing (market_name, market_id)
    """
    return [(name, market_id) for name, market_id in STOCK_MARKETS.items()]

def get_market_choices():
    """
    Get market choices formatted for Django forms.
    
    Returns:
        list: List of tuples for Django form choices
    """
    return [(market_id, f"{name} ({market_id})") for name, market_id in STOCK_MARKETS.items()]

def search_markets(query):
    """
    Search for markets by name or ID.
    
    Args:
        query (str): Search query
        
    Returns:
        list: List of matching markets as tuples (name, id)
    """
    query = query.lower()
    results = []
    
    for name, market_id in STOCK_MARKETS.items():
        if query in name.lower() or query in market_id.lower():
            results.append((name, market_id))
    
    return results
