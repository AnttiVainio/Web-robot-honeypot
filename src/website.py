import cherrypy
import time
import os
import traceback

from cherrypy.process.plugins import Monitor
from database import Database
from database_visits import DatabaseVisits
from own_ip import OwnIP
from botname import get_bot_name

# Disabling debug removes stack traces from 500-pages and removes some whitespace from html/css/js
DEBUG = False
# Cherrypy https settings are at the end of this file
HTTPS = False
LOCALHOST = False
# Use the X-Forwarded-For header to get the ip address of the connecting client
# Set to true when this server is run behind a proxy server that sets the X-Forwarded-For header
USE_X_FORWARDED_FOR = False

# The domain and the ports are ignored in some stats
LISTEN_PORT = 8090 # the actual port that is listened
PUBLIC_PORTS = 80, 8090 # only ignored in some stats
DOMAINS = "manaatti.dy.fi", "bottest.dy.fi" #also just ignored in some stats
IGNOREDCOOKIES = "dyvisit",
# The index and error pages have random names so that these pages cannot (easily) be directly queried
#   in order to see if clients try to request some index or error pages
# These names are not visible in the front end
INDEX = "index_t5dCCpikeZ.html"
ERROR = "error_2M9nnuFKiN.html"
# Add some delay before responding to requests
# Would not be needed if running on a powerful server machine
DELAY = 0.1
DBUPDATE_FREQ = 3600
IPUPDATE_FREQ = 7201

print("Using CherryPy version", cherrypy.__version__)
print("Debug mode is", "enabled" if DEBUG else "disabled")
print("Using", "secure HTTPS" if HTTPS else "plain HTTP")

