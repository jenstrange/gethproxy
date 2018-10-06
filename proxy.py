#!/usr/bin/env python3
import asyncio
import websockets
import json
from contextlib import closing
from sqlitedict import SqliteDict

# geth aware proxy:
#   block based invalidation, if not latest, it's fine to cache:
#     eth_getBlockByNumber 
#     eth_getLogs
# can i cache eth_call?


async def gethnode(req):
  # 256MB max request
  async with websockets.connect("wss://gethnode.com/ws", max_size=2**28) as websocket:
    await websocket.send(req)
    resp = await websocket.recv()
    return resp

async def server(websocket, path):
  # is SqliteDict threadsafe? looks like it
  # can replace the sqlite with redis to scale anyway
  with closing(SqliteDict('./cache.sqlite', autocommit=True)) as memoize:
    while 1:
      req = json.loads(await websocket.recv())
      assert sorted(req.keys()) == sorted(['id', 'jsonrpc', 'method', 'params'])
      key = json.dumps((req['method'], req['params']))
      print(f"< {key}")
      if key not in memoize:
        print("> cache miss, fetch...")
        resp = json.loads(await gethnode(json.dumps(req)))
        assert sorted(resp.keys()) == sorted(['id', 'jsonrpc', 'result'])
        #print(f">> {resp}")
        memoize[key] = resp['result']
      presp = {'id':req['id'], 'jsonrpc':req['jsonrpc'], 'result':memoize[key]}
      presp = json.dumps(presp)
      #print(f"> {presp}")
      print(f"> {len(presp)}")
      await websocket.send(presp)

if __name__ == "__main__":
  """
  print("test")
  resp = asyncio.get_event_loop().run_until_complete(gethnode('{"id":1,"jsonrpc":"2.0","method":"net_version","params":[]}'))
  print(resp)
  """
  print("starting server")
  start_server = websockets.serve(server, 'localhost', 8547)
  asyncio.get_event_loop().run_until_complete(start_server)
  asyncio.get_event_loop().run_forever()

