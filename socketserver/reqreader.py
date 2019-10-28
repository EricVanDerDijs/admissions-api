import asyncio, socket, json, struct
from collections import namedtuple

class Reader:
  def __init__(self, client):
    self._client = client
    self._received_data = b''

  async def read(self):
    request = namedtuple('request', [
      'header',
      'body',
    ])
    stillReading = True
    header_len = None
    header = None
    body = None
    while stillReading:
      self._received_data += await self._read()

      if header_len is None:
        header_len, data_without_protoheader = self.process_protoheader()
        self._received_data = data_without_protoheader

      if (
        header_len is not None and
        header is None
      ):
        header, data_without_header = self.process_header(header_len)
        self._received_data = data_without_header

      if (
        header is not None and
        body is None
      ):
        body, data_without_body = self.process_body(header)
        self._received_data = data_without_body
      
      if body is not None:
        stillReading = False
    
    return request(header, body)

  async def _read(self):
    data = b''
    try:
      loop = asyncio.get_event_loop()
      data = await loop.sock_recv(self._client, 256)
    except Exception as e:
      print(f'_read() err: {e}')

    return data

  def process_protoheader(self):
    protoheader_len = 2
    returnedVal = namedtuple('returnedVal', [
      'header_len',
      'data_without_protoheader',
    ])
    if len(self._received_data) >= protoheader_len:
      # get header len
      header_len = struct.unpack(
        '>H',
        self._received_data[:protoheader_len]
      )[0]
      # remove protoheader from request
      data_without_protoheader = self._received_data[protoheader_len:]
      return returnedVal(header_len, data_without_protoheader)
    else:
      return returnedVal(None, self._received_data)

  def process_header(self, header_len):
    returnedVal = namedtuple('returnedVal', [
      'header',
      'data_without_header',
    ])
    if len(self._received_data) >= header_len:
      header = self._received_data[:header_len]
      header = header.decode('utf-8')
      header = json.loads(header)
      data_without_header = self._received_data[header_len:]
      return returnedVal(header, data_without_header)
    else:
      return returnedVal(None, self._received_data)

  def process_body(self, header):
    returnedVal = namedtuple('returnedVal', [
      'body',
      'data_without_body',
    ])
    content_len = header.get('content-length')
    content_type = header.get('content-type')
    content_encoding = header.get('content-encoding')

    if (
      content_len and
      content_type and
      content_encoding and
      len(self._received_data) >= content_len
    ):
      body = self._received_data[:content_len]
      data_without_body = self._received_data[content_len:]

      if content_type == 'text/json':
        body = body.decode( content_encoding )
        body = json.loads( body )
        return returnedVal(body, data_without_body)
      else:
        # implement other content types id needed
        return returnedVal(None, self._received_data)
        
    else:
      return returnedVal(None, self._received_data)
