import urllib.request
import json

# Check Rubel Ahmed search
url1 = "http://localhost:8000/api/drivers/search?q=6900883581"
try:
    req = urllib.request.urlopen(url1)
    res = json.loads(req.read().decode())
    print("Search 6900883581 in drivers:", res)
except Exception as e:
    print("Driver search error:", e)

# Check Operator 1 fleet summary
url2 = "http://localhost:8000/api/operators/1/fleet-summary"
try:
    req = urllib.request.urlopen(url2)
    res = json.loads(req.read().decode())
    print("Operator 1 vehicles count:", len(res.get('vehicles', [])))
    print("Operator 1 to_pay:", res.get('to_pay'), "to_collect:", res.get('to_collect'))
    print("Sample vehicle:", res.get('vehicles', [])[0] if res.get('vehicles') else None)
except Exception as e:
    print("Fleet summary error:", e)

