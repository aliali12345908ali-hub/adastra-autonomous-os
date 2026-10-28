import stripe

stripe.api_key = "sk_test_مفتاحك_السري_هنا"

try:
    products = stripe.Product.list(limit=5)
    print("Products found:")
    for p in products.data:
        print(f"Name: {p.name} | ID: {p.id}")
except Exception as e:
    print(f"Error: {e}")
