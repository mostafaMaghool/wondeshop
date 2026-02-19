class InsufficientStockError(Exception):
    # requested and available parameters are amounts
    def __init__(self, product_id, requested, available):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}: "
            f"requested={requested}, available={available}"
        )
