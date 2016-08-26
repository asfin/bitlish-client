#!/usr/bin/env python3
import os
import argparse
from time import time
from pprint import pprint

import asyncio

from Bitlish import Bitlish, BitlishError

TOKEN = os.getenv('TOKEN')
TOKEN = TOKEN or "fixed:qweqwe"

parser = argparse.ArgumentParser(description='Parallel execution example')
parser.add_argument('-t', '--token', help='API token')


@asyncio.coroutine
def main():
    api = yield from Bitlish(TOKEN, timeout=10, throw_errors=False).init()
    # please note that sometimes calls can be delayed by server to prevent DDoS
    # you should get informative exception about that

    a = time()
    t_resp = yield from api.list_active_trades()
    o_resp = yield from api.trades_depth()
    b_resp = yield from api.balance()
    print(t_resp, b_resp)  # o_resp too large for displaying
    print()
    b = time(); print('Serial requests completed in {:5.3f}s'.format(b-a))

    tasks = [api.list_active_trades(), api.trades_depth(), api.balance()]
    t_resp, o_resp, b_resp = yield from asyncio.gather(*tasks)
    print(t_resp, b_resp)
    print()
    c = time(); print('Parallel requests completed in {:5.3f}s'.format(c-b))

    api.stop()


if __name__ == '__main__':
    args = parser.parse_args()
    TOKEN = args.token or TOKEN

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
