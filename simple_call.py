#!/usr/bin/env python3
from time import time

import os
import argparse
from pprint import pprint

import asyncio

from Bitlish import Bitlish, BitlishError

TOKEN = os.getenv('TOKEN')
TOKEN = TOKEN or "fixed:qweqwe"
PREC = 3

parser = argparse.ArgumentParser(description='Simple periodic buy-sell example')
parser.add_argument('-t', '--token', help='API token')


@asyncio.coroutine
def main():
    a = time()
    api = yield from Bitlish(TOKEN, timeout=10, throw_errors=False).init()
    b = time(); print('Connected in {:5.3f}s'.format(b-a))

    resp = yield from api.profile()
    c = time(); print('Request completed in {:5.3f}s'.format(c-b))

    if resp.get('error'):
        print('Error on API call:', api.wrap_error(resp))
    else:
        profile = resp["data"]
        print('\nProfile:')
        pprint(profile)

    api.stop()


if __name__ == '__main__':
    args = parser.parse_args()
    TOKEN = args.token or TOKEN

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
