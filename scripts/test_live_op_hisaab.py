import urllib.request
import json

url = "http://localhost:8000/api/hisaabs/operator/475"
req = urllib.request.urlopen(url)
data = json.loads(req.read().decode())
print("Operator 475 aggregate hisaabs count:", data.get('count'))
for h in data.get('data', [])[:3]:
    print("  Week", h['week_number'], h['hisaab_number'], "Trips:", h['completed_trips'], "Gross:", h['total_gross_earnings'], "To Pay:", h['to_pay'], "To Collect:", h['to_collect'])
