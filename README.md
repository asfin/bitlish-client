# bitlish-client
Official https://bitlish.com bitcoin exchange WebSocket API wrapper on python3 with asyncio.

# Dependencies
Now only `asyncio` and `websockets` modules required.

# Usage
With your account at https://bitlish.com create "fixed" API token on personal settings page.
Run examples with `-t` flag like `./simple_call.py -t 'your_token'` or use `Bitlish.py` module in your own scripts.
```python
# import wrapper
from Bitlish import Bitlish
...
# create and initialize connection
api = yield from Bitlish(TOKEN, timeout=20, throw_errors=False).init()
...
# make your calls
resp = yield from api.list_my_trades({'limit': 1})
err, data = resp.get('error'), resp.get('data')
if err:
    print('Error:', api.wrap_error(resp))  # construct error string
else:
    print('My order:', data['list'][0])
```

# Examples
`simple_call.py` - simple API call, you can get error with invalid token.

`parallel_calls.py` - example of parallel call execution.

`simple_call_with_exception.py` - try/except example for error handling.

`simple_bot.py` - periodic random buying and selling in selected pairs with tiny amounts(~0.001btc).

# Notes
`throw_errors=True` parameter raises exception when error from server is received,
see `simple_call_with_exception.py` for example.

