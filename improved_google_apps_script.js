function ImportStockHistory(url, market, type, query, parseOptions) {
  // Set default values to prevent parameter errors
  if (!query) query = "";
  if (!parseOptions) parseOptions = "parseNumbers";
  
  return ImportJSONAdvancedImportStockHistory(url, market, type, null, query, parseOptions, includeXPath_, defaultTransform_);
}

function ImportStockHistoryKeyRatio(url, market, query, parseOptions) {
  return ImportJSONAdvancedImportStockHistoryKeyRatio(url, market, null, query, "parseNumbers", includeXPath_, defaultTransform_);
}

function ImportJSONHeader(url, data_param, query, parseOptions) {
  return ImportJSONAdvanced(url, data_param, null, query, parseOptions, includeXPath_, defaultTransform_);
}

function ImportJSON(url, data_param, query) {
  return ImportJSONNoHeader(url, data_param, null, query, "noHeaders", includeXPath_, defaultTransform_);
}

function ImportJSONAdvancedImportStockHistoryKeyRatio(url, market, fetchOptions, query, parseOptions, includeFunc, transformFunc) {
  var jsondata = UrlFetchApp.fetch("https://ancient-dawn-83050.herokuapp.com/stock_history_key_ratio_json?ticker=" + url + "&market=" + market, fetchOptions);
  var object = JSON.parse(jsondata.getContentText());
  return parseJSONObject_(object, query, parseOptions, includeFunc, transformFunc);
}

// OPTIMIZED VERSION FOR GOOGLE SHEETS TIMEOUT LIMITS
function ImportJSONAdvancedImportStockHistory(url, market, type, fetchOptions, query, parseOptions, includeFunc, transformFunc) {
  var startTime = new Date();
  var maxExecutionTime = 240000; // 4 minutes (240 seconds) - leave room for processing
  
  try {
    console.log("Starting data fetch for " + url + " (" + type + ") at " + startTime);
    
    // Set fetch options optimized for Google Sheets
    var options = {
      'muteHttpExceptions': true,
      'method': 'GET',
      'headers': {
        'User-Agent': 'GoogleSheets/1.0',
        'Accept': 'application/json'
      }
    };
    
    // Merge with any existing fetchOptions
    if (fetchOptions) {
      Object.keys(fetchOptions).forEach(function(key) {
        options[key] = fetchOptions[key];
      });
    }
    
    var apiUrl = "YOUR_DOMAIN_HERE/financial-statements-json?ticker=" + url + "&market=" + market + "&type=" + type;
    console.log("Making API request to: " + apiUrl);
    
    // Single attempt with timeout handling - no retries to avoid script timeout
    var jsondata = UrlFetchApp.fetch(apiUrl, options);
    
    // Check execution time
    var currentTime = new Date();
    var elapsedTime = currentTime - startTime;
    console.log("API response received after " + (elapsedTime/1000) + " seconds");
    
    if (elapsedTime > maxExecutionTime) {
      throw new Error("EXECUTION_TIMEOUT: Request took too long");
    }
    
    // Check response status
    var responseCode = jsondata.getResponseCode();
    if (responseCode !== 200) {
      throw new Error("HTTP " + responseCode + ": " + jsondata.getContentText());
    }
    
    var responseText = jsondata.getContentText();
    
    // Handle API timeout responses
    if (responseText.indexOf('"error"') !== -1) {
      var errorObj = JSON.parse(responseText);
      if (errorObj.error && errorObj.error.indexOf('timeout') !== -1) {
        return [
          ["Status", "Message", "Action"],
          ["API_BUSY", "Server is processing your request", "Wait 2-3 minutes, then try again"],
          ["Tip", "Use =checkAPIStatus() first", "Check if server is ready"]
        ];
      } else {
        return [
          ["Error", "Details"],
          ["API_ERROR", errorObj.error || "Unknown API error"]
        ];
      }
    }
    
    // Parse successful response
    var object = JSON.parse(responseText);
    console.log("Data parsed successfully for " + url);
    
    // Check execution time before processing
    currentTime = new Date();
    elapsedTime = currentTime - startTime;
    
    if (elapsedTime > maxExecutionTime * 0.9) { // 90% of max time
      console.log("Warning: Close to execution time limit, processing quickly");
    }
    
    return parseJSONObject_(object, query, parseOptions, includeFunc, transformFunc);
    
  } catch (error) {
    var errorString = error.toString();
    console.log("Error occurred: " + errorString);
    
    // Return user-friendly errors in spreadsheet format
    if (errorString.indexOf('Exceeded maximum execution time') !== -1 || 
        errorString.indexOf('EXECUTION_TIMEOUT') !== -1) {
      return [
        ["Error", "Solution"],
        ["TIMEOUT", "Google Sheets timeout - try these steps:"],
        ["Step 1", "Wait 3-5 minutes before trying again"],
        ["Step 2", "Use =checkAPIStatusFast() to check server"],
        ["Step 3", "Try =ImportStockHistoryFast() instead"],
        ["Note", "First request for a stock takes longest"]
      ];
    } else if (errorString.indexOf('timeout') !== -1 || errorString.indexOf('API_BUSY') !== -1) {
      return [
        ["Status", "Action"],
        ["SERVER_BUSY", "API is processing data for this stock"],
        ["Wait", "2-3 minutes then try again"],
        ["Check", "Use =checkAPIStatusFast() first"]
      ];
    } else {
      return [
        ["Error", "Details"],
        ["UNKNOWN", errorString.substring(0, 100)]
      ];
    }
  }
}

