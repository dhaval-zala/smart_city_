from re import M, T
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
       
        self.tracker = CentroidTracker(maxDisappeared=50, maxDistance=200)
        self._db_metadata = DBIngest(host = dbhost, index="metadata", office=office)
       

    def fetch_data(self, BOTNAME):

        _path1=os.getcwd()
        _path2=os.path.join(_path1,"video/")
        os.makedirs(os.path.dirname(_path2), exist_ok=True)

        botconfig_ids = []
        dbb = DBQuery(host = dbhost, index = "botconfigs", office=office)
        for botconfig in dbb.search("algorithm:'"+str(BOTNAME)+"'"):
            botconfig_id = botconfig["_id"]
            botconfig_ids.append(botconfig_id)
        print("botconfig_ids",botconfig_ids,flush=True)


        json_data = []    
        # cnt = 0

        for botconfig_id in botconfig_ids:
            
            sensor_ids = []
            _dbb = DBCommon(host=dbhost, index="botconfigs", office=office)
            botconfig_index = _dbb.get(botconfig_id)
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
            
            for zones in dbz.search("botName:'"+str(BOTNAME)+"' and sensorId:'"+str(sensor_ids[0])+"'"):
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


        return botconfig_data

    def object_monitor(self, zonename, objectid, curr_time):

        try:

            with open("/home/custom_transforms/"+"object_monitor"+str(zonename)+".json","r") as object_id_list:
                data = json.load(object_id_list)
              
        except:
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
            data["object_id_list"].append(objectid)
            data["dtime"][str(objectid)] = curr_time
            data["average_time"][str(objectid)] = 0
        
        else:
            old_time = data["dtime"][str(objectid)]
            time_diff = curr_time - old_time
            data["average_time"][str(objectid)] += time_diff
            data["dtime"][str(objectid)] = curr_time

        with open("/home/custom_transforms/"+"object_monitor"+str(zonename)+".json","w") as object_id_list:
            json.dump(data,object_id_list)
        
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

    def data_storage(self, zonename, wait_objects, curr_time, timelimit):

        send_data_storage = False
        try:
            with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","r") as object_id_list:
                data = json.load(object_id_list)
        except:
            
            data = {
                "wait_objects":[],
                "start_time":time.time(),
                "unique_ids":[]
            }

            with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","w") as object_id_list:
                json.dump(data,object_id_list)

        # data["start_time"] += time_length
        if len(wait_objects) > 0:
            for _object in wait_objects:
                if _object["Id"] not in data["unique_ids"]:
                    data["unique_ids"].append(_object["Id"])

                data["wait_objects"].append(_object)

        with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","w") as object_id_list:
            json.dump(data,object_id_list)

        wait_objects_storage = data["wait_objects"]
        start_time = data["start_time"]
        unique_ids = data["unique_ids"]
        time_diff = curr_time - start_time

        total_human_time_spend = 0

        if time_diff > timelimit:

            last_frame_object_id = []
            for _id in wait_objects:
                if _id["Id"] not in last_frame_object_id:
                    last_frame_object_id.append(_id["Id"])

            print("unique_ids______",unique_ids)
            print("last_frame_object_id____",last_frame_object_id)

            id_time = []
            for uniq_id in unique_ids:
                _time = []
                if uniq_id not in last_frame_object_id:
                    for wait_obj in wait_objects_storage:
                        if wait_obj["Id"] == uniq_id:
                            _time.append(wait_obj["time_spend"])
                    id_time.append([uniq_id, max(_time)])

            print("id_time_______",id_time)

            for human_time in id_time:
                total_human_time_spend += human_time[1]

            print("total_human_time_spend____",total_human_time_spend)


            send_data_storage = True
            data["start_time"] = time.time()
            data["wait_objects"] = []
            data["unique_ids"] = []

            with open("/home/custom_transforms/"+"data_storage"+str(zonename)+".json","w") as object_id_list:
                json.dump(data,object_id_list)

        return [send_data_storage, wait_objects_storage, time_diff, len(unique_ids), total_human_time_spend]
            
    def process_frame(self, frame):
        try:
            messages = list(frame.messages())
            if len(messages) > 0:       #checking if frame message is not empty, if it is empty it will move to next frame
                try:
                    BOTNAME = "heatmap"
                    new_data = self.fetch_data(BOTNAME)
                    print("Successfully fetch the data ..!!")
                except Exception as error:
                    print("wrong in fetch_data", error, flush=True)
            
                
                for botconfig_data in new_data["botconfig_data"]:
                    botConfigId = botconfig_data["botconfig_id"]
                    siteId = botconfig_data["site_id"]
                    site_name = botconfig_data["site_name"]
                    node_name = botconfig_data["node_name"]
                    botName = BOTNAME
                    checklist = "None"

                    if len(messages)>0:
                        # print("messages____",messages)
                        print("messages____",messages[0], dir(messages[0]))
                        try:
                                
                            rects = []
                            output_centroid = dict()
                            messages=list(frame.messages())
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

                            
                        except Exception as error:
                            print("wrong in starting:{}".format(error),flush=True)

                       
                        for i in botconfig_data['sensors']:
                        
                            sensorId = i["camera_id"]
                            sensor_name = i["sensor_name"]
                            start_time = i["start_time"]
                            print("sensor_______",json_msg['source'], i["url"])
                            if i["url"]==json_msg['source']:
                                
                                if start_time == None:
                                    new_time = time.time() * 1000 # for live streaming
                                else:
                                    print("new_time   ",start_time, (time.time()), float(self.last_time()))
                                    new_time = int(start_time + (time.time()-float(self.last_time()))) * 1000 # for simulation
                                    print("new_time ",new_time)

                            
                                for zone_ in i["roi"]:
                                    
                                    roi_box = zone_["roi_box"]
                                    roiName = zone_["roi_name"]
                                    print("roiname__________",roiName)

                                    new_rects = []
                                    foot_points = []
                                    try:
                                        for rect in rects:      # iterating through rects and checking person is in roi or not 
                                            startX, startY, endX, endY = rect
                                            cX = int((startX + endX) / 2.0)
                                            cY = int((startY + endY) / 2.0)
                                            info = self.inroi(cX, cY, roi_box)

                                            foot_point_x = cX
                                            foot_point_y = endY

                                            if info==True:      # if person is in roi then storing rect in new_rects
                                                new_rects.append(rect)
                                                foot_points.append([foot_point_x, foot_point_y])



                                    except Exception as error:
                                        print("wrong in inroi:{}".format(error),flush=True)
                                        

                                    try:

                                        print(f"objects_in_roi____{new_rects}")
                                        print(f"foot points ___{foot_points}")
                                                                    
                                        objects = self.tracker.update(new_rects)        # getting objectId for all person in roi
                                        
                                        wait_objects = []
                                        foot_cnt = 0
                                        for (objectId, centroid) in objects.items(): # getting individual objectId of a person
                                            output_centroid = dict()
                                            cX, cY = centroid
                                            curr_time = time.time()
                                            foot_x = foot_points[foot_cnt][0]
                                            foot_y = foot_points[foot_cnt][1]

                                            object_monitor = self.object_monitor(roiName, objectId, curr_time)
                                            if object_monitor > 10:
                                            
                                                output_centroid['X'] = int(foot_x)
                                                output_centroid['Y'] = int(foot_y)
                                                output_centroid['Id'] = int(objectId)
                                                output_centroid["time_spend"] = object_monitor
                                                output_centroid["unique"] = str(cX) +" + "+str(cY)
                                                wait_objects.append(output_centroid)

                                            foot_cnt += 1
                                    
                                    except Exception as error:
                                        print("wrong in tracker:{}".format(error),flush=True)  

                                    curr_time = time.time()

                                    print(f"roiName____{roiName}_and_it's_objects_are _____{wait_objects}")

                                    send_data_storage_flag, wait_objects_storage, time_diff, people_count, total_human_time_spend = self.data_storage(roiName, wait_objects, curr_time, 30)
                                
                                    print("send_________________________",send_data_storage_flag, time_diff, people_count, total_human_time_spend)
                                    
                                    if send_data_storage_flag == True:
                                        
                                        print("send_________________________",send_data_storage_flag, wait_objects_storage, time_diff, people_count, total_human_time_spend)
                                    
                                        
                                        try:
                                            self._db_metadata.ingest(
                                                {
                                                    "time":new_time,
                                                    "totalCount":len(wait_objects_storage),
                                                    "coordinates":wait_objects_storage,
                                                    "peoplecount":people_count,
                                                    "totalHumantimeSpend":total_human_time_spend,
                                                    "siteId":siteId,
                                                    "roiName":roiName,
                                                    "botName":botName,
                                                    "checklist":checklist,
                                                    "botConfigId":botConfigId,
                                                    "sensorId":sensorId
                                                }
                                            )["_id"]
                                            print("Successfully dump data ..!!")
                                        except Exception as error:
                                            print("wrong in ingesting data  ",error)

                                        
                                    #     try:
                                    #         frame.remove_message(messages[0]) 
                                    #     except:
                                    #         ignore = None

                                    # else:
                                    #     try:
                                    #         frame.remove_message(messages[0]) 
                                    #     except:
                                    #         ignore = None  

                          
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
