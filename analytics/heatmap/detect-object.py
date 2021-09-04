#!/usr/bin/python3

from db_ingest import DBIngest
from db_query import DBQuery
from signal import signal, SIGTERM
from rec2db import Rec2DB
from runva import RunVA
from language import text
from threading import Event
from configuration import env
import traceback
import json
import os

scenario = env["SCENARIO"]
office = list(map(float, env["OFFICE"].split(",")))
dbhost = env["DBHOST"]
every_nth_frame = int(env["EVERY_NTH_FRAME"])

stop=Event()
myAlgorithm=""
version=0

def connect(sensor, location, uri, algorithm, algorithmName):
    try:
        rec2db=Rec2DB(sensor)
        rec2db.start()

        runva=RunVA("heatmap", version, stop=stop)
        runva.loop(sensor, location, uri, algorithm, algorithmName)

        rec2db.stop()
        raise Exception("VA exited. This should not happen.")

    except Exception as error:
        print(traceback.format_exc(), flush=True)

def quit_service(signum, sigframe):
    stop.set()

signal(SIGTERM, quit_service)
dba=DBIngest(host=dbhost, index="algorithms", office=office)
dbs=DBQuery(host=dbhost, index="sensors", office=office)

if scenario=="traffic":
    version = 1
    myAlgorithm="object-detection"
if scenario=="stadium":
    version = 2
    myAlgorithm="heatmap"

# register algorithm (while waiting for db to startup)
dba.wait(stop)
algorithm=dba.ingest({
    "name": text["heatmap"],
    "office": {
        "lat": office[0],
        "lon": office[1],
    },
    "status": "processing",
    "skip": every_nth_frame,
})["_id"]

# compete for a sensor connection
while not stop.is_set():
    try:
        print("Searching...", flush=True)
        for sensor in dbs.search("type:'camera' and status:'idle' or status:'disconnected' and algorithm='"+myAlgorithm+"' and office:["+str(office[0])+","+str(office[1])+"]"):
            try:
                # compete (with other va instances) for a sensor
                r=dbs.update(sensor["_id"],{"status":"streaming"},seq_no=sensor["_seq_no"],primary_term=sensor["_primary_term"])

                # stream from the sensor
                print("Connected to "+sensor["_id"]+"...",flush=True)
                connect(sensor["_id"],sensor["_source"]["location"],sensor["_source"]["url"],algorithm,sensor["_source"]["algorithm"])

                # if exit, there is somehting wrong
                r=dbs.update(sensor["_id"],{"status":"disconnected"})
                if stop.is_set(): break

            except Exception as e:
                print("Exception: "+str(e), flush=True)

    except Exception as e:
        print("Exception: "+str(e), flush=True)

    stop.wait(10)

# searching = 0
# while not stop.is_set():
#     try:
#         for sensor in dbs.search("type:'camera' and algorithm='"+myAlgorithm+"' and office:["+str(office[0])+","+str(office[1])+"] and url:*"):
#             botconfig_id = sensor["_source"]["botconfig_id"]

#             bot_id = {
#                 "botconfig_id":botconfig_id
#             }

#             _botconfig_id = None
#             write_flag = True

#             try:
#                 with open("/home/"+str(botconfig_id)+".json", "r") as data:
#                     _botconfig_id_data = json.load(data)
#                     _botconfig_id = _botconfig_id_data["botconfig_id"]
#                     print("_botconfig_id_data_botconfig_id_data",_botconfig_id)

#             except Exception as error:

#                 if _botconfig_id == None:
#                     for root, dirs, files in os.walk("botconfig/"):
#                         for file in files:
#                             if file.endswith(".json"):
#                                 write_flag = False
#                             else: write_flag = True

#                     if write_flag == True:
#                         with open("/home/"+str(botconfig_id)+".json", "w") as data:
#                             json.dump(bot_id, data)
#                             _botconfig_id = botconfig_id

            
#         if botconfig_id == _botconfig_id:
#             print("Searching...", flush=True)
#             searching += 1
#             if searching == 20:
#                 for sensor in dbs.search("type:'camera' and status:'streaming' and algorithm='"+myAlgorithm+"' and office:["+str(office[0])+","+str(office[1])+"] and url:*"):
#                     dbs.update(sensor["_id"],{"status":"idle"},seq_no=sensor["_seq_no"],primary_term=sensor["_primary_term"])
#                 print("sensor status is updated")    
                
#             for sensor in dbs.search("type:'camera' and status:'idle' or status:'disconnected' and algorithm='"+myAlgorithm+"' and office:["+str(office[0])+","+str(office[1])+"] and url:*"):
#                 try:
#                     # compete (with other va instances) for a sensor
#                     r=dbs.update(sensor["_id"],{"status":"streaming"},seq_no=sensor["_seq_no"],primary_term=sensor["_primary_term"])

#                     if sensor["_source"]["url"].split(":")[0] == "rtmp":
#                         if scenario=="traffic": version = 3
#                         if scenario=="stadium": version = 4

#                     # stream from the sensor
#                     print("Connected to "+sensor["_id"]+"...",flush=True)
#                     connect(sensor["_id"],sensor["_source"]["location"],sensor["_source"]["url"],algorithm,sensor["_source"]["algorithm"])
                   
#                     # if exit, there is somehting wrong
#                     r=dbs.update(sensor["_id"],{"status":"disconnected"})
#                     if stop.is_set(): break

#                 except Exception as e:
#                     print("Exception: "+str(e), flush=True)
#         else: print("YOUR BOT IS IN OCCUPIED POD....!")

#     except Exception as e:
#         print("Exception: "+str(e), flush=True)

#     stop.wait(10)


# delete the algorithm instance
# dba.delete(algorithm)

