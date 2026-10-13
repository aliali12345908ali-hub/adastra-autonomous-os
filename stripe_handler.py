import os
import stripe

# تحميل المفتاح من المتغيرات البيئية لضمان الأمان
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(amount, currency="usd", product_name="Adastra OS Service"):
    """إنشاء جلسة دفع Stripe"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': product_name,
                    },
                    'unit_amount': amount,  # المبلغ بالسنت (مثلاً 1000 = $10.00)
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )
        return session.url
    except Exception as e:
        print(f"Error creating session: {e}")
        return None

if __name__ == "__main__":
    print("Stripe Handler Loaded Successfully.")
