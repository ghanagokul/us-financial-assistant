import requests

def get_investment_advice(payload):
    res = requests.post("http://localhost:5000/invest", json=payload)
    return res.json().get("response", "No response received.")
