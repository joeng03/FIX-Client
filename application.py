import random
import time
import threading
from datetime import datetime
import quickfix as fix
from order import OrderMessage, OrderCancelRequest
from ordertype import OrderType
from orderside import OrderSide
from transaction import Transaction
from stats import DTLTradeStats
from utils import generate_boolean_with_probability
from constants import FIX_CLIENT_WAIT_TIME

__SOH__ = chr(1)

class OrderManager:
    def __init__(self):
        self.orders_message = {}
        self.orders_qty_filled = {}
        self.orders_status = {}
        self.orders_to_cancel = set()

    def add_order(self, order_id, message, qty_filled=0, status=fix.OrdStatus_NEW):
        self.orders_message[order_id] = message
        self.orders_qty_filled[order_id] = qty_filled
        self.orders_status[order_id] = status

    def get_order_message(self, order_id):
        return self.orders_message.get(order_id)

    def get_qty_filled(self, order_id):
        return self.orders_qty_filled.get(order_id, 0)

    def set_order_status(self, order_id, status):
        self.orders_status[order_id] = status

    def mark_order_for_cancellation(self, order_id):
        self.orders_to_cancel.add(order_id)

    def create_cancel_request(self, clOrdID):
        order_message = self.get_order_message(clOrdID)
        if order_message:
            return OrderCancelRequest(
                origClOrdID=clOrdID,
                symbol=order_message.getField(fix.Symbol().getField()),
                side=order_message.getField(fix.Side().getField()),
                qty=int(order_message.getField(fix.OrderQty().getField())) - self.get_qty_filled(clOrdID),
            )
        return None

class DTLFixApplication(fix.Application):
    def __init__(self, numOrders, order_cancel_probability, order_qty, random_seed, symbols, reference_prices):
        super().__init__()
        self.random_seed = random_seed
        random.seed(random_seed)

        self.numOrders = numOrders
        self.order_cancel_probability = order_cancel_probability
        self.order_qty = order_qty

        self.order_manager = OrderManager()
        self.symbols = symbols
        self.reference_prices = reference_prices
        self.delta = 5
        self.sides = [OrderSide.BUY, OrderSide.SELL, OrderSide.SHORT]
        self.order_types = [OrderType.MARKET, OrderType.LIMIT]

        self.logon_event = threading.Event()
        self.orders_sent = 0
        self.orders_filled = 0
        self.orders_cancelled = 0
        self.trade_stats = DTLTradeStats(instruments=self.symbols)

    ### EVENT HANDLERS

    def onCreate(self, sessionID):
        print("onCreate:", sessionID)

    def onLogon(self, sessionID):
        self.sessionID = sessionID
        self.logon_event.set()
        print("onLogon:", sessionID)

    def onLogout(self, sessionID):
        print("onLogout:", sessionID)
        print("Orders sent:", self.orders_sent)
        print("Orders filled:", self.orders_filled)
        print("Orders cancelled:", self.orders_cancelled)
        self.trade_stats.summarize()

    def toAdmin(self, message, sessionID):
        print("toAdmin:", self.formatMessage(message))

    def toApp(self, message, sessionID):
        pass

    def fromAdmin(self, message, sessionID):
        print("fromAdmin:", self.formatMessage(message))

    def fromApp(self, message, sessionID):
        message_type = message.getHeader().getField(fix.MsgType().getField())
        if message_type == fix.MsgType_ExecutionReport:
            self.handle_execution_report(message)
        elif message_type == fix.MsgType_OrderCancelReject:
            self.handle_order_cancel_reject(message)
        elif message_type == fix.MsgType_Reject:
            print("This message was rejected by the server: ", self.formatMessage(message))

    def handle_execution_report(self, message):
        order_status = message.getField(fix.OrdStatus().getField())
        clOrdID = message.getField(fix.ClOrdID().getField())

        if order_status == fix.OrdStatus_NEW:
            return

        if order_status == fix.OrdStatus_CANCELED:
            self.order_manager.set_order_status(clOrdID, fix.OrdStatus_CANCELED)
            self.orders_cancelled += 1
            return

        side = message.getField(fix.Side().getField())
        symbol = message.getField(fix.Symbol().getField())

        last_shares = int(message.getField(fix.LastShares().getField()))
        last_px = float(message.getField(fix.LastPx().getField()))
        transaction = Transaction(symbol=symbol, side=side, qty=last_shares, price=last_px)
        self.trade_stats.process(transaction)
        self.order_manager.orders_qty_filled[clOrdID] += last_shares

        if order_status == fix.OrdStatus_FILLED:
            self.orders_filled += 1

    def handle_order_cancel_reject(self, message):
        origClOrdID = message.getField(fix.OrigClOrdID().getField())
        orderCancelRequest = self.order_manager.create_cancel_request(origClOrdID)
        if orderCancelRequest:
            self.cancelOrder(orderCancelRequest)

    ### UTIL FUNCTIONS

    def formatMessage(self, message):
        return message.toString().replace(__SOH__, "|")

    def create_order_message(self):
        order_type = random.choice(self.order_types)
        symbol = random.choice(self.symbols)
        side = random.choice(self.sides)
        return OrderMessage(
            symbol=symbol,
            side=side,
            qty=self.order_qty,
            order_type=order_type,
            price=random.uniform(self.reference_prices[symbol] - self.delta, self.reference_prices[symbol] + self.delta),
        ) if order_type == OrderType.LIMIT else OrderMessage(
            symbol=symbol,
            side=side,
            qty=self.order_qty,
            order_type=order_type,
        )

    def sendOrder(self, orderMsg):
        fix.Session.sendToTarget(orderMsg.msg, self.sessionID)
        self.orders_sent += 1

    def cancelOrder(self, orderCancelRequest):
        fix.Session.sendToTarget(orderCancelRequest.msg, self.sessionID)

    ### SINGLE ENTRY POINT
    def run(self):
        self.logon_event.wait()
        print("Sending Orders...")
        for i in range(self.numOrders):
            orderMsg = self.create_order_message()
            self.order_manager.add_order(
                order_id=orderMsg.orderID,
                message=orderMsg.msg,
                qty_filled=0,
                status=fix.OrdStatus_NEW
            )

            if generate_boolean_with_probability(self.order_cancel_probability):
                self.order_manager.mark_order_for_cancellation(orderMsg.orderID)
            self.sendOrder(orderMsg)

        print("Cancelling Orders...")
        for clOrdID in self.order_manager.orders_to_cancel:
            orderCancelRequest = self.order_manager.create_cancel_request(clOrdID)
            if orderCancelRequest:
                self.cancelOrder(orderCancelRequest)

        time.sleep(FIX_CLIENT_WAIT_TIME)
