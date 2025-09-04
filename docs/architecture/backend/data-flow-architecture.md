# Data Flow Architecture

## 1. Authentication Flow
```
credentials.json → Service Account → Google Sheets API → Authorized Access
```

## 2. Data Retrieval Flow
```
API Request → Sheet Range → Raw Values → DataFrame Conversion → Return
```

## 3. Calculation Flow
```
DataFrame → Column Extraction → Type Conversion → Formula Application → KPI Value
```

## 4. Error Handling Flow
```
Exception → Log Error → Return None → Frontend Shows "Data Unavailable"
```
