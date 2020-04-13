To generate a list which can be pasted into Google Maps as a CSV:

```
curl "https://lots.impark.com/IMP/EN?latlng=37.77038390870099,-122.4192867539673&zoom=14&_ga=2.8431733.1721953865.1560835651-924525142.1560482923" > impark_list.html

# Was easier to copy-paste it from the web-browser into impark_list.txt
less impark_list.txt  | grep -v '\$' | grep -v mi | grep -v 'Lot Details' | grep -v '[0-2]\.' | grep -v 'Lot #' | grep -v 'hourly' | grep -v 'RATES' | grep -v 'Monthly' | grep ...... | sort | uniq | grep -v rates
```
