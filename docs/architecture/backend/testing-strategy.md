# Testing Strategy

## Manual Validation Points
1. **Connection Test:**
   ```python
   reader = SheetsReader()
   df = reader.get_sheet_data('EOD - Baytown Billing!A1:N10')
   assert df is not None
   ```

2. **Calculation Test:**
   ```python
   test_df = pd.DataFrame({
       'total_production': [1000, 2000, 3000],
       'total_collections': [900, 1800, 2700]
   })
   rate = calculate_collection_rate(test_df)
   assert rate == 90.0  # (5400/6000) * 100
   ```

3. **Integration Test:**
   ```python
   kpis = get_all_kpis()
   assert all(key in kpis for key in [
       'production_total', 'collection_rate', 
       'new_patients', 'treatment_acceptance', 
       'hygiene_reappointment'
   ])
   ```
