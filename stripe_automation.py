import os
import stripe

# قراءة مفتاح الأمان من متغيرات البيئة لحمايته على GitHub
stripe.api_key = os.environ.get("STRIPE_API_KEY")

try:
    print("جاري إنشاء العميل...")
    customer = stripe.Customer.create(
        email="client@example.com",
        name="John Doe"
    )
    print(f"Success! Customer ID: {customer.id}")
    
    print("جاري إنشاء المنتج...")
    product = stripe.Product.create(
        name="Termux Premium Package", 
        description="Customized payment bundle"
    )
    print(f"Success! Product ID: {product.id}")
    
    print("جاري إنشاء السعر...")
    price = stripe.Price.create(
        product=product.id, 
        unit_amount=2500, 
        currency="usd"
    )
    print(f"Success! Price ID: {price.id}")
    
    print("جاري إنشاء رابط الدفع...")
    payment_link = stripe.PaymentLink.create(
        line_items=[{"price": price.id, "quantity": 1}],
        allow_promotion_codes=True
    )
    print(f"Success! Custom Payment Link: {payment_link.url}")

except Exception as e:
    print(f"Error: {e}")
