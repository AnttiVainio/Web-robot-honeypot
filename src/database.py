import json
import time
import re
import os
import threading
from collections import defaultdict

# Format of the data dict:
#
# { type : [ largesttime,
#            { time1 : value1,
#              time2 : value2,
#              ...
#            }
#          ],
#   ...
# }

# Amount of returned unique values
# Double the amount is kept in the database
RETURNSIZE = 30
# Hard limit the size of database
HARDLIMIT = 3000
# Maximum length of a single value in database
MAXVALUELEN = 2000

# This function is used to simplify data strings before comparing them with each other
#   this is done to match similar strings together when counting hits
def simplify(s):
    return re.sub(r'\d', r'0', s).lower()

class Database:
    def __init__(self):
        print("    DATABASE: Loading database data from data.dat")
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(os.path.join("data", "data.dat")) as file:
                self.data = json.load(file)
        except IOError:
            self.data = dict()
        # lock is needed because update_data is run periodically in a thread
        self.data_lock = threading.Lock()
        self.changed = True
        self.update_data(False)
        # can be used to remove certain data
        #del self.data["bot"]

    # Called in a thread
    def update_data(self, save = True):
        dat = dict()
        # dictionary for holding the set of pages (e.g. html, css, js) each bot requested
        dat["botreq"] = defaultdict(dict)
        size = 0
        with self.data_lock:
            # only run when there is new data
            if not self.changed: return
            self.changed = False
            print("    DATABASE: Updating data")
            # handle database data
            for i in self.data:
                dat[i] = defaultdict(int) #this is returned in get_data
                limit = set()
                size+= len(self.data[i][1]) #calc old size here
                # sort newest first
                data_sort = sorted(self.data[i][1].items(), reverse = True)
                # this dict is used to connect a simplified string to one of the original ones
                translation = dict()
                amount = 0
                for j in data_sort:
                    amount+= 1
                    # hard limit amount by throwing oldests ones away
                    if amount > HARDLIMIT: del self.data[i][1][j[0]]
                    else:
                        # get value - j[1] is list only for bots, the second value is the requested page
                        if type(j[1]) is list: value = j[1][0]
                        else: value = j[1]
                        simple = simplify(value)
                        # add value
                        if simple in translation:
                            dat[i][translation[simple]]+= 1
                        elif len(dat[i]) < RETURNSIZE:
                            dat[i][value]+= 1
                            # create translation from the simplified version to this version
                            # other strings with same simplified version will change to this version
                            #   when counting hits
                            translation[simple] = value
                        # handle the requested pages by bots (e.g. html, css, js)
                        if type(j[1]) is list and simple in translation:
                            try: dat["botreq"][translation[simple]].add(j[1][1])
                            except AttributeError:
                                dat["botreq"][translation[simple]] = set([j[1][1]])
                        # limiting database size
                        if len(limit) < RETURNSIZE * 2:
                            limit.add(simple)
                        # limit unique values
                        elif simple not in limit:
                            del self.data[i][1][j[0]]
            # misc data
            dat["dbsize"] = size
            print("    DATABASE: Database size is", size)
            # convert sets to lists
            for i in dat["botreq"]:
                dat["botreq"][i] = list(dat["botreq"][i])
            # set returned data for get_data
            self.ret_data = json.dumps(dat).encode()
        # save data
        if save: self.save_data()

    def add_value(self, typ, value):
        currenttime = int(time.time())
        # limit data length
        if type(value) is dict:
            for i in value:
                if len(value[i]) > MAXVALUELEN:
                    value[i] = value[i][:MAXVALUELEN] + "..."
            value = json.dumps(value)
        elif type(value) is list:
            if len(value[0]) > MAXVALUELEN: value[0] = value[0][:MAXVALUELEN] + "..."
        elif len(value) > MAXVALUELEN: value = value[:MAXVALUELEN] + "..."
        # save
        with self.data_lock:
            self.changed = True
            if not typ in self.data:
                self.data[typ] = [currenttime - 1, dict()]
            # the time value has to always grow
            newtime = max(self.data[typ][0] + 1, currenttime)
            self.data[typ][0] = newtime
            self.data[typ][1][str(newtime)] = value

    def get_data(self):
        with self.data_lock:
            return self.ret_data

    def save_data(self):
        with self.data_lock:
            print("    DATABASE: Saving database data to data.dat")
            with open(os.path.join("data", "data.dat"), "w") as file:
                json.dump(self.data, file)
