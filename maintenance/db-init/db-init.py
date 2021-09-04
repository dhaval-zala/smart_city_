#!/usr/bin/python3

from signal import SIGTERM, signal
from db_ingest import DBIngest
from provision import Provision
from configuration import env
import traceback
import requests
import time
import json
import re

dbhost=env["DBHOST"]
dbchost=env.get("DBCHOST",None)
dbmhost = env.get("DBMHOST")
office=list(map(float,env["OFFICE"].split(",")))
replicas=list(map(int,env["REPLICAS"].split(",")))

def quit_service():
    exit(143)
    print("not quiting service=---------------------")

#signal(SIGTERM, quit_service)

# wait until DB is ready
dbs=DBIngest(index="sensors", office=office, host=dbhost)
while True:
    try:
        if dbs.health(): break
    except:
        print("Waiting for DB...", flush=True)
    time.sleep(1)
    
officestr=dbs.office()
settings={
    "offices": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "location": { "type": "geo_point", },
            },
        },
    },
    "provisions"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "location": { "type": "geo_point", },
                "office": { "type": "geo_point", },
                # "ip": { "type": "ip_range", },
                "rtmpid": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
            },
        },
    },
    "sensors"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point", },
                "location": { "type": "geo_point", },
                # "ip": { "type": "ip_range", },
                "type": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "subtype": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "algorithm": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "address": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "mnth": { "type": "float" },
                "alpha": { "type": "float" },
                "fovh": { "type": "float" },
                "fovv": { "type": "float" },
                "theta": { "type": "float" },
            },
        },
    },
    "sensors": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point", },
                "location": { "type": "geo_point", },
                # "ip": { "type": "ip_range", },
                "type": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "subtype": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "algorithm": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "address": {
                    "type" : "text",
                    "fields" : {
                        "keyword" : {
                            "type" : "keyword",
                            "ignore_above" : 256,
                        },
                    },
                },
                "mnth": { "type": "float" },
                "alpha": { "type": "float" },
                "fovh": { "type": "float" },
                "fovv": { "type": "float" },
                "theta": { "type": "float" },
            },
        },
    },
    "activity"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "timestamp": { "type": "date" },
            },
        },
    },
    "activity": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "timestamp": { "type": "date" },
            },
        },
    },
    "recordings"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "time": { "type": "date" },
            },
        },
    },
    "recordings": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "time": { "type": "date" },
            },
        },
    },
    "algorithms"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
            },
        },
    },
    "analytics"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "location": { "type": "geo_point" },
                "time": { "type": "date" },
                "objects": { "type": "nested" },
            },
        },
    },
    "analytics": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "location": { "type": "geo_point" },
                "time": { "type": "date" },
                "objects": { "type": "nested" },
            },
        },
    },
    "metadata"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "location": { "type": "geo_point" },
                "time": { "type": "date" },
                "new_time": { "type": "date" },
                "objects": { "type": "nested" },
            },
        },
    },
    "metadata": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "location": { "type": "geo_point" },
                "time": { "type": "date" },
                "new_time": { "type": "date" },
                "objects": { "type": "nested" },
            },
        },
    },
    "alerts"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "time": { "type": "date" },
                "location": { "type": "geo_point" },
                "office": { "type": "geo_point" },
            },
        },
    },
    "services"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
            },
        },
    }
}

worker_node_api_indexes = {
    
    "botconfigs"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "botconfigs": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "notification_rules"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "rules"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "rules": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "responsetypes"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "responsetypes": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "notification_responsetypes"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "kpis"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "kpis": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "zones"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "zones": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "schedules"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "schedules": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "aividbots"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "activities"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "notification_templates"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "notificationconfigs"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "nodes"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "nodes": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    },
    "sites"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "timestamp": { "type": "date" },
            },
        },
    }
}

activity_settings = {
    "activity"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "timestamp": {
            "type": "date",
            "format": "yyyy-MM-dd HH:mm:ss"
        }
            }
        }
    },
    "activity": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                "office": { "type": "geo_point" },
                "timestamp": {
            "type": "date",
            "format": "yyyy-MM-dd HH:mm:ss"
        }
            }
        }
    }
}

sensor_summary_settings = {
    "sensor_summary"+officestr: {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[1],
            },
        },
        "mappings": {
            "properties": {
                 "timestamp": {
            "type": "date",
            "format": "yyyy-MM-dd HH:mm:ss"
        }
            }
        }
    },
    "sensor_summary": {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": replicas[0],
            },
        },
        "mappings": {
            "properties": {
                   "timestamp": {
            "type": "date",
            "format": "yyyy-MM-dd HH:mm:ss"
        }
            }
        }
    }
}

_requests=requests.Session()
while True:
    try:
        # delete office specific indexes (to start the office afresh)
        for index in settings:
            if index.endswith(officestr):
                print("Do not Delete index "+index , flush=True)
                #r=_requests.delete(dbhost+"/"+index)

        # initialize db index settings
        _include_type_name={"include_type_name":"false"}
        for index in settings:
            print("Initialize index "+index, flush=True)
            host=dbhost if index.endswith(officestr) else dbchost
            if host:
                r=_requests.put(host+"/"+index,json=settings[index],params=_include_type_name)
                print(r.json(), flush=True)

        officeinfo=Provision(officestr)

        if dbchost:
            print("Register office {}".format(office), flush=True)
            dbo_c=DBIngest(index="offices",office="",host=dbchost)
            dbo_c.ingest(officeinfo, id1=officestr)

        print("Signal starting up", flush=True)
        dbs.ingest({"type":"startup"})


        #################### worker node indexes ####################

        # initialize db index settings
        _include_type_name={"include_type_name":"false"}
        for index in worker_node_api_indexes:
            print("Initialize index "+index, flush=True)
            host=dbhost if index.endswith(officestr) else dbchost
            if host:
                r=_requests.put(host+"/"+index,json=worker_node_api_indexes[index],params=_include_type_name)
                print(r.json(), flush=True)

        ############################################################


        ####################  master db  ########################
        
        # initialize db index settings
        _include_type_name={"include_type_name":"false"}
        for index in activity_settings:
            print("Initialize index "+index, flush=True)
            host=dbmhost if index.endswith(officestr) else dbchost
            if host:
                r=_requests.put(host+"/"+index,json=activity_settings[index],params=_include_type_name)
                print(r.json(), flush=True)

        _include_type_name={"include_type_name":"false"}
        for index in sensor_summary_settings:
            print("Initialize index "+index, flush=True)
            host=dbmhost if index.endswith(officestr) else dbchost
            if host:
                r=_requests.put(host+"/"+index,json=sensor_summary_settings[index],params=_include_type_name)
                print(r.json(), flush=True)

        ############################################################
        break

    except Exception as e:
        print(traceback.format_exc(), flush=True)
        print("Waiting for DB...", flush=True)

    time.sleep(1)

print("DB Initialized", flush=True)

while True:
    time.sleep(10000)

