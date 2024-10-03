import quickfix as fix
import sys
from application import DTLFixApplication
from constants import (
    NUM_ORDERS,
    ORDER_CANCEL_PROBABILITY,
    RANDOM_SEED,
    FIX_CONFIG_FILE_PATH,
    SYMBOLS,
    REFERENCE_PRICES
)

class FixClient:
    def __init__(self, config_file: str):
        self.settings = fix.SessionSettings(config_file)

    def run(self):
        application = DTLFixApplication(
        numOrders=NUM_ORDERS,
        order_cancel_probability=ORDER_CANCEL_PROBABILITY,
        order_qty=1000,
        random_seed=RANDOM_SEED,
        symbols=SYMBOLS,
        reference_prices=REFERENCE_PRICES
        )
        storefactory = fix.FileStoreFactory(self.settings)
        logfactory = fix.FileLogFactory(self.settings)
        initiator = fix.SocketInitiator(
            application, storefactory, self.settings, logfactory
        )
        try:

            initiator.start()
            application.run()
            initiator.stop()

        except (fix.ConfigError, fix.RuntimeError) as e:
            print(e)
            initiator.stop()
            sys.exit()


if __name__ == "__main__":
    client = FixClient(FIX_CONFIG_FILE_PATH)
    client.run()
