from flask import Flask
import requests
import random
import json
import faker
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
fake = faker.Faker("fr_FR")

# Config Shopify (depuis .env)
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
VARIANT_ID = 54597229150532
PRODUCT_PRICE = 49.95
PANIER_MOYEN = 60

# Objectifs journaliers
MIN_CA = 2500
MAX_CA = 4500

# Fichier où stocker l'avancement journalier
STORAGE_FILE = "ca_journalier.json"


def get_now_fr():
    """Retourne l'heure actuelle en France"""
    utc_now = datetime.utcnow()
    france_time = utc_now + timedelta(hours=2)  # UTC+2
    return france_time


def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {"date": "", "total": 0, "objectif": 0}
    with open(STORAGE_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f)


def reset_if_new_day(data):
    today_str = get_now_fr().strftime("%Y-%m-%d")
    if data["date"] != today_str:
        data["date"] = today_str
        data["total"] = 0
        data["objectif"] = random.randint(MIN_CA, MAX_CA)
        save_data(data)
        print(f"🔁 Nouveau jour : objectif = {data['objectif']}€")
    return data


def generate_order():
    email = fake.first_name().lower() + str(random.randint(100, 999)) + "@gmail.com"
    quantity = random.choice([1, 2])
    total = quantity * PRODUCT_PRICE

    data = {
        "order": {
            "email": email,
            "financial_status": "paid",
            "fulfillment_status": "unfulfilled",
            "line_items": [{"variant_id": VARIANT_ID, "quantity": quantity}]
        }
    }

    response = requests.post(
        f"{SHOPIFY_STORE_URL}/admin/api/2024-01/orders.json",
        auth=(SHOPIFY_API_KEY, SHOPIFY_PASSWORD),
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )

    now = get_now_fr().strftime("%H:%M:%S")
    if response.status_code == 201:
        print(f"[{now}] ✅ Commande : {email} ({quantity}) = {total:.2f}€")
        return total
    else:
        print(f"[{now}] ❌ Erreur Shopify : {response.json()}")
        return 0


@app.route("/")
def home():
    return "🚀 Bot de commandes actif."


@app.route("/run")
def run():
    now = get_now_fr()
    heure = now.hour

    if heure < 7 or heure >= 24:
        return "🛑 En dehors des horaires autorisés."

    data = load_data()
    data = reset_if_new_day(data)

    if data["total"] >= data["objectif"]:
        return f"✅ Objectif atteint : {data['total']:.2f}€ / {data['objectif']}€"

    # Probabilité d'achat (1 chance sur 2 par appel)
    if random.random() < 0.5:
        montant = generate_order()
        data["total"] += montant
        save_data(data)
        return f"🛒 Commande OK | Total : {data['total']:.2f}€ / {data['objectif']}€"
    else:
        return f"🔁 Pas de commande cette fois. Total : {data['total']:.2f}€ / {data['objectif']}€"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
