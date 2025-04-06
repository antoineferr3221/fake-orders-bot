from flask import Flask
import requests
import random
import json
import faker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
fake = faker.Faker('fr_FR')

# 🔐 Variables d'environnement
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
VARIANT_ID = 54597229150532
PRODUCT_PRICE = 49.95

# Objectif de chiffre d'affaires journalier
MIN_DAILY_REVENUE = 2500
MAX_DAILY_REVENUE = 4500

def generate_order():
    email = fake.first_name().lower() + str(random.randint(100, 999)) + "@gmail.com"
    quantity = random.choice([1, 2, 3])
    total = quantity * PRODUCT_PRICE

    data = {
        "order": {
            "email": email,
            "financial_status": "paid",
            "fulfillment_status": "unfulfilled",
            "line_items": [{
                "variant_id": VARIANT_ID,
                "quantity": quantity
            }]
        }
    }

    response = requests.post(
        f"{SHOPIFY_STORE_URL}/admin/api/2024-01/orders.json",
        auth=(SHOPIFY_API_KEY, SHOPIFY_PASSWORD),
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )

    now = datetime.now().strftime("%H:%M:%S")
    if response.status_code == 201:
        print(f"[{now}] ✅ Commande : {email} ({quantity}) = {total:.2f}€")
        return total
    else:
        print(f"[{now}] ❌ Erreur : {response.json()}")
        return 0

@app.route("/")
def index():
    return "✅ Bot de commandes en ligne."

@app.route("/run")
def run_bot():
    total = 0
    objectif = random.randint(MIN_DAILY_REVENUE, MAX_DAILY_REVENUE)
    print(f"🎯 Objectif : {objectif}€")
    while total < objectif:
        total += generate_order()
    return f"🔥 {total:.2f}€ générés aujourd'hui !"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


