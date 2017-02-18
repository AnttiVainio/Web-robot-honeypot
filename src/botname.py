import re
import socket

# Regular expressions for identifying bots based on the user-agent
# bot name with a version number
b1 = re.compile('(\w*bot\w*/[.\d]+)', flags=re.I)
b2 = re.compile('(\w*crawl\w*/[.\d]+)', flags=re.I)
b3 = re.compile('(\w*spider\w*/[.\d]+)', flags=re.I)
# without version number
b4 = re.compile('(\w*bot\w*)', flags=re.I)
b5 = re.compile('(\w*crawl\w*)', flags=re.I)
b6 = re.compile('(\w*spider\w*)', flags=re.I)
# website address
b7 = re.compile('http://([\w\.]*)', flags=re.I)
b8 = re.compile('https://([\w\.]*)', flags=re.I)

class BotResult(Exception):
    pass

# Raises the found match as an exception
def test(b, ua):
    match = b.search(ua)
    if match: raise BotResult(match.group(1))

# Adds the host, that was got from a reverse dns query, after the name of the bot
def add_host(bot, ip):
    try: host = socket.gethostbyaddr(ip)[0]
    except Exception as e:
        print("    BOT: exception:")
        print("        " + str(type(e)) + ": " + str(e))
        return bot + " - ???"
    # try to remove possible ip address from the host and only keep the last part
    host_parts = []
    for i in reversed(host.split(".")):
        if i[-1] >= '0' and i[-1] <= '9': break # the part ends with a digit
        else: host_parts.append(i)
    if not host_parts: return bot
    return " - ".join((bot, ".".join(reversed(host_parts))))

def get_bot_name(ua, ip):
    # try to find bots using regular expressions
    try:
        test(b1, ua)
        test(b2, ua)
        test(b3, ua)
        test(b4, ua)
        test(b5, ua)
        test(b6, ua)
        test(b7, ua)
        test(b8, ua)
    except BotResult as e: return add_host(str(e), ip)
    # if the user-agent is very short, it's probably a bot except when it contain Mozilla or Opera
    if len(ua) < 40 and not "Mozilla" in ua and not "Opera" in ua:
        return add_host(ua.strip(), ip)
