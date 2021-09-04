#!/usr/bin/python3

from db_ingest import DBIngest
import paho.mqtt.client as mqtt
from threading import Thread, Condition, Timer
from signal import signal, SIGTERM
from configuration import env
import traceback
import json

mqtthost = env["MQTTHOST"]
scenario = env["SCENARIO"]
dbhost = env["DBHOST"]
office = list(map(float, env["OFFICE"].split(",")))

class MQTT2DB(object):
    def __init__(self):
        super(MQTT2DB, self).__init__()

        #host
        print(" ### host__",dbhost)
        #office
        print("### office__",office)
        self._db = DBIngest(host=dbhost, index="analytics", office=office)
        print("### print step1------", self._db, flush=True)
        self._cache = []
        self._cond = Condition()

        self._mqtt = mqtt.Client()
        print("### step2 connected to mqtt client", flush=True)
        self._mqtt.on_message = self.on_message
        print("### step3 mqtt on message", flush=True)
        self._mqtt.on_disconnect = self.on_disconnect


    def loop(self, topic="analytics"):
        print("connecting mqtt", flush=True)
        timer = Timer(10, self._connect_watchdog)
        print("### step4 timer", timer, flush=True)
        timer.start()
        print("timer start", flush=True)
        while True:
            try:
                self._mqtt.connect(mqtthost)
                print("step5 mqtt connect", flush=True)
                break
            except:
                pass
        timer.cancel()

        print("### step6 mqtt connected", flush=True)

        self._stop = False
        Thread(target=self.todb).start()

        self._mqtt.subscribe(topic)
        print("### step7 mqtt subscribe called", flush=True)
        self._mqtt.loop_forever()
        

    def _connect_watchdog(self):
        print("quit due to mqtt timeout", flush=True)
        exit(-1)

    def _add1(self, item=None):
        self._cond.acquire()
        if item:
            self._cache.append(item)
        self._cond.notify()
        print("### step8 add1 function")
        self._cond.release()

    def stop(self):
        self._mqtt.disconnect()

    def on_disconnect(self, client, userdata, rc):
        self._stop = True
        print("on_disconnect", flush=True)
        self._add1()

    def on_message(self, client, userdata, message):
        try:

            r = json.loads(str(message.payload.decode("utf-8", "ignore")))
            print("### printing json", r,   flush=True)

            if "tags" in r:
                r.update(r["tags"])
                del r["tags"]

            if ("time" not in r) and ("real_base" in r) and ("timestamp" in r): 
                real_base=r["real_base"] if "real_base" in r else 0
                r["time"] = int((real_base + r["timestamp"]) / 1000000)
                print("r2", r, flush=True)

            if "objects" in r and scenario == "traffic":
                r["nobjects"] = int(len(r["objects"]))
                print("r3", r, flush=True)
            if "objects" in r and scenario == "stadium":
                r["count"] = {"people": len(r["objects"])}
                print("r4", r, flush=True)
            if "count" in r:
                r["nobjects"] = int(max([r["count"][k] for k in r["count"]]))

        except:
            print(traceback.format_exc(), flush=True)
            print("wrong in sending r", flush=True)
        finally:
            print("### on_message is running__")

        self._add1(r)

    def todb(self):
        while not self._stop:
            print("### printing1 todb", flush=True)
            self._cond.acquire()
            print("### printing2 todb", flush=True)

            self._cond.wait()
            print("### printing3 todb", flush=True)
            bulk = self._cache
            self._cache = []
            self._cond.release()

            try:
                print("### Ingesting todb", flush=True)
                print("### bulk__",bulk)
                self._db.ingest_bulk(bulk)
                print("### Ingested todb", flush=True)
            except:
                print(traceback.format_exc(), flush=True)
                print("wrong in sending to db", flush=True)
            finally:
                print("### todb function running__")


mqtt2db = MQTT2DB()


def quit_service(signum, sigframe):
    mqtt2db.stop()
    print("stopping", flush=True)


signal(SIGTERM, quit_service)
mqtt2db.loop()
