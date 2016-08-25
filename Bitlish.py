import asyncio
import websockets
import json


class BitlishError(Exception):
    pass

class Bitlish(object):

    def __init__(self, token=None, timeout=30, throw_errors=True, url='wss://bitlish.com/ws'):
        self.url = url
        self.ws = None
        self.req_cnt = 0
        self.token = token
        self.timeout = timeout
        self.waiting = {}
        self.listener = None
        self.throw_errors = throw_errors
        self.loop = asyncio.get_event_loop()
        self.wlock = asyncio.locks.Lock()

    @asyncio.coroutine
    def init(self):
        self.ws = yield from websockets.connect(self.url)
        self.listener = self.loop.create_task(self._listen())
        return self

    def __del__(self):
        self.stop()

    def stop(self):
        if self.loop.is_running():
            self.listener.cancel()
            self.ws.close()

    @asyncio.coroutine
    def _listen(self):
        while True:
            ans = yield from self.ws.recv()
            # print(ans, self.waiting.keys())
            if ans:
                resp = json.loads(ans)
                mark = resp.get('mark')
                if mark:
                    with (yield from self.wlock):
                        state = self.waiting.get(str(mark), None)
                        if state:
                            # print(ans)
                            t = state['timer']
                            # TODO: race with timeout handler?
                            t.cancel()
                            q = state['queue']
                            q.put_nowait(resp)

    @asyncio.coroutine
    def _wait_for(self, mark):
        q = self.waiting[mark]['queue']
        resp = yield from q.get()
        with (yield from self.wlock):
            # removing handler because waiting for answer completed
            self.waiting.pop(mark)
        # TODO: return error if not throwed?
        err = self.wrap_error(resp)
        return resp

    def wrap_error(self, resp):
        err, data = resp.get('error'), resp.get('data')
        if err:
            if data:
                try:
                    err += ' ' + (data['msg'] % tuple(data['args']))
                    path = data.get('path')
                    if path:
                        err += ' Path: ' + str(path)
                except:
                    err += ' ' + str(data)
            if self.throw_errors:
                raise BitlishError(err)
        return err

    def __getattr__(self, item):

        @asyncio.coroutine
        def _wrap(args=None):
            req = self._construct_req(item, args)
            res = yield from self._call(req)
            return res

        return _wrap

    def _construct_req(self, call, args):
        return {
            'call': call,
            'token': self.token,
            'data': args,
            'mark': self._get_mark(),
        }

    def _get_mark(self):
        self.req_cnt += 1
        return str(self.req_cnt)

    @asyncio.coroutine
    def _call(self, req):
        @asyncio.coroutine
        def _timeout(time, req):
            yield from asyncio.sleep(time)
            mark = req['mark']
            with (yield from self.wlock):
                hdl = self.waiting.get(mark)
                hdl['queue'].put_nowait({
                    'call': req['call'],
                    'mark': mark,
                    'error': 'Bitlish::Err::Timeout',
                    'data': {'args': [self.timeout], 'msg': 'Timeout %ss'},
                })

        q = asyncio.Queue(maxsize=1)
        ct = self.loop.create_task(_timeout(self.timeout, req))

        mark = req['mark']
        self.waiting[mark] = {
            'req': req,
            'timer': ct,
            'queue': q,
        }

        raw = json.dumps(req)
        while True:
            try:
                yield from self.ws.send(raw)
            except websockets.exceptions.ConnectionClosed:
                print('retry')
                self.ws = yield from websockets.connect(self.url)
                yield from asyncio.sleep(1)
                continue
            except Exception as e:
                print('error on send:', e)
            else:
                break

        ans = yield from self._wait_for(mark)
        return ans
