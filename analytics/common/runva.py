#!/usr/bin/python3

from db_common import DBCommon
from db_query import DBQuery
from paho.mqtt.client import Client
from db_ingest import DBIngest
from threading import Event
from vaserving.vaserving import VAServing
from vaserving.pipeline import Pipeline
from configuration import env
import time
import traceback
import psutil

mqtthost = env["MQTTHOST"]
dbhost = env["DBHOST"]
dbmhost = env["DBMHOST"]
every_nth_frame = int(env["EVERY_NTH_FRAME"])
office = list(map(float, env["OFFICE"].split(",")))

class RunVA(object):
    def _test_mqtt_connection(self):
        print("testing mqtt connection", flush=True)
        mqtt = Client()
        while True:
            try:
                mqtt.connect(mqtthost)
                break
            except:
                print("Waiting for mqtt...", flush=True)
                time.sleep(5)
        print("mqtt connected", flush=True)
        mqtt.disconnect()
    
    def __init__(self, pipeline, version="2", stop=Event()):
        super(RunVA, self).__init__()
        self._test_mqtt_connection()

        self._pipeline = pipeline
        self._version = version
        self._db = DBIngest(host=dbhost, index="algorithms", office=office)
        self._db_activity = DBIngest(host = dbmhost, index="activity", office=office)
        self._stop=stop

    def stop(self):
        print("stopping", flush=True)
        self._stop.set()

    def loop(self, sensor, location, uri, algorithm, algorithmName, options={}, topic="analytics"):
        try:
            VAServing.start({
                'model_dir': '/home/models',
                'pipeline_dir': '/home/pipelines',
                'max_running_pipelines': 1,
            })

            try:
                source={
                    "type": "uri",
                    "uri": uri,
                }
                destination={
                    "type": "mqtt",
                    "host": mqtthost,
                    "clientid": algorithm,
                    "topic": topic
                }
                tags={
                    "sensor": sensor, 
                    "location": location, 
                    "algorithm": algorithmName,
                    "office": {
                        "lat": office[0], 
                        "lon": office[1]
                    },
                }
                parameters = {
                    "inference-interval": every_nth_frame,
                    "recording_prefix": "/tmp/rec/" + sensor
                }
                parameters.update(options)

                pipeline = VAServing.pipeline(self._pipeline, self._version)
                print("pipelinepipeline", self._pipeline)
                instance_id = pipeline.start(source=source,
                                         destination=destination,
                                         tags=tags,
                                         parameters=parameters)

                if instance_id is None:
                    raise Exception("Pipeline {} version {} Failed to Start".format(
                        self._pipeline, self._version))

                self._stop.clear()
                while not self._stop.is_set():
                    status = pipeline.status()
                    print(status, flush=True)

                    if status.state.stopped():
                        print("Pipeline {} Version {} Instance {} Ended with {}".format(
                            self._pipeline, self._version, instance_id, status.state.name), 
                            flush=True)
                        break

                    if status.avg_fps > 0 and status.state is Pipeline.State.RUNNING:
                        avg_pipeline_latency = status.avg_pipeline_latency
                        if not avg_pipeline_latency: avg_pipeline_latency = 0



                        try:
                            self._db.update(algorithm, {
                                "sensor": sensor,
                                "performance": status.avg_fps,
                                "latency": avg_pipeline_latency * 1000,
                                "cpu": psutil.cpu_percent(),
                                "memory": psutil.virtual_memory().percent,
                            })

                            try:
                                    
                                dbb = DBQuery(host = dbhost, index = "botconfigs", office=office)

                                # print("sensorsensor",sensor)
                                for botconfig in dbb.search("sensorId:'"+str(sensor)+"'"):
                                    activityId = botconfig["_source"]["activityId"]
                                    botId = botconfig["_source"]["botId"]
                                    kpisId = botconfig["_source"]["kpisId"]
                                    site_id = botconfig["_source"]["siteId"]
                                    nodeId = botconfig["_source"]["nodeId"]

                                    _dba = DBCommon(host = dbhost, index = "activities", office=office)
                                    activity_index = _dba.get(activityId)
                                    activity_name = activity_index["_source"]["uniqueName"]
                                    print("activity_nameactivity_name",activity_name)
                                    
                                    _dbb = DBCommon(host=dbhost, index="aividbots", office=office)
                                    aividbot_index = _dbb.get(botId)
                                    aividbot_name = aividbot_index["_source"]["name"]
                                    print("aividbot_nameaividbot_name",aividbot_name)

                                    _dbk = DBCommon(host=dbhost, index="kpis", office=office)
                                    kpi_index = _dbk.get(kpisId)
                                    kpi_name = kpi_index["_source"]["name"]
                                    print("kpi_namekpi_name",kpi_name)

                                    _dbs = DBCommon(host=dbhost, index="sites", office=office)
                                    site_index = _dbs.get(site_id)
                                    site_name = site_index["_source"]["name"]
                                    print("site_namesite_name",site_name)

                                    _dbn = DBCommon(host=dbhost, index="nodes", office=office)
                                    node_index = _dbn.get(nodeId)
                                    node_name = node_index["_source"]["name"]
                                    print("node_namenode_name",node_name)

                                    _dbs = DBCommon(host=dbhost, index="provisions", office=office)
                                    provision_index = _dbs.get(sensor)
                                    sensor_name = provision_index["_source"]["name"]
                                    print("sensor_namesensor_name",sensor_name)



                                self._db_activity.ingest({
                                        "name": aividbot_name,
                                        "office": {
                                            "lat": office[0],
                                            "lon": office[1],
                                        },
                                        "status": "connected",
                                        "skip": every_nth_frame,
                                        "sensor": sensor,
                                        "performance": status.avg_fps,
                                        "latency": avg_pipeline_latency * 1000,
                                        "cpu": psutil.cpu_percent(),
                                        "memory": psutil.virtual_memory().percent,
                                        "activity_name":activity_name,
                                        "sensor_name":sensor_name,
                                        "aividbot_name":aividbot_name,
                                        "kpi_name":kpi_name,
                                        "site_name":site_name,
                                        "node_name":node_name,
                                        "timestamp":int(time.time()) * 1000

                                    })["_id"]
                            except Exception as error:
                                print("wrong in activity ingest",error)

                        except:
                            print("Failed to update algorithm status", flush=True)
                            self._stop.set()
                            raise

                    self._stop.wait(3)

                self._stop=None
                pipeline.stop()
            except:
                print(traceback.format_exc(), flush=True)

            VAServing.stop()
        except:
            print(traceback.format_exc(), flush=True)

   