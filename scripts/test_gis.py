import requests

url = 'https://services2.arcgis.com/1UvBaQ5y1ubjUPmd/arcgis/rest/services/Tax_Parcels/FeatureServer/0/query'
params = {
    'where': "Site_Address LIKE '%PINE ST%'",
    'outFields': 'TaxParcelNumber,Site_Address,Business_Name,Land_Value,Improvement_Value,Taxable_Value,Landuse_Description',
    'resultRecordCount': 3,
    'f': 'json'
}
r = requests.get(url, params=params)
print('Status:', r.status_code)
features = r.json().get('features', [])
for f in features:
    print(f['attributes'])
