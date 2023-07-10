from deribitv2 import DeriBit
import time

# # without async

d = DeriBit()
d.getauth()

time.sleep(5)
n = 15

t_s = time.time()

for i in range(n):
    d.getorderbook("BTC-PERPETUAL")
    
took = time.time() - t_s
print('time used without async', took)
print("average per call", took/n)

# time.sleep(2)

# url = "https://www.deribit.com"

# # async def do_request():
# #     async with aiohttp.ClientSession() as session:
# #         async with session.get(url + "/api/v2/public/get_order_book", params = {"instrument_name": "BTC-PERPETUAL"}) as res:
# #             r = await res.json()
# #             print(r)
# # asyncio.get_event_loop().run_until_complete(do_request())

# async def action(session):
#     async with session.get(url + "/api/v2/public/get_order_book", params={"instrument_name": "BTC-PERPETUAL"}) as res:
#         r = await res.json()
#         # print(r)
#         return r

# async def main():
#     async with aiohttp.ClientSession() as session:
#         r = []
#         for i in range(3):
#             task = asyncio.ensure_future(action(session))
#             r.append(task)
#         r = await asyncio.gather(*r)

# t_s = time.time()
# # loop.run_until_complete(main())
# asyncio.run(main())
# print("time used with async", time.time() - t_s)
# # # # on average 26-40 ms / 0.026-0.04delay

# session.close()