class Website():
    def __init__(self):
        # set general and visitor databases
        self.database = Database()
        self.visitors = DatabaseVisits()
        self.own_ip = OwnIP()
        # save database contents when CherryPy stops
        cherrypy.engine.subscribe('stop', self.database.save_data)
        cherrypy.engine.subscribe('stop', self.visitors.save_data)
        # update and save databases and own IP periodically
        Monitor(cherrypy.engine, self.database.update_data, frequency = DBUPDATE_FREQ).subscribe()
        Monitor(cherrypy.engine, self.visitors.save_data, frequency = DBUPDATE_FREQ + 1).subscribe()
        Monitor(cherrypy.engine, self.own_ip.update_ip, frequency = IPUPDATE_FREQ).subscribe()
        # favicon
        with open(os.path.join("content", "favicon.ico"), "rb") as file:
            self.favicon = file.read()
        # 'static' files
        self.webpages = {
            INDEX : {"type":"text/html"},
            ERROR : {"type":"text/html"},
            "robots.txt" : {"type":"text/plain"},
            "stylesheet.css" : {"type":"text/css"},
            "content.js" : {"type":"text/javascript"},
        }
        for i in self.webpages:
            with open(os.path.join("content", i), "rb") as file:
                data = file.read()
                if not DEBUG:
                    # optimize by removing some unneeded whitespace
                    # this will break with single line comments though
                    data = data.replace(b'\t',b'')
                    data = data.replace(b'\r',b'')
                    data = data.replace(b'\n',b'')
                self.webpages[i]["data"] = data

    # Returns true if the address is the server http address without wrong ports or anything extra
    def is_server_address(self, address):
        split = address.split("/")
        # check for malformed address or query string
        if len(split) < 3 or len(split) > 4: return False
        if len(split) == 4 and split[3] != "": return False
        # check port
        try: port = int(split[2].split(":")[1])
        except IndexError: port = 443 if HTTPS else 80
        # public address
        for i in DOMAINS:
            if i in split[2]:
                return port in PUBLIC_PORTS
        if split[2].startswith(self.own_ip.get_ip()):
            return port in PUBLIC_PORTS
        # local address
        if split[2].startswith("localhost") or\
           split[2].startswith("127.") or\
           split[2].startswith("192.168."):
            return port in PUBLIC_PORTS
        return False

    # Add a bot to the database, typ is the type of web page that the bot requested
    def addbot(self, botname, typ):
        if botname: self.database.add_value("bot", [botname, typ])

    # This will hide the stack trace by providing a custom 500-page
    def hide_error(self, ex):
        time.sleep(DELAY * 0.5)
        if DEBUG: raise ex
        else:
            traceback.print_exc()
            cherrypy.response.status = 500
            cherrypy.response.headers['Content-Type'] = self.webpages[ERROR]["type"]
            return self.webpages[ERROR]["data"]

    # Handle login requests
    def l(self, **kwargs):
        time.sleep(DELAY * 0.5)
        if "login" in kwargs:
            self.database.add_value("username", kwargs["login"])
        if "password" in kwargs:
            self.database.add_value("password", kwargs["password"])
        raise cherrypy.HTTPRedirect("/")

    # Handle message posting requests
    def p(self, **kwargs):
        time.sleep(DELAY * 0.5)
        tmp = dict()
        if "title" in kwargs:
            tmp["t"] = kwargs["title"]
        if "message" in kwargs:
            tmp["m"] = kwargs["message"]
        if len(tmp): self.database.add_value("message", tmp)
        raise cherrypy.HTTPRedirect("/")

    # Return database content as json
    def c(self):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return self.database.get_data()

    # Automatic favicon
    @cherrypy.expose
    def favicon_ico(self, *args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'image/x-icon'
        return self.favicon

    @cherrypy.expose
    def default(self, *args, **kwargs):
        try:
            time.sleep(DELAY)
            req = cherrypy.request
            headers = req.headers

            # check if the query is the address to this server
            server_address = self.is_server_address(req.base)

            # get the ip address of the connecting client
            remote_ip = ""
            if USE_X_FORWARDED_FOR:
                if "X-Forwarded-For" in headers: remote_ip = headers["X-Forwarded-For"]
            else: remote_ip = req.remote.ip

            # bots
            botname = None
            if "User-Agent" in headers:
                botname = get_bot_name(headers["User-Agent"], remote_ip)
            # cookies
            for i in req.cookie.keys():
                if i not in IGNOREDCOOKIES:
                    self.database.add_value("cookie", i + " = " + req.cookie[i].value)
            # referer
            if "Referer" in headers:
                refr = headers["Referer"]
                # don't include the server addresses in referers
                if not self.is_server_address(refr):
                    self.database.add_value("referer", refr)

            # show the other website content when the address is very correct
            if server_address and len(args) == 1:
                if args[0] == "l":
                    self.addbot(botname, "l") #login
                    self.l(**kwargs)
                elif args[0] == "p":
                    self.addbot(botname, "m") #message
                    self.p(**kwargs)
                elif len(kwargs) == 0:
                    if args[0] == "c":
                        self.addbot(botname, "d") #data
                        return self.c()
                    elif args[0] in self.webpages:
                        if args[0] == "robots.txt": self.addbot(botname, "r") #robot
                        elif args[0] == "stylesheet.css": self.addbot(botname, "s") #stylesheet
                        elif args[0] == "content.js": self.addbot(botname, "j") #javascript
                        cherrypy.response.headers['Content-Type'] = self.webpages[args[0]]["type"]
                        return self.webpages[args[0]]["data"]

            # save visitor
            self.visitors.add_visitor(remote_ip)

            # query - ignore requests for /mobile and /m
            #   because legit web crawlers seem to randomly try that
            if not (server_address and len(args) == 1 and len(kwargs) == 0 and (args[0] == "mobile" or args[0] == "m")):
                val = ""
                if not server_address:
                    try: val+= req.base.split("/")[2]
                    except IndexError: val+= req.base
                if len(args) > 0 or len(kwargs) > 0:
                    val+= req.path_info
                    if req.query_string: val+= "?" + req.query_string
                if val:
                    self.addbot(botname, "?") #bot requested an unknown page
                    self.database.add_value("query", val)
                else: self.addbot(botname, "i") #index

            cherrypy.response.headers['Content-Type'] = self.webpages[INDEX]["type"]
            return self.webpages[INDEX]["data"]

        # re-raise redirections
        except cherrypy.HTTPRedirect as ex: raise ex
        # handle other exceptions
        except Exception as ex: return self.hide_error(ex)

cherrypy_configs = {
    'server.socket_host' : '127.0.0.1' if LOCALHOST else '0.0.0.0',
    'server.socket_port' : LISTEN_PORT,
    'engine.autoreload.on' : False,
    'response.headers.server' : '',
}
if HTTPS: cherrypy_configs.update({
    'server.ssl_module' : 'builtin',
    'server.ssl_certificate' : 'cert.pem',
    'server.ssl_private_key' : 'privkey.pem',
})
cherrypy.config.update(cherrypy_configs)

cherrypy.quickstart(Website(), '/')
