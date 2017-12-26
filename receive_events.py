#!/usr/bin/env python3
import os
import argparse
from time import time
from pprint import pprint

import asyncio

from Bitlish import Bitlish, BitlishError

TOKEN = os.getenv('TOKEN')
TOKEN = TOKEN or "fixed:qweqwe"

parser = argparse.ArgumentParser(description='Event handling example')
parser.add_argument('-t', '--token', help='API token')


@asyncio.coroutine
def handle_order_event(ev):
    print('got trade event: {}'.format(ev))


@asyncio.coroutine
def handle_payment_info(ev):
    print('got payment_info event: {}'.format(ev))


@asyncio.coroutine
def main():
    api = yield from Bitlish(TOKEN, timeout=10, throw_errors=False).init()

    a = yield from api.resign()  # initialize session

    api.on_event('public_trade_order_cancel', handle_order_event)
    api.on_event('public_trade_order_create', handle_order_event)
    api.on_event('payment_info', handle_payment_info)

    yield from asyncio.sleep(1500)  # wait for some events

    api.stop()


if __name__ == '__main__':
    args = parser.parse_args()
    TOKEN = args.token or TOKEN

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
