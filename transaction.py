from orderside import OrderSide


class Transaction:
    def __init__(self, symbol: str, side: OrderSide, qty: int, price: float):
        self.symbol = symbol
        self.side = side
        self.qty = qty
        self.price = price
