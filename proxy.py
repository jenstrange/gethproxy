#!/usr/bin/env python3
import asyncio
import websockets
import json
from contextlib import closing
from sqlitedict import SqliteDict

async def gethnode(req):
  async with websockets.connect("wss://gethnode.com/ws") as websocket:
    await websocket.send(req)
    resp = await websocket.recv()
    return resp

async def server(websocket, path):
  with closing(SqliteDict('./cache.sqlite', autocommit=True)) as memoize:
    while 1:
      req = json.loads(await websocket.recv())
      print(f"< {req}")
      key = (req['method'], req['params'])
      if key not in memoize:
        print("cache miss")
        memoize[key] = await gethnode(json.dumps(req))
      resp = memoize[key] 
      print(f"> {resp}")
      #print(f"> {len(resp)}")
      await websocket.send(resp)

if __name__ == "__main__":
  """
  print("test")
  resp = asyncio.get_event_loop().run_until_complete(gethnode('{"id":1,"jsonrpc":"2.0","method":"net_version","params":[]}'))
  print(resp)
  """
  print("starting server")
  start_server = websockets.serve(server, 'localhost', 8546)
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()

