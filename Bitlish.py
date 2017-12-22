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
        self.waiting = dict()
        self.ev_hdls = dict()
        self.listener = None
        self.throw_errors = throw_errors
        self.loop = asyncio.get_event_loop()
        self.wlock = asyncio.locks.Lock()

    @asyncio.coroutine
    def init(self):
        if self.listener:
            self.listener.cancel()
        if self.ws:
            self.ws.close()
        e = None
        for i in range(1, 5):
            try:
                self.ws = yield from websockets.connect(self.url)
                self.listener = self.loop.create_task(self._listen())
            except Exception as _e:
                e = _e
                yield from asyncio.sleep(i * 2)
            else:
                break
        if e:
            raise e
        return self

    def on_event(self, ev_name, coro):
        self.ev_hdls[ev_name] = coro

    def __del__(self):
        self.stop()

    def stop(self):
        if self.loop.is_running():
            self.listener.cancel()
            self.ws.close()

    @asyncio.coroutine
    def _listen(self):
        while True:
            try:
                ans = yield from self.ws.recv()
            except websockets.exceptions.ConnectionClosed as e:
                break
            # print(ans, self.waiting.keys())
            if ans:
                resp = json.loads(ans)

                ans_type = resp.get('type')
                if ans_type == 'response':
                    mark = resp.get('mark')
                    if mark:
                        # with (yield from self.wlock):
                        state = self.waiting.get(str(mark), None)
                        if state:
                            # print(ans)
                            t = state['timer']
                            # TODO: race with timeout handler?
                            # case: while processing this call, timer is triggered, but it will be canceled in next line
                            # python docs said that `cancel` "does not guarantee that the task will be cancelled"
                            t.cancel()
                            q = state['queue']
                            q.put_nowait(resp)
                elif ans_type == 'event':
                    call = resp.get('call')
                    coro = self.ev_hdls.get(call)
                    if coro:
                        self.loop.create_task(coro(resp))

        self.loop.create_task(self.init())

    @asyncio.coroutine
    def _wait_for(self, mark):
        q = self.waiting[mark]['queue']
        resp = yield from q.get()
        # with (yield from self.wlock):
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
            # if timeout has been cancelled, will throw CancelledError here
            yield from asyncio.sleep(time)
            mark = req['mark']
            # with (yield from self.wlock):
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
                print('retrying send')
                # self.ws = yield from websockets.connect(self.url)
                # yield from self.init()
                yield from asyncio.sleep(1)
                continue
            except Exception as e:
                print('error on send:', e)
                raise e
            else:
                break

        ans = yield from self._wait_for(mark)
        return ans
