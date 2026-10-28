import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

if not stripe.api_key:
    raise SystemExit("Missing STRIPE_SECRET_KEY; no Stripe request sent.")

try:
    products = stripe.Product.list(limit=5)
    print("Products found:")
    for p in products.data:
        print(f"Name: {p.name} | ID: {p.id}")
except Exception as e:
    print(f"Error: {e}")