// FAST VERSION - Attempts quick fetch, fails fast if data not ready
function ImportStockHistoryFast(url, market, type, query, parseOptions) {
  try {
    // Set default values
    if (!query) query = "";
    if (!parseOptions) parseOptions = "parseNumbers";
    
    console.log("Fast fetch attempt for " + url + " (" + type + ")");
    
    var options = {
      'muteHttpExceptions': true,
      'method': 'GET',
      'headers': {'User-Agent': 'GoogleSheets/Fast/1.0'}
    };
    
    var apiUrl = "YOUR_DOMAIN_HERE/financial-statements-json?ticker=" + url + "&market=" + market + "&type=" + type;
    var jsondata = UrlFetchApp.fetch(apiUrl, options);
    
    var responseCode = jsondata.getResponseCode();
    var responseText = jsondata.getContentText();
    
    if (responseCode !== 200) {
      return [["Status", "Action"], ["ERROR", "HTTP " + responseCode], ["Try", "Use regular ImportStockHistory()"]];
    }
    
    // Quick check for errors
    if (responseText.indexOf('"error"') !== -1) {
      return [
        ["Status", "Action"],
        ["NOT_READY", "Data still being processed"],
        ["Wait", "Use =checkAPIStatusFast() then try again"],
        ["Alternative", "Use =ImportStockHistory() for full wait"]
      ];
    }
    
    // Parse and return data
    var object = JSON.parse(responseText);
    return parseJSONObject_(object, query, parseOptions, includeXPath_, defaultTransform_);
    
  } catch (error) {
    return [
      ["Error", "Solution"],
      ["FAST_FAIL", error.toString().substring(0, 50)],
      ["Try", "Use =ImportStockHistory() instead"]
    ];
  }
}

// QUICK API STATUS CHECK
function checkAPIStatusFast() {
  try {
    var response = UrlFetchApp.fetch("YOUR_DOMAIN_HERE/financial-statements-json?ticker=AAPL&market=XNAS&type=is", {
      'muteHttpExceptions': true,
      'method': 'GET'
    });
    
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    if (responseCode === 200 && responseText.indexOf('"error"') === -1) {
      return [["Status", "Action"], ["READY", "API working - you can import data"], ["Go", "Use ImportStockHistory() or ImportStockHistoryFast()"]];
    } else if (responseText.indexOf('timeout') !== -1) {
      return [["Status", "Action"], ["BUSY", "Server processing - wait 2-3 minutes"], ["Then", "Try this function again"]];
    } else {
      return [["Status", "Details"], ["ISSUE", responseText.substring(0, 100)]];
    }
  } catch (error) {
    return [["Status", "Error"], ["FAILED", error.toString().substring(0, 100)]];
  }
}

// ORIGINAL API STATUS CHECK (DETAILED)
function checkAPIStatus() {
  try {
    var response = UrlFetchApp.fetch("YOUR_DOMAIN_HERE/financial-statements-json?ticker=AAPL&market=XNAS&type=is", {
      'muteHttpExceptions': true,
      'method': 'GET'
    });
    
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    console.log("API Status Check:");
    console.log("Response Code: " + responseCode);
    console.log("Response Preview: " + responseText.substring(0, 200) + "...");
    
    if (responseCode === 200 && responseText.indexOf('"error"') === -1) {
      return "API is working correctly";
    } else {
      return "API returned error: " + responseText;
    }
  } catch (error) {
    return "API check failed: " + error.toString();
  }
}

