import requests
from django.conf import settings
from store.models import Payment, Order

def create_crypto_payment(order_id, user):
    order = Order.objects.get(id=order_id, user=user)

    payload = {
        "price_amount": str(order.total_amount),
        "price_currency": "usd",
        "pay_currency": "usdttrc20",
        "ipn_callback_url": settings.NOWPAYMENTS_WEBHOOK_URL
    }

    headers = {
        "x-api-key": settings.NOWPAYMENTS_API_KEY
    }

    response = requests.post(
        "https://api.nowpayments.io/v1/payment",
        json=payload,
        headers=headers
    )

    data = response.json()

    payment = Payment.objects.create(
        order=order,
        user=user,
        payment_id=data["payment_id"],
        pay_address=data["pay_address"],
        pay_currency=data["pay_currency"],
        price_amount=order.total_amount,
        pay_amount=data["pay_amount"],
        status=data["payment_status"]
    )

    return payment