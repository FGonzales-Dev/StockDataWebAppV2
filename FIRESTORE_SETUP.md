# Firestore Storage Setup Guide

This guide explains how to migrate from Firebase Realtime Database to Firestore for your stock scraper application.

## 🎯 **What This Does**

Instead of using Firebase Realtime Database, your app will now:

1. **Check Firestore first** for existing data (ticker + market combination)
2. **Return existing data** if found (no scraping needed)
3. **Scrape only if data doesn't exist** in Firestore
4. **Store new data** in Firestore for future use

## 🚀 **Benefits**

- **Faster responses** - No unnecessary scraping
- **Better queries** - Compound queries on ticker + market + data_type
- **Structured storage** - Better organization than flat JSON
- **Cost effective** - Pay per operation, not bandwidth
- **Scalable** - Handles large datasets efficiently

## 📋 **Setup Steps**

### 1. **Get Firebase Service Account Key**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `scraper-b0a07`
3. Go to **Project Settings** > **Service Accounts**
4. Click **Generate New Private Key**
5. Download the JSON file

### 2. **Update Firestore Storage Configuration**

Edit `core/firestore_storage.py` and replace the credentials section:

```python
# Replace this section in firestore_storage.py
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "scraper-b0a07",
    "private_key_id": "your_private_key_id",        # From downloaded JSON
    "private_key": "your_private_key",              # From downloaded JSON  
    "client_email": "your_client_email",            # From downloaded JSON
    "client_id": "your_client_id",                  # From downloaded JSON
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "your_cert_url"        # From downloaded JSON
})

# OR use the JSON file directly:
cred = credentials.Certificate("path/to/your/serviceAccount.json")
```

### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 4. **Test the Setup**

```python
# Test Firestore connection
from core.firestore_storage import get_storage

storage = get_storage()
stats = storage.get_storage_stats()
print("Firestore connected successfully:", stats)
```

## 🔧 **Usage**

### **Option 1: Use New Firestore Endpoints**

```bash
# Main Firestore interface (checks first, scrapes if needed)
http://127.0.0.1:8000/firestore/

# Check what data exists for a stock
http://127.0.0.1:8000/firestore/check_status/?ticker=AAPL&market=XNAS

# Get storage statistics
http://127.0.0.1:8000/firestore/storage_stats/

# Direct API endpoint
curl -X POST http://127.0.0.1:8000/firestore/direct/ \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "market": "XNAS", "data_type": "INCOME_STATEMENT"}'
```

### **Option 2: Update Existing Code**

Replace your existing scraper imports:

```python
# OLD
from .tasks_optimized import scraper_optimized

# NEW  
from .tasks_firestore import scraper_firestore

# Usage remains the same
task = scraper_firestore.delay(ticker, market, data_type)
```

## 📊 **Data Structure in Firestore**

Each document in the `stock_data` collection:

```json
{
  "ticker": "AAPL",
  "market": "XNAS", 
  "data_type": "INCOME_STATEMENT",
  "data": "...scraped JSON data...",
  "scraped_at": "2024-01-15T10:30:00Z",
  "status": "DONE"
}
```

Document ID format: `{TICKER}_{MARKET}_{DATA_TYPE}`
Example: `AAPL_XNAS_INCOME_STATEMENT`

## 🔍 **Check Existing Data**

```python
from core.firestore_storage import get_storage, DataType

storage = get_storage()

# Check if specific data exists
existing = storage.check_data_exists("AAPL", "XNAS", DataType.INCOME_STATEMENT)
if existing:
    print("Data exists:", existing['scraped_at'])
else:
    print("Need to scrape")

# Get all data for a stock
all_data = storage.get_all_data_for_stock("AAPL", "XNAS")
print(f"Found {len(all_data)} data types for AAPL")
```

## 🔄 **Migration Strategy**

### **Gradual Migration (Recommended)**

1. **Keep existing endpoints** working with Realtime DB
2. **Use new `/firestore/` endpoints** for new requests
3. **Gradually migrate** users to new endpoints
4. **Eventually deprecate** old endpoints

### **Full Migration**

1. **Export existing data** from Realtime DB
2. **Import to Firestore** using the new structure
3. **Update all endpoints** to use Firestore
4. **Remove Realtime DB** dependencies

## 🚨 **Important Notes**

1. **Service Account Security**: Keep your service account JSON file secure and never commit it to version control

2. **Firestore Rules**: Set up appropriate security rules in Firebase Console:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /stock_data/{document} {
         allow read, write: if request.auth != null;
       }
     }
   }
   ```

3. **Indexing**: Firestore will automatically create indexes for your queries. Monitor the Firebase Console for any required composite indexes.

4. **Costs**: Firestore charges per operation. With the check-first approach, you'll save money by avoiding unnecessary scraping.

## 🎉 **You're Ready!**

Your stock scraper now uses Firestore with a smart check-first approach:

- ✅ **Checks existing data** before scraping
- ✅ **Fast compound queries** on ticker + market + data_type  
- ✅ **Structured storage** for better organization
- ✅ **Backward compatible** with existing code
- ✅ **Cost effective** - no unnecessary scraping

Visit `http://127.0.0.1:8000/firestore/` to start using the new system! 