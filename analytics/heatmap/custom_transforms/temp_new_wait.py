from re import T
import re
import gstgva
import numpy as np
import json
from configuration import env
import os, sys, traceback
import logging
import datetime
import time
from notification import notification
from centroidtracker import CentroidTracker
from shapely.geometry import Point, Polygon
from db_query import DBQuery
from db_common import DBCommon
from db_ingest import DBIngest


office = list(map(float, env["OFFICE"].split(",")))
print("officeoffice",office)
dbhost = env["DBHOST"]

class WaitTime:

    def __init__(self):
       
        self.tracker = CentroidTracker(maxDisappeared=30, maxDistance=90)
        self._db_analytics = DBIngest(host = dbhost, index="analytics", office=office)
       

    def fetch_data(self, BOTNAME):

        _path1=os.getcwd()
        _path2=os.path.join(_path1,"video/")
        os.makedirs(os.path.dirname(_path2), exist_ok=True)

        botconfig_ids = []
        dbb = DBQuery(host = dbhost, index = "botconfigs", office=office)
        for botconfig in dbb.search_without_office("algorithm:'"+str(BOTNAME)+"'"):
            botconfig_id = botconfig["_id"]
            botconfig_ids.append(botconfig_id)
        print("botconfig_ids",botconfig_ids,flush=True)


        json_data = []    
        # cnt = 0

        for botconfig_id in botconfig_ids:
            
            sensor_ids = []
            _dbb = DBCommon(host=dbhost, index="botconfigs", office=office)
            botconfig_index = _dbb.get_without_office(botconfig_id)
            sensor_ids.append(botconfig_index["_source"]["sensorId"])
            _site_id = botconfig_index["_source"]["siteId"]
            print("sensor_ids",sensor_ids,flush=True)

            rtspurls = []
            _dbp = DBCommon(host=dbhost, index="provisions", office=office)
            provisions_index = _dbp.get(sensor_ids[0])
            rtspurls.append(provisions_index["_source"]["rtspurl"])
            sensor_name = provisions_index["_source"]["name"]
            start_time = provisions_index["_source"]["startTime"]

            _dbs = DBCommon(host=dbhost, index="sites", office=office)
            sites_index = _dbs.get(_site_id)
            site_name = sites_index["_source"]["name"]

            print("sensor_ids",sensor_ids,flush=True)
            print("rtspurls",rtspurls, flush=True)
            print("site_name", site_name)


            coordinates = []
            zone_names = []
            dbz = DBQuery(host=dbhost, index="zones", office=office)
            
            for zones in dbz.search_without_office("botName:'"+str(BOTNAME)+"' and sensorId:'"+str(sensor_ids[0])+"'"):
                coordinate = zones["_source"]["coordinates"][0] 
                coordinates.append(coordinate)
                zone_name = zones["_source"]["name"]
                zone_names.append(zone_name)
            print("coordinates",coordinates, flush=True)
            print("zone_names",zone_names, flush=True)
        

            dbn = DBQuery(host = dbhost, index = "nodes", office=office)
            
            for nodes in dbn.search("coordinates:'"+str(office)+"'"):
                node_name = nodes["_source"]["name"]
            print("node_name",node_name, flush=True)

        
            _sensors = []      
            for sensors_num in range(len(sensor_ids)):
                _url = rtspurls[sensors_num]
                rois = []
                for rois_num in range(len(coordinates)):
                    
                   
                    rois.append({
                        "roi_box":coordinates[rois_num],
                        "roi_name":zone_names[rois_num],
                    })
                _sensors.append({
                    "url":_url,
                    "camera_id":sensor_ids[sensors_num],
                    "roi":rois,
                    "sensor_name":sensor_name,
                    "start_time":start_time
                })


            json_data.append({
            "sensors":_sensors,
            "botconfig_id":botconfig_id,
            "site_id":_site_id,
            "site_name":site_name,
            "node_name":node_name
            })
            # cnt +=1

        botconfig_data = {
            "botconfig_data":json_data
        }
        print("botconfig_databotconfig_databotconfig_data",botconfig_data,flush=True)

        return botconfig_data

    def object_monitor(self, zonename, objectid, curr_time):

        try:
            # print("__________try_______________________")

            with open("/home/custom_transforms/"+"object_monitor"+str(zonename)+".json","r") as object_id_list:
                data = json.load(object_id_list)
              
        except:
            # print("__________except_______________________")
            _object_ids = []
            _dtime = dict()
            _average_time = dict()
            data = {
                "object_id_list":_object_ids,
                "dtime":_dtime,
                "average_time":_average_time
            }
            with open("/home/custom_transforms/"+"object_monitor"+str(zonename)+".json","w") as object_id_list:
                json.dump(data,object_id_list)

        if objectid not in data["object_id_list"]:
            # print("if_________",flush=True)
            data["object_id_list"].append(objectid)
            data["dtime"][str(objectid)] = curr_time
            data["average_time"][str(objectid)] = 0
        
        else:
            # print("else_______",flush=True)
            old_time = data["dtime"][str(objectid)]
            time_diff = curr_time - old_time
            data["average_time"][str(objectid)] += time_diff
            data["dtime"][str(objectid)] = curr_time

        with open("/home/custom_transforms/"+"object_monitor"+str(zonename)+".json","w") as object_id_list:
            json.dump(data,object_id_list)

        # print("datadatadata",data, flush=True)
        
        return data["average_time"][str(objectid)]

    def last_time(self):
        json_time = {"last_time":time.time()}

        try:
            with open("/home/jsontime.json", "r") as data:
                json_time = json.load(data)

                last_time = json_time["last_time"]

                with open("/home/jsontime.json", "w") as data:
                    json.dump(json_time, data)

        except:
            with open("/home/jsontime.json", "w") as data:
                json.dump(json_time, data)

                last_time = json_time["last_time"]
                
        return last_time

    def data_storage(self, zonename, wait_objects, curr_time, last_time, timelimit):

        send_data_storage = False
        time_length = (curr_time - float(last_time))
        try:
            with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","r") as object_id_list:
                data = json.load(object_id_list)
        except:
            
            data = {
                "wait_objects":[],
                "start_time":time.time()
            }

            with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","w") as object_id_list:
                json.dump(data,object_id_list)

        # data["start_time"] += time_length

        if len(wait_objects) > 0:
            for _object in wait_objects:
                data["wait_objects"].append(_object)

        with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","w") as object_id_list:
            json.dump(data,object_id_list)

        wait_objects_storage = data["wait_objects"]
        start_time = data["start_time"]
        time_diff = curr_time - start_time
        if time_diff > timelimit:
            send_data_storage = True
            data["start_time"] = time.time()
            data["wait_objects"] = []

            with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","w") as object_id_list:
                json.dump(data,object_id_list)

        return [send_data_storage, wait_objects_storage, time_diff]
            
    # def dynamic

    def process_frame(self, frame):
        try:
            messages = list(frame.messages())
            if len(messages) > 0:       #checking if frame message is not empty, if it is empty it will move to next frame
                try:
                    BOTNAME = "heatmap"
                    new_data = self.fetch_data(BOTNAME)
                except Exception as error:
                    print("wrong in fetch_data", error, flush=True)
            
                
                for botconfig_data in new_data["botconfig_data"]:
                    botConfigId = botconfig_data["botconfig_id"]
                    siteId = botconfig_data["site_id"]
                    site_name = botconfig_data["site_name"]
                    print("site_namesite_name",site_name)
                    node_name = botconfig_data["node_name"]
                    botName = BOTNAME
                    checklist = "None"

                    if len(messages)>0:
                        try:
                                
                            rects = []
                            output_centroid = dict()
                            messages=list(frame.messages())
                            # if len(messages)>0:     # checking if the frame message is not empty and loading in json_msg
                            json_msg = json.loads(messages[0])
                            for i in json_msg:      # getting all detcted object's coordinates
                                if i=='objects':
                                    dic=json_msg[i]
                                    for j in range(len(dic)):
                                        if dic[j]['detection']['label']=='person':      # checking if detected object is person and then storing it's coordinates in rects list
                                            x_max=dic[j]['x']+dic[j]['w']
                                            y_max=dic[j]['y']+dic[j]['h']
                                            x=dic[j]['x']
                                            y=dic[j]['y']
                                            rects.append([x,y,x_max,y_max])
                                    break
                            # else:
                            #     json_msg={}
                            
                        
                        except Exception as error:
                            print("wrong in starting:{}".format(error),flush=True)

                        data = botconfig_data

                        for i in data['sensors']:
                        
                            sensorId = i["camera_id"]
                            sensor_name = i["sensor_name"]
                            start_time = i["start_time"]
                            zone_cnt = 0
                            for zone_ in i["roi"]:

                                new_rects = []

                                roi_box = zone_["roi_box"]
                                roiName = zone_["roi_name"]
                                print("roiname__________1",roiName)
                                    
                                try:
                                    for rect in rects:      # iterating through rects and checking person is in roi or not 
                                        startX, startY, endX, endY = rect
                                        cX = int((startX + endX) / 2.0)
                                        cY = int((startY + endY) / 2.0)
                                        info = self.inroi(cX, cY, roi_box)
                                        if info==True:      # if person is in roi then storing rect in new_rects
                                            new_rects.append(rect)
                                except Exception as error:
                                    print("wrong in inroi:{}".format(error),flush=True)
                                    

                                try:
                                
                                    objects = self.tracker.update(new_rects)        # getting objectId for all person in roi
                                    # print("objectsobjects",objects, len(new_rects))

                                    wait_objects = []
                                    for (objectId, centroid) in objects.items(): # getting individual objectId of a person
                                        output_centroid = dict()
                                        cX, cY = centroid
                                        curr_time = time.time()

                                        object_monitor = self.object_monitor(roiName, objectId, curr_time)
                                        if object_monitor > 10:
                                        
                                            output_centroid['X'] = int(cX)
                                            output_centroid['Y'] = int(cY)
                                            output_centroid['Id'] = int(objectId)
                                            output_centroid["unique"] = str(cX) +" + "+str(cY)
                                            # print("ouput_centroid  ", output_centroid,  flush=True)
                                            wait_objects.append(output_centroid)
                                        
                                    # print("wait_objects", wait_objects, roiName, flush=True)
                                
                                except Exception as error:
                                    print("wrong in tracker:{}".format(error),flush=True)  

                                # if len(wait_objects)>0:

                                dump_storage_data = self.data_storage(roiName, wait_objects, curr_time, self.last_time(), 300)
                                print("__________________do not dump_______________________",dump_storage_data[0], dump_storage_data[2])
                                if dump_storage_data[0] == True:
                                    print("________x____x______dump_______x________x________",dump_storage_data[0], dump_storage_data[1], dump_storage_data[2])
                                

                                    if start_time == None:
                                        new_time = curr_time * 1000 # for live streaming
                                    else:
                                        new_time = start_time + (curr_time-float(self.last_time())) # for simulation


                                    self._db_analytics.ingest(
                                        {
                                            "new_time":new_time,
                                            "count":len(dump_storage_data[1]),
                                            "coordinates":dump_storage_data[1],
                                            "siteId":siteId,
                                            "roiName":roiName,
                                            "botName":botName,
                                            "checklist":checklist,
                                            "botConfigId":botConfigId,
                                            "sensorId":sensorId
                                        }
                                    )["_id"]

                                    # if start_time == None:
                                    #     json_msg["new_time"] = curr_time * 1000 # for live streaming
                                    # else:
                                    #     json_msg["new_time"] = start_time + (curr_time-float(self.last_time())) # for simulation
                                    # json_msg["count"] = len(dump_storage_data[1])
                                    # json_msg["coordinates"] = dump_storage_data[1]
                                    # json_msg["siteId"] = siteId
                                    # json_msg["roiName"] = roiName
                                    # json_msg["botName"] = botName
                                    # json_msg["checklist"] = checklist
                                    # json_msg["botConfigId"] = botConfigId
                                    # json_msg["sensorId"] = sensorId 

                                    # print("messages___1",messages[0])
                                    try:
                                        frame.remove_message(messages[0]) 
                                    except:
                                        ignore = None
                                        print("dont remove for ", roiName)

                                    print("roiname__________2",roiName)
                                    # print("messages___2",messages[0])
                                
                                    # frame.add_message(json.dumps(json_msg))
                                    # try:
                                #     frame.remove_message(messages[0]) 
                                # except:
                                #     ignore = None

                                else:
                                    try:
                                        frame.remove_message(messages[0]) 
                                    except:
                                        ignore = None  

                           

                                  

                                
                            

        except Exception as error:
            print("wrong in processing_frame:{}".format(error), flush=True)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, flush=True)
            print(traceback.format_exc(), flush=True)
            # or
            print(sys.exc_info()[2], flush=True)
        return True
    

    def inroi(self,x,y,line):       # function checks whether the x and y point of a person detected is in roi, return True or False
        k=line
        p1 = Point(x,y)
        coords = [(k[0],k[1]), (k[2],k[3]), (k[4],k[5]), (k[6],k[7])]
        poly = Polygon(coords)
        info=p1.within(poly)
        return info
    
    def convert(self, seconds):     # function converts the waitTime from seconds to h:m:s format
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        
        return "%d:%02d:%02d" % (hour, minutes, seconds)
