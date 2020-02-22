from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters
from AsyncAPY.objects import Packet
import time
from copy import copy
import re


srv = AsyncAPY(timeout=86400, logging_level=10)
usernames = {"SYSTEM": None}
URI_REGEX = """((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])"""
URI_REGEX_PATTERN = re.compile(URI_REGEX)
BLOCK_LINKS = True     # Set to False to disable the AntiSpam in chat
MAX_MSG_THRESHOLD = (3, 2)  # Choose how many message can be sent in every second, default to 3 msgs per 2 sec, False to disable


@srv.handler_add([Filters.Fields(method="PING")])
async def pong(c, p):
    encoding = 1 if c.encoding == 'ziproto' else 0
    await c.send(Packet({"status": "success"}, encoding=encoding), close=False)


@srv.handler_add([Filters.Fields(method="CHECK_NAME", name=None)])
async def check_name(c, p):
    names = copy(usernames)
    del names['SYSTEM']
    name = p["name"]
    encoding = 1 if c.encoding == 'ziproto' else 0
    if name in usernames:
        await c.send(Packet({"status": "success", "name": "taken"}, encoding=encoding), close=False)
    else:
        usernames[name] = c.session
        await c.send(Packet({"status": "success", "name": "free"}, encoding=encoding), close=False)
        for name, session in list(names.items()):
            recipient = session.get_client()
            await recipient.send(Packet({"whisper": False, "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": f"{p['name']} joins the chat room!", "sender": 'SYSTEM'}, encoding=encoding), close=False)


@srv.handler_add([Filters.Fields(method="SEND_MESSAGE", type="BROADCAST", sender=None, message=None)])
async def broadcast_message(c, p):
    names = copy(usernames)
    del names['SYSTEM']
    encoding = 1 if c.encoding == 'ziproto' else 0
    for name, session in list(names.items()):
        recipient = session.get_client()
        await recipient.send(Packet({"whisper": False, "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": p["message"], "sender": p["sender"]}, encoding=encoding), close=False)


@srv.handler_add([Filters.Fields(method='FREE_USERNAME', name=None)])
async def free_username(c, p):
    global usernames
    names = copy(usernames)
    del names['SYSTEM']
    if p["name"] in names:
        del usernames[p["name"]]
    encoding = 1 if c.encoding == 'ziproto' else 0
    await c.close()
    for name, session in list(names.items()):
        recipient = session.get_client()
        await recipient.send(Packet({"whisper": False, "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": f"{p['name']} left the chat room", "sender": 'SYSTEM'}, encoding=encoding), close=False)


@srv.handler_add([Filters.Fields(method="SEND_MESSAGE", type="WHISPER", sender=None, recipient=None, message=None)])
async def whisper_message(c, p):
    encoding = 1 if c.encoding == 'ziproto' else 0
    if p["recipient"] in usernames and p["recipient"] != "SYSTEM":
        client = usernames[p["recipient"]].get_client()
        await client.send(Packet({"whisper": True, "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": p["message"], "sender": p["sender"]}, encoding=encoding), close=False)
    else:
        await c.send(Packet({"whisper": True, "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": f"User {p['recipient']} is not online! Message not sent", "sender": "SYSTEM"}, encoding=encoding), close=False)


@srv.handler_add([Filters.Fields(method="GET_ONLINE_USERS", limit='\d+', sender=None)])
async def get_online_users(c, p):
    names = copy(usernames)
    del names["SYSTEM"]
    encoding = 1 if c.encoding == "ziproto" else 0
    msg = "Currently online users:\n"
    for index, (name, session) in enumerate(list(names.items())):
        msg += f"{index}) {name}"
        if index + 1 == int(p["limit"]):
            break
    await c.send(Packet({"whisper": True, "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": msg, "sender": "SYSTEM"}, encoding=encoding), close=False)


@srv.handler_add([Filters.Fields(method='SEND_MESSAGE', type='BROADCAST', sender=None, message=None)], priority=-1)
async def spam_watcher(c, p):
    names = copy(usernames)
    del names["SYSTEM"]
    msg = p["message"]
    encoding = 1 if c.encoding == 'ziproto' else 0
    if URI_REGEX_PATTERN.search(msg) and BLOCK_LINKS:
        match = URI_REGEX_PATTERN.search(msg)
        await c.send(Packet({"whisper": True, "kicked": True,  "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": f"{p['sender']} don't spam!", "sender": "SYSTEM"}, encoding=encoding), close=False)
        await c.close()
        try:
            del usernames[p["sender"]]
        except Exception:
            pass
        for name, session in list(names.items()):
            recipient = session.get_client()
            await recipient.send(Packet({"whisper": False, "date" : time.strftime("%d/%m/%Y %H:%M:%S %p"), "msg": f"{p['sender']} kicked for link spam!", "sender": "SYSTEM"}, encoding=encoding), close=False)
        await p.stop_propagation()


@srv.handler_add([Filters.Fields(method='SEND_MESSAGE', type='BROADCAST', sender=None, message=None)], priority=-2)
async def antiflood(c, p):
    pass


srv.start()

