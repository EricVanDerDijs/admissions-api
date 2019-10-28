import socket, asyncio, types
from .reqreader import Reader
from .formater import formatRequest
import socketserver.constants as constants

class Server:
  def __init__(self, *, host = 'localhost', port):
    # Define socket
    self._host = host
    self._port = port
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.bind( (host, port) )
    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Define Loop field
    self._loop = None
    # Define routes dict
    self._routes_handlers = {
      'GET': {},
      'POST': {},
      'PUT': {},
      'PATCH': {},
      'DELETE': {},
    }
    # Define dict with server-wide variables
    self._server_vars = {}
  
  # HANDLER SETTERS, ONE PER VERB
  def get(self, route, handler):
    if isinstance(route, str):
      self._routes_handlers[constants.GET][route] = handler
    else:
      raise Exception('Routes must be strings')

  def post(self, route, handler):
    if isinstance(route, str):
      self._routes_handlers[constants.POST][route] = handler
    else:
      raise Exception('Routes must be strings')

  def put(self, route, handler):
    if isinstance(route, str):
      self._routes_handlers[constants.PUT][route] = handler
    else:
      raise Exception('Routes must be strings')

  def patch(self, route, handler):
    if isinstance(route, str):
      self._routes_handlers[constants.PATCH][route] = handler
    else:
      raise Exception('Routes must be strings')

  def delete(self, route, handler):
    if isinstance(route, str):
      self._routes_handlers[constants.DELETE][route] = handler
    else:
      raise Exception('Routes must be strings')

  # SERVER_VARS SETTER
  def use(self, var_name, var_value):
    if isinstance(var_name, str):
      self._server_vars[var_name] = var_value
    else:
      raise Exception('var_name must be strings')

  # EXPOSED RUN FUNCTION
  # gets the event loop, save it to the instance of the server
  # and start the inner server loop
  def run(self):
    self._loop = asyncio.get_event_loop()
    self._loop.run_until_complete( self._server_loop() )

  # INNER SERVER LOOP COROUTINE
  # starts listening on a non-blocking socket and pass
  # the incoming conections to the general handle_client
  # handler
  async def _server_loop(self):
    self._socket.listen()
    self._socket.setblocking(False)
    print(f'server listening on {self._host}:{self._port}')
    while True:
      client, addr = await self._loop.sock_accept(self._socket)
      print(f'accepted conn from {addr}')
      self._loop.create_task( self.handle_client(client) )
  
  # GENERAL HANDLER
  # creates a reader object and tries to read the data
  # from the connections which should be formatted as
  # 'protoheader{json-header}{body}'
  # if fails, then the connection is closed
  # else 
  async def handle_client(self, client):
    # Tries to read data
    reader = Reader(client)
    try:
      header, body = await asyncio.wait_for(
        reader.read(),
        10,
      )
    except asyncio.TimeoutError:
      header, body = (None, None)

    if ( # fail -> close connection
      header is None or
      body is None
    ):
      client.close()
    else: # manage the request
      try:
        # get the right handler for the request based on the
        # VERB and ROUTE
        verb = header.get('verb', constants.GET)
        verb_handlers = self._routes_handlers[verb]
        route = header.get('route', '')
        handler = verb_handlers.get(route)
        # if a handler is found, run it with the request data
        # and await for results
        if (
          isinstance(handler, types.FunctionType) or
          isinstance(handler, types.MethodType)
        ):
          resHeader, resBody = await handler(header, body, **self._server_vars)
          resHeader = {
            **header,
            **resHeader,
          }
          # format the response
          response = formatRequest(
            verb,
            route,
            body = resBody,
            header = resHeader,
          )
          # send it to the client
          await self._loop.sock_sendall(client, response)
          # close connection
          client.close()
        else:
          # no handler has been found
          # responde with 404 err
          notFoundHeader = {
            **header,
            'code': 404
          }
          notFoundBody = {
            'error': 'not_found',
            'message': 'The resource your are looking for has not been found'
          }
          notFoundResponse = formatRequest(
            verb,
            route,
            header = notFoundHeader,
            body = notFoundBody,
          )
          await self._loop.sock_sendall(client, notFoundResponse)
          # close connection
          client.close()
      except Exception as e:
        try:
          # General Err handler
          # responde with 500 err
          gErrHeader = {
            **header,
            'code': 500
          }
          gErrBody = {
            'error': 'internal_err',
            'message': repr(e)
          }
          generalErrorResponse = formatRequest(
            verb,
            route,
            header = gErrHeader,
            body = gErrBody,
          )
          await self._loop.sock_sendall(client, generalErrorResponse)
          # close connection
          client.close()
        except Exception:
          # If the sending of the err message fails, close de connection
          # close connection
          client.close()