function ImportJSONAdvanced(url, data_param, fetchOptions, query, parseOptions, includeFunc, transformFunc) {
  var jsondata = UrlFetchApp.fetch("https://ancient-dawn-83050.herokuapp.com/stock/" + data_param + "/?ticker=" + url, fetchOptions);
  var object = JSON.parse(jsondata.getContentText());
  return parseJSONObject_(object, query, parseOptions, includeFunc, transformFunc);
}

function ImportJSONNoHeader(url, data_param, fetchOptions, query, parseOptions, includeFunc, transformFunc) {
  var jsondata = UrlFetchApp.fetch("https://ancient-dawn-83050.herokuapp.com/stock/" + data_param + "/?ticker=" + url, fetchOptions);
  var object = JSON.parse(jsondata.getContentText());
  return parseJSONObject_(object, query, parseOptions, includeFunc, transformFunc);
}

/** 
 * Parses a JSON object and returns a two-dimensional array containing the data of that object.
 */
function parseJSONObject_(object, query, options, includeFunc, transformFunc) {
  var headers = new Array();
  var data = new Array();
  
  if (query && !Array.isArray(query) && query.toString().indexOf(",") != -1) {
    query = query.toString().split(",");
  }

  // Prepopulate the headers to lock in their order
  if (hasOption_(options, "allHeaders") && Array.isArray(query)) {
    for (var i = 0; i < query.length; i++) {
      headers[query[i]] = Object.keys(headers).length;
    }
  }
  
  if (options) {
    options = options.toString().split(",");
  }
    
  parseData_(headers, data, "", {rowIndex: 1}, object, query, options, includeFunc);
  parseHeaders_(headers, data);
  transformData_(data, options, transformFunc);
  
  return hasOption_(options, "noHeaders") ? (data.length > 1 ? data.slice(1) : new Array()) : data;
}

function parseData_(headers, data, path, state, value, query, options, includeFunc) {
  var dataInserted = false;

  if (Array.isArray(value) && isObjectArray_(value)) {
    for (var i = 0; i < value.length; i++) {
      if (parseData_(headers, data, path, state, value[i], query, options, includeFunc)) {
        dataInserted = true;

        if (data[state.rowIndex]) {
          state.rowIndex++;
        }
      }
    }
  } else if (isObject_(value)) {
    for (key in value) {
      if (parseData_(headers, data, path + "/" + key, state, value[key], query, options, includeFunc)) {
        dataInserted = true; 
      }
    }
  } else if (!includeFunc || includeFunc(query, path, options)) {
    // Handle arrays containing only scalar values
    if (Array.isArray(value)) {
      value = value.join(); 
    }
    
    // Insert new row if one doesn't already exist
    if (!data[state.rowIndex]) {
      data[state.rowIndex] = new Array();
    }
    
    // Add a new header if one doesn't exist
    if (!headers[path] && headers[path] != 0) {
      headers[path] = Object.keys(headers).length;
    }
    
    // Insert the data
    data[state.rowIndex][headers[path]] = value;
    dataInserted = true;
  }
  
  return dataInserted;
}

function parseHeaders_(headers, data) {
  data[0] = new Array();

  for (key in headers) {
    data[0][headers[key]] = key;
  }
}

function transformData_(data, options, transformFunc) {
  for (var i = 0; i < data.length; i++) {
    for (var j = 0; j < data[0].length; j++) {
      transformFunc(data, i, j, options);
    }
  }
}

function isObject_(test) {
  return Object.prototype.toString.call(test) === '[object Object]';
}

/** 
 * Returns true if the given test value is an array containing at least one object; false otherwise.
 */
function isObjectArray_(test) {
  for (var i = 0; i < test.length; i++) {
    if (isObject_(test[i])) {
      return true; 
    }
  }  

  return false;
}

/** 
 * Returns true if the given query applies to the given path. 
 */
function includeXPath_(query, path, options) {
  if (!query) {
    return true; 
  } else if (Array.isArray(query)) {
    for (var i = 0; i < query.length; i++) {
      if (applyXPathRule_(query[i], path, options)) {
        return true; 
      }
    }  
  } else {
    return applyXPathRule_(query, path, options);
  }
  
  return false; 
};

/** 
 * Returns true if the rule applies to the given path. 
 */
function applyXPathRule_(rule, path, options) {
  return path.indexOf(rule) == 0; 
}

