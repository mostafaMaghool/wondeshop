class PaymentGatewayService:
    """
    Responsible for talking to external payment provider,
     like shaparak and other bank payment services
    """

    @staticmethod
    def verify(transaction_id):
        """
        Call real gateway verify endpoint.
        Replace URL and payload with real gateway data.
        """

        # TODO fake verification (replace with real request later,
        #  by connecting to the PSP service)
        response_data = {
            "transaction_id": transaction_id,
            "status": "success",  # success / failed
        }

        return response_data
