## How to run the application

### Option 1 (Preferred): Docker

Prerequisites: Docker

`cd` into the root directory (The one containing the Dockerfile). Run:

    docker build -t fix-client .

    docker run fix-client

### Option 2:

Prerequisites: Conda (Or a Python 3.9 environment correctly set up), pip

`cd` into the root directory. Run:

    conda create --name=fix-client python=3.9

    conda activate fix-client

    pip install quickfix-1.15.1-cp39-cp39-win_amd64.whl

    python client.py

## Documentation

The classes of the application are:

**OrderMessage**: Encapsulates a FIX New Order - Single

**OrderCancelRequest**: Encapsulates a FIX OrderCancelRequest

**OrderManager** - Manages the state of the orders (status, messages, fill quantity, and orders to cancel)

**Transaction**: Encapsulates a successful transaction (BUY/SELL/SHORT) after an order is filled/partially filled

**DTLTradeStats**: Manages the statistics of the orders (total volume, PnL, fill VWAP of each instrument, and inventories of each instrument)

**DTLFixApplication**: Inherits `quickfix.Application` to handle all FIX events of the application

**FixClient**: The entry point of the application

### How it works

#### How the orders are sent out

The application sends out 1000 orders immediately upon start, while also adding some of the orders sent to a set with 20% probability. After all orders are sent, the application begins to send out cancellation requests for the orders in the set. It then waits for 2 minutes for most orders to complete (either successful execution or cancellation). Note that the number of complete orders could be closer to 1000 if we increase the waiting time. Also, due to random price generation, some limit orders will never be filled due to the price being too low/too high compared to current market prices on the server.

#### How messages from the server are handled

We handle 3 messages, Reject, ExecutionReport, and OrderCancelReject.

For ExecutionReport, we ignore it if its a NEW order. Update the order state if it is a CANCELED order. If it is FILLED or PARTIALLY FILLED, we create a **Transaction** and utilize the **DTLTradeStats** class to process this transaction.

For OrderCancelReject, we resend the cancellation request if the order is still active.

#### How the statistics are calculated

The **DTLTradeStats** class updates the total volume and total value of each instrument every time it processes a transaction. This enables us to calculate the total volume and per-instrument fill VWAP.

Methodology of **PnL** calculation:
We start with a balance of 0.
Every BUY trade increases inventory and decreases the balance, while every SELL/SHORT trade decreases inventory and increases the balance.
At the point of PnL calculation, we use the VWAP of the fills to estimate the value of our existing inventory, and add it to the balance.

Formula: _PnL = balance + sum((inventory * VWAP) for each instrument)_

Note that balance or inventory could be negative (which means we owe cash and/or inventory).
