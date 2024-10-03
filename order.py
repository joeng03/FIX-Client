import quickfix as fix
from ordertype import OrderType
from orderside import OrderSide
from typing import Optional
import datetime
import uuid

class OrderMessageBase:
    def generate_fix_order_id(self):
        # Generate a unique identifier
        unique_id = str(uuid.uuid4())
        # Get the current date
        current_date = datetime.date.today()
        # Format the date as YYYYMMDD
        date_str = current_date.strftime("%Y%m%d")
        # Generate a sequence number
        sequence_number = str(uuid.uuid4().int)[:6]
        # Combine the components to form the FIX order ID
        fix_order_id = f"ORD-{date_str}-{unique_id[:10]}-{sequence_number}"

        return fix_order_id
    
class OrderMessage(OrderMessageBase):
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        qty: int,
        order_type: OrderType,
        price: Optional[float] = None,
    ):

        if type == OrderType.LIMIT and price is None:
            raise ValueError("Price must be provided for limit orders")

        self.orderID = self.generate_fix_order_id()

        msg = fix.Message()
        msg.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))
        msg.getHeader().setField(fix.StringField(60,(datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))
        msg.setField(fix.ClOrdID(self.orderID))
        msg.setField(fix.Symbol(symbol))
        msg.setField(fix.OrdType(order_type))
        msg.setField(fix.OrderQty(qty))
        msg.setField(fix.Side(side))
        msg.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION))
        if type == OrderType.LIMIT:
            msg.setField(fix.Price(price))

        self.msg = msg


class OrderCancelRequest(OrderMessageBase):
    def __init__(self,
        origClOrdID: str,         
        symbol: str,
        side: OrderSide,
        qty: int,
    ):
        self.orderID = self.generate_fix_order_id()

        msg = fix.Message()
        msg.getHeader().setField(fix.MsgType(fix.MsgType_OrderCancelRequest))
        msg.getHeader().setField(fix.StringField(60,(datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))
        msg.setField(fix.ClOrdID(self.orderID))
        msg.setField(fix.OrigClOrdID(origClOrdID))  # Original order ID to cancel
        msg.setField(fix.Symbol(symbol))
        msg.setField(fix.Side(side))
        msg.setField(fix.OrderQty(qty))

        self.msg = msg