function defaultTransform_(data, row, column, options) {
  if (data[row][column] == null) {
    if (row < 2 || hasOption_(options, "noInherit")) {
      data[row][column] = "";
    } else {
      data[row][column] = data[row-1][column];
    }
  } 

  if (!hasOption_(options, "rawHeaders") && row == 0) {
    if (column == 0 && data[row].length > 1) {
      removeCommonPrefixes_(data, row);  
    }
    
    data[row][column] = toTitleCase_(data[row][column].toString().replace(/[\/\_]/g, " "));
  }
  
   if (!hasOption_(options, "noTruncate") && data[row][column]) {
    if ((typeof data[row][column]) === 'number' || (typeof data[row][column]) === 'boolean') {
      data[row][column] = data[row][column];
    } else {
      data[row][column] = data[row][column].toString().substr(0, 256);
    }
  }

  if (hasOption_(options, "debugLocation")) {
    data[row][column] = "[" + row + "," + column + "]" + data[row][column];
  }

  if (hasOption_(options, "parseNumbers")) {
    var num = filterFloat(data[row][column]);
    if (!isNaN(num)) {
      data[row][column] = num;
    }
  }
}

function filterFloat(value) {
  if(/^(-|\+)?([0-9]+(.[0-9]+)?|Infinity)$/.test(value)) {
    return Number(value);
  }
  return NaN;
}

/** 
 * If all the values in the given row share the same prefix, remove that prefix.
 */
function removeCommonPrefixes_(data, row) {
  var matchIndex = data[row][0].length;

  for (var i = 1; i < data[row].length; i++) {
    matchIndex = findEqualityEndpoint_(data[row][i-1], data[row][i], matchIndex);

    if (matchIndex == 0) {
      return;
    }
  }
  
  for (var i = 0; i < data[row].length; i++) {
    data[row][i] = data[row][i].substring(matchIndex, data[row][i].length);
  }
}

/** 
 * Locates the index where the two strings values stop being equal, stopping automatically at the stopAt index.
 */
function findEqualityEndpoint_(string1, string2, stopAt) {
  if (!string1 || !string2) {
    return -1; 
  }
  
  var maxEndpoint = Math.min(stopAt, string1.length, string2.length);
  
  for (var i = 0; i < maxEndpoint; i++) {
    if (string1.charAt(i) != string2.charAt(i)) {
      return i;
    }
  }
  
  return maxEndpoint;
}

/** 
 * Converts the text to title case.
 */
function toTitleCase_(text) {
  if (text == null) {
    return null;
  }
  
  return text.replace(/\w\S*/g, function(word) { return word.charAt(0).toUpperCase() + word.substr(1).toLowerCase(); });
}

/** 
 * Returns true if the given set of options contains the given option.
 */
function hasOption_(options, option) {
  return options && options.indexOf(option) >= 0;
}

/** 
 * Parses the given string into an object, trimming any leading or trailing spaces from the keys.
 */
function parseToObject_(text) {
  var map = new Object();
  var entries = (text != null && text.trim().length > 0) ? text.toString().split(",") : new Array();
  
  for (var i = 0; i < entries.length; i++) {
    addToMap_(map, entries[i]);  
  }
  
  return map;
}

/** 
 * Parses the given entry and adds it to the given map, trimming any leading or trailing spaces from the key.
 */
function addToMap_(map, entry) {
  var equalsIndex = entry.indexOf("=");  
  var key = (equalsIndex != -1) ? entry.substring(0, equalsIndex) : entry;
  var value = (key.length + 1 < entry.length) ? entry.substring(key.length + 1) : "";
  
  map[key.trim()] = value;
}

/** 
 * Returns the given value as a boolean.
 */
function toBool_(value) {
  return value == null ? false : (value.toString().toLowerCase() == "true" ? true : false);
}

/**
 * Converts the value for the given key in the given map to a bool.
 */
function convertToBool_(map, key) {
  if (map[key] != null) {
    map[key] = toBool_(map[key]);
  }  
}

function getDataFromNamedSheet_(sheetName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var source = ss.getSheetByName(sheetName);
  
  var jsonRange = source.getRange(1,1,source.getLastRow());
  var jsonValues = jsonRange.getValues();
  
  var jsonText = "";
  for (var row in jsonValues) {
    for (var col in jsonValues[row]) {
      jsonText +=jsonValues[row][col];
    }
  }
  Logger.log(jsonText);
  return JSON.parse(jsonText);
} 