import asyncio, functools, socket
from .formater import formatRequest
from .reqreader import Reader

runNo = []

class Go:
  def __init__(
    self,
    verb,
    route,
    *,
    host_port = None,
    sock = None,
    body = {},
    header = {},
  ):
    if (
      isinstance(host_port, tuple) and
      isinstance(host_port[0], str) and
      isinstance(host_port[1], int)
    ):
      self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
        self._sock.connect( host_port )
      except Exception as e:
        self._sock = e
    elif sock is not None:
      self._sock = sock
    else:
      raise Exception('socket or connection address is missing!')
    self.req = formatRequest(verb, route, body = body, header = header)

  async def as_coroutine(self):
    if isinstance(self._sock, Exception):
      header = { 'code': 500 }
      body = {}
      
      if isinstance(self._sock, ConnectionRefusedError):
        body = { 'error_code': 'connection-refused', 'error': repr(self._sock) }
      else: 
        body = { 'error_code': 'unexpected-error', 'error': repr(self._sock) }
      
      return header, body
    
    if self.req is not None:
      reader = Reader(self._sock)
      loop = asyncio.get_event_loop()
      # Send req
      try:
        await loop.sock_sendall(self._sock, self.req)
      except Exception as e: # Error Sending
        print(f'sendall() err: {repr(e)}')
        body = { 'error_code': 'unexpected-error', 'error': repr(e) }
        header = { 'code': 500 }
        return header, body
      # Read res
      try:
        res = await asyncio.wait_for(
          reader.read(),
          10,
        )
        return res
      except asyncio.TimeoutError:
        body = { 'error_code': 'timeout-error' }
        header = { 'code': 408 }
        return header, body
      except Exception as e: # Error Reading
        print(f'reader.read() err: {repr(e)}')
        body = { 'error_code': 'unexpected-error', 'error': repr(e) }
        header = { 'code': 500 }
        return header, body
    else:
      body = { 'error_code': 'no-request-provided' }
      header = { 'code': 400 }
      return header, body


  def with_callback(self, callback = None, args = ()):
    if callback is None:
      raise Exception('Callback is missing!')
    else:
      loop = asyncio.get_event_loop()
      cb_with_args = functools.partial(callback, *args)
      task = loop.create_task( self.as_coroutine() )
      task.add_done_callback( cb_with_args )
      if not loop.is_running():
        loop.run_until_complete( task )
  