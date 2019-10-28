import json, struct

def formatRequest(verb, route, *, body = {}, header = {}):
  formatedBody = jsonEncode(body)
  formatedHeader = None
  req = None
  if (
    isinstance(verb, str) and
    isinstance(route, str) and
    formatedBody is not None
  ):
    standard_header = {
      **header,
      'verb': verb,
      'route': route,
      'content-length': len(formatedBody)
    }
    formatedHeader = formatHeader(standard_header)
    if (
      formatedHeader is not None and
      formatedBody is not None
    ):
      protoHeader = struct.pack(">H", len(formatedHeader))
      req = protoHeader + formatedHeader + formatedBody
  if req is None:
    raise Exception('Parsing Error')
  return req

def formatHeader(header):
  verb = header.get('verb')
  route = header.get('route')
  contentLen = header.get('content-length')
  contentEncoding = header.get('content-encoding', 'utf-8')
  contentType = header.get('content-type', 'text/json')

  if (
    isinstance(verb, str) and
    isinstance(route, str) and
    isinstance(contentLen, int)
  ):
    finalHeader = {
      **header,
      'content-encoding': contentEncoding,
      'content-type': contentType,
    }
    return jsonEncode(finalHeader)
  else:
    return None

def jsonEncode(dictionary, *, encoding = 'utf-8'):
  try:
    return json.dumps(dictionary).encode(encoding)
  except Exception:
    return None