#!/usr/bin/env python3
import os
import argparse
import math
from time import time
from random import random
from decimal import Decimal, getcontext, ROUND_FLOOR

import asyncio

from Bitlish import Bitlish

TOKEN = os.getenv('TOKEN')
TOKEN = TOKEN or "fixed:qweqwe"
PREC = 3
b = None

parser = argparse.ArgumentParser(description='Simple periodic buy-sell example')
parser.add_argument('-t', '--token', help='API token')


def trunc(num, prec):
    p = 10**prec
    num *= p
    num = math.trunc(num)
    return Decimal(num)/p


@asyncio.coroutine
def try_sell(pair, max_amount, balances):
    balance, btc_balance = balances
    max_amount = round(max_amount, PREC)
    res = yield from b.create_trade({
        "pair_id": pair,
        "dir": "ask",
        "amount": max_amount,
    })
    return res


@asyncio.coroutine
def try_buy(pair, max_amount, balances):
    balance, btc_balance = balances
    depth = (yield from b.trades_depth({"pair_id": pair}))["data"]
    ask = depth["ask"]
    if not len(ask):
        return None
    top = ask[0]
    to_buy = trunc(balance/float(top["price"]), PREC)
    to_buy = str(to_buy)

    res = yield from b.create_trade({
        "pair_id": pair,
        "dir": "bid",
        "amount": to_buy,
    })
    if res.get("error"):
        ans = yield from try_sell(pair, max_amount, balances)
        return ans
    else:
        return res



@asyncio.coroutine
def main():
    global b
    loop = asyncio.get_event_loop()
    b = yield from Bitlish(TOKEN).init()

    PERIOD = 3500
    CURRENCIES = ["usd", "eur"]
    AMOUNT = 0.001
    while True:
        for cur in CURRENCIES:
            pair = "btc" + cur
            print("pair", pair)
            balances = (yield from b.balance())["data"]
            print("got balances")
            balances = (float(balances[cur]["funds"]), float(balances["btc"]["funds"]))
            # select handler
            if balances[0] > 0:
                f = try_buy(pair, AMOUNT+random()/1000, balances)
            else:
                f = try_sell(pair, AMOUNT+random()/1000, balances)
            # run handler
            res = yield from f
            yield from asyncio.sleep(PERIOD/len(CURRENCIES))

    b.stop()


if __name__ == '__main__':
    args = parser.parse_args()
    TOKEN = args.token or TOKEN

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
