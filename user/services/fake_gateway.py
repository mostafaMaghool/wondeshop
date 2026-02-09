import uuid
from random import random


class FakePaymentGateway:
    """
    Simulates an external payment provider
    """

    @staticmethod
    def initiate(amount):
        # user is now supposed to be directed to gateway
        return {
            "transaction_id": str(uuid.uuid4()),
            "gateway_url": "https://fake-gateway/pay",
            "amount": amount,
        }

    @staticmethod
    def verify(transaction_id):
        # the gateway response, or callback verification
        return {
            "transaction_id": transaction_id,
            "success": random.choice([True, True, False]),
        }
