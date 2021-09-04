from enum import unique
from os import WEXITED
from re import T

try:
    import gstgva  
    from gstgva.util import libgst, gst_buffer_data
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    from db_query import DBQuery
    from db_common import DBCommon
    import numpy as np
    import json
    import os
    import logging
    import datetime
    from notification import notification
    from configuration import env
    from centroid_tracker import CentroidTracker
    from memory_profiler import profile
    from shapely.geometry import Point, Polygon
    import time
    import PIL.ImageDraw as ImageDraw



except Exception as e:
    print("module problem:{}".format(e),flush=True)

# office=list(map(float,env["OFFICE"].split(",")))
# dbhost=env["DBHOST"]
scenario = env["SCENARIO"]
office = list(map(float, env["OFFICE"].split(",")))
dbhost = env["DBHOST"]
every_nth_frame = int(env["EVERY_NTH_FRAME"])
mqtt_topic=env.get("MQTT_TOPIC","analytics")

class Queue:
    def __init__(self,data, camera_id=0):
        self.camera_id=camera_id
        # self.botconfig_id = botconfig_id
        self.data=data
        self.roi=self.data["roi_box"]
        self.queue_count=0
        self.entry=[]
        self.wait_time=0
        self.exit=[]



class QueueCounting:
    queue={}
    capture = {}
    compliance_capture = {}
    notifications = {}
    print("queue_______",queue, flush=True)
    compliance=True
   
    def __init__(self):
        
        self.total_count={}
        self.exit_count={}
        self.entry_count={}
        self.dbq=DBQuery(index="recordings",office=office,host=dbhost)
        self.dba=DBQuery(index="analytics",office=office,host=dbhost)
        # self.exceed_time={}
        self.tracker=  CentroidTracker(maxDisappeared=150)
        self.initmethod()


           
       
    def new_initmethod(self, BOTNAME):

        _path1=os.getcwd()
        _path2=os.path.join(_path1,"video/")
        #print(path2,flush=True)
        # self.pathi="{}.jpeg".format(path2)
        #print(pathi,flush=True)
        os.makedirs(os.path.dirname(_path2), exist_ok=True)

        site_ids = []
        botconfig_ids = []
        dbb = DBQuery(host = dbhost, index = "botconfigs", office=office)
        for botconfig in dbb.search_without_office("algorithm:'"+str(BOTNAME)+"'"):
            site_id = botconfig["_source"]["siteId"]
            botconfig_id = botconfig["_id"]
            site_ids.append(site_id)
            botconfig_ids.append(botconfig_id)
        print("botconfig_ids",botconfig_ids,flush=True)
        print("site_ids",site_ids,flush=True)


        json_data = []    
        cnt = 0
        for botconfig_id in botconfig_ids:
            

            _dbb = DBCommon(host=dbhost, index="botconfigs", office=office)
            
            sensor_ids = []
            
            botconfig_index = _dbb.get_without_office(botconfig_id)
            sensor_ids.append(botconfig_index["_source"]["sensorId"])
            _rule_id = botconfig_index["_source"]["ruleId"]
            print("sensor_ids",sensor_ids,flush=True)

            rtspurls = []
            _dbp = DBCommon(host=dbhost, index="provisions", office=office)
            provisions_index = _dbp.get(sensor_ids[0])
            rtspurls.append(provisions_index["_source"]["rtspurl"])

            _dbr = DBCommon(host = dbhost, index = "rules", office=office)
            rule_index =  _dbr.get_without_office(_rule_id)
            rule_value = rule_index["_source"]["value"]

            print("sensor_ids",sensor_ids,flush=True)
            print("rtspurls",rtspurls, flush=True)


            # sensor_ids = []
            # rtspurls = []
            # dbp = DBQuery(host=dbhost, index="provisions", office=office)
            # for sensor in dbp.search("algorithm:'queuemanage'"):
            #     sensor_id = sensor["_id"]
            #     sensor_ids.append(sensor_id)
            #     try:
            #         rtspurl = sensor["_source"]["rtspurl"]
            #     except:
            #         rtspurl = "None"
            #     rtspurls.append(rtspurl)
            # print("sensor_ids",sensor_ids)
            # print("rtspurls",rtspurls)

            coordinates = []
            zone_names = []
            dbz = DBQuery(host=dbhost, index="zones", office=office)
            
            for zones in dbz.search_without_office("botName:'"+str(BOTNAME)+"' and sensorId:'"+str(sensor_ids[0])+"'"):
                coordinate = zones["_source"]["coordinate"][0]
                coordinates.append(coordinate)
                zone_name = zones["_source"]["name"]
                zone_names.append(zone_name)
            print("coordinates",coordinates, flush=True)
            print("zone_names",zone_names, flush=True)

        # coordinates = []
        # zone_names = []
        # for sensorid in sensor_ids:
        #     temp_coordinate = []
        #     temp_zones = []
        #     dbz = DBQuery(host=dbhost, index="zones", office=office)
            
        #     for zones in dbz.search_without_office("botName:'queuemanage' and sensorId:'"+str(sensorid)+"'"):
        #         coordinate = zones["_source"]["coordinate"][0]
        #         temp_coordinate.append(coordinate)
        #         zone_name = zones["_source"]["name"]
        #         temp_zones.append(zone_name)
        #     coordinates.append(temp_coordinate)
        #     zone_names.append(temp_zones)
            
        # print("coordinates",coordinates)
        # print("zone_names",zone_names)

        

            dbn = DBQuery(host = dbhost, index = "nodes", office=office)
            
            for nodes in dbn.search("coordinates:'"+str(office)+"'"):
                node_name = nodes["_source"]["name"]
            print("node_name",node_name, flush=True)

            dbn = DBQuery(host=dbhost, index="notificationconfigs", office=office)
            pro_sends = []
            pro_snapshots = []
            norm_sends = []
            norm_snapshots = []
            real_sends = []
            real_snapshots = []
            responsetype_ids = []
            rule_ids = []
            templateIds = []
            notification_ids = []
            resendIntervals = []
            isResends = []
            for notification in dbn.search_without_office("botConfigId:'"+str(botconfig_id)+"'"):
                id = notification["_id"]
                notification_ids.append(id)
                _type = notification["_source"]["type"]
                snapshot = notification["_source"]["attachedSnap"]
                botConfigId = notification["_source"]["botConfigId"]
                responsetype_id = notification["_source"]["responseTypeId"]
                rule_id = notification["_source"]["ruleId"]
                templateId = notification["_source"]["templateId"]
                resendInterval = notification["_source"]["resendInterval"]
                isResponseType = notification["_source"]["isResponseType"]
                isResend = notification["_source"]["isResend"]

                if _type == 1 and isResponseType == False:
                    real_sends.append("true")
                    if snapshot == True:
                        real_snapshots.append("true")
                    if snapshot == False:
                        real_snapshots.append("false")
                    pro_sends.append("false")
                    pro_snapshots.append("false")
                    norm_sends.append("false")
                    norm_snapshots.append("false")

                if _type == 1 and isResponseType == True:
                    norm_sends.append("true")
                    if snapshot == True:
                        norm_snapshots.append("true")
                    if snapshot == False:
                        norm_snapshots.append("false")
                    pro_sends.append("false")
                    pro_snapshots.append("false")
                    real_sends.append("false")
                    real_snapshots.append("false")


                if _type == 3:
                    pro_sends.append("true")
                    if snapshot == True:
                        pro_snapshots.append("true")
                    if snapshot == False:
                        pro_snapshots.append("flase")
                    real_sends.append("false")
                    real_snapshots.append("false")
                    norm_sends.append("false")
                    norm_snapshots.append("false")

                print("isResponseTypeisResponseTypeisResponseType",isResponseType, snapshot, id)


                responsetype_ids.append(responsetype_id)
                rule_ids.append(rule_id)
                templateIds.append(templateId)
                resendIntervals.append(resendInterval)
                isResends.append(isResend)

            print("new_norm_send",norm_sends)
            print("new_norm_snapshots",norm_snapshots)
            print("new_pro_sends",pro_sends)
            print("new_pro_snapshots",pro_snapshots)
            print("new_real_sends",real_sends)
            print("new_real_snapshots",real_snapshots)
            print("isResends",isResends)
            print("notification_idsxxnotification_ids",notification_ids)
            print("isResends_type",type(isResends[0]))
        

            dbr = DBCommon(host=dbhost, index="notification_responsetypes", office=office)
            inspectionScores_p = []
            inspectionScores_n = []
            for notification_responsetype_id in responsetype_ids:
                responsetype = dbr.get_without_office(notification_responsetype_id)
                inspectionScore_p = responsetype["_source"]["trueResponse"]["score"]
                inspectionScore_n = responsetype["_source"]["falseResponse"]["score"]
                inspectionScores_p.append(inspectionScore_p)
                inspectionScores_n.append(inspectionScore_n)

            print("inspectionScores",inspectionScores_p, flush=True)
            print("inspectionScores",inspectionScores_n, flush=True)


            exceeding_lengths = []
            dbru = DBCommon(host=dbhost, index="notification_rules", office=office)
            for notification_rules_id in rule_ids:
                rules = dbru.get_without_office(notification_rules_id)
                exceeding_length = rules["_source"]["value"]
                exceeding_lengths.append(exceeding_length)
            
            print("exceeding_lengths",exceeding_lengths)

            dbt = DBQuery(host=dbhost, index="notification_templates", office=office)
            texts = []
            for notification_template_id in templateIds:
                templates  = dbt.get_without_office(notification_template_id)
                source = templates["_source"]
                message = source["whatsApp"]["message"]
                to = source["whatsApp"]["to"]
                texts.append(message)
            print("texts_____",texts)

            _notifications = []
        

            # for num_notification in range(len(responsetype_ids)):
            #     print("num_notification",notification_ids[num_notification])
            #     real_snd = real_sends[num_notification]
            #     real_snp = real_snapshots[num_notification]
            #     pro_snd = pro_sends[num_notification]
            #     pro_snp = pro_snapshots[num_notification]
            #     exc = exceeding_lengths[num_notification]
            #     resend = isResends[num_notification]
            #     wait_time = resendIntervals[num_notification]

            #     print(exc,"eeexxxxxcccc")
            _sensors = []      
            for sensors_num in range(len(sensor_ids)):
                # _rois = coordinates[sensors_num]
                _url = rtspurls[sensors_num]
                rois = []
                for rois_num in range(len(coordinates)):
                    _notifications = []
                    for num_notification in range(len(responsetype_ids)):

                        print("num_notification",notification_ids[num_notification])
                        real_snd = real_sends[num_notification]
                        real_snp = real_snapshots[num_notification]
                        pro_snd = pro_sends[num_notification]
                        pro_snp = pro_snapshots[num_notification]
                        norm_snd = norm_sends[num_notification]
                        norm_snp = norm_snapshots[num_notification]
                        exc = exceeding_lengths[num_notification]
                        resend = isResends[num_notification]
                        wait_time = resendIntervals[num_notification]

                        print(exc,"eeexxxxxcccc")
                        _notifications.append({
                            "notification_ids":notification_ids[num_notification],
                            "all_notification_ids":notification_ids,
                            "other_data":{
                                "zone_names":zone_names,
                                "botConfigId":botConfigId,
                                "site_id":site_ids,
                                "inspectionScore_p":inspectionScores_p[num_notification],
                                "rtspurls":rtspurls,
                                "inspectionScore_n":inspectionScores_n[num_notification],
                                "exceeding_lengths":int(exc),
                                "isResend":resend,
                                "wait_time":wait_time,
                                # "exceeding_lengths":10,
                                "pro_exceeding_lengths":int(rule_value),
                                # "pro_exceeding_lengths":5,
                                "sensor_ids":sensor_ids,
                                "texts":texts[0],
                                "pro_send":pro_snd,
                                "pro_snapshot":pro_snp,
                                "real_send":real_snd,
                                "real_snapshot":real_snp,
                                "normal_send": norm_snd,
                                "normal_snapshot": norm_snp,
                                "node_name":node_name,
                                "to":to

                            }})
                    # _sensors = []  

                    rois.append({
                        "roi_box":coordinates[rois_num],
                        "roi_name":zone_names[rois_num],
                        "min_people": 1,
                        "score_true": 10,
                        "score_false": 10,
                        "tracking":"centroid",
                        "pro_active_notification":{
                            "send":pro_snd,
                            "snapshot":pro_snp,
                            "exceeding_length":int(exc),
                            "wait_time": 20
                        },
                        "real_time_notification":{
                            "queue_exceeded":{
                                "send":real_snd,
                                "snapshot":real_snp,
                                "exceed_length":int(exc),
                                "exceeded_time": 20,
                                "wait_time": 30
                            },
                            "queue_normal": {
                                "send": "false",
                                "snapshot": "false"
                            }
                        },
                        "notification":_notifications
                    })
                _sensors.append({
                    "url":_url,
                    "camera_id":sensor_ids[sensors_num],
                    "roi":rois
                    
                    
                })


            json_data.append({
            "sensors":_sensors,
            "botconfig_id":botconfig_id,
            "site_id":site_ids[cnt],
            })
            cnt +=1

            # print("json_data: ",json_data, flush=True)



        botconfig_data = {
            "botconfig_data":json_data
        }

        # print("botconfig_data___",botconfig_data, flush=True)

        return botconfig_data


    def initmethod(self):
        try:
            BOTNAME = "queuemanage"
            data = self.new_initmethod(BOTNAME)
            # data = self.new_initmethod()           #add...
        except Exception as error:
            print("Error in new_initmethod:1 ",error, flush=True)
        for botconfig_data in data["botconfig_data"]:
            botconfig_id = botconfig_data["botconfig_id"]
            self.queue[botconfig_id] = {}
            self.total_count[botconfig_id] = {}
            self.exit_count[botconfig_id] = {}
            self.entry_count[botconfig_id] = {}
            # print("botconfig_databotconfig_data",botconfig_data)

            # for notifications in botconfig_data["data"]:
                
            #     notification_id = notifications["notification_ids"]
            #     print("notification_id_________",notification_id)
            #     self.queue[botconfig_id][notification_id] = {}
            #     self.total_count[botconfig_id][notification_id] = {}
            #     self.exit_count[botconfig_id][notification_id] = {}
            #     self.entry_count[botconfig_id][notification_id] = {}
            for ii in botconfig_data["sensors"]:
                self.camera_id=ii["camera_id"]
                
                self.queue[botconfig_id][self.camera_id]=[]
                self.roi=ii["roi"]
                print("______sdf_____",self.roi)
                print("________sdssr______",self.queue[botconfig_id])
                
                print("done1")
                self.total_count[botconfig_id][self.camera_id]={}
                print("done2")
                self.exit_count[botconfig_id][self.camera_id]={}
                print("done3")
                self.entry_count[botconfig_id][self.camera_id]={}
                print("done4")

                # self.exceed_time[self.camera_id]={}
                for j in range(len(ii["roi"])):
                    # zone_name = j["roi_name"]
                    # print("_______j__________",self.camera_id)
                    q=Queue(self.roi[j],self.camera_id)
                    self.queue[botconfig_id][self.camera_id].append(q)
                    self.total_count[botconfig_id][self.camera_id][j]={}
                    self.exit_count[botconfig_id][self.camera_id][j]={}
                    self.entry_count[botconfig_id][self.camera_id][j]={}
                    # print("xxxxx____xxxx",ii)
                    for notification in ii["roi"][j]["notification"]:
                        notification_id = notification["notification_ids"]
                        # self.botconfig_id = notification_id
                        # self.queue[botconfig_id][self.camera_id][zone_name][notification_id].append(q)
                        self.total_count[botconfig_id][self.camera_id][j][notification_id]=0
                        self.exit_count[botconfig_id][self.camera_id][j][notification_id]=0
                        self.entry_count[botconfig_id][self.camera_id][j][notification_id]=0

                    # self.exceed_time[self.camera_id][j]=0
        # print(self.total_count,"self.total_count")
        # print(self.queue,"self.total_count")
              
               
    @classmethod
    def give_queue(cls):
        return cls.queue 



    def send_notification_without_snap(self,to,json_msg,time,date, text_message):
        # zone_names = self.required_data[1]
        # texts = self.required_data[8]
        json_msg1={"eventId": "123",
            "mqttEventName": "NOTIFICATION",
            "templates":{
               
                "whatsApp":{
                        "to": to,
                "message":text_message,
                },
                "type": "WHATSAPP"}}
        print("send_notification_without_snap",json_msg1)
        notification("192.168.1.2",32400,json_msg1)

        print("send_notification_without_snap_1",json_msg1)

    def send_notification_with_snap(self,to, json_msg,time,date, node_name, sensor_id, botname, timestamp, text_message):
        temp_path = "http://122.169.112.242/images/"+str(node_name)+"/"+str(sensor_id)+"/"+str(botname)+"/"+"img_"+str(timestamp)+".jpeg"

        print("temp_pathtemp_pathtemp_pathtemp_pathtemp_path",temp_path)

        #print("enter  send_notication_with_snap",flush=True)
        json_msg1={"eventId": "123",
            "mqttEventName": "NOTIFICATION",
            "templates":{
               
                "whatsApp":{
                        "to": to,
                # "message":{"text_message":json_msg["text_message"],
                #             "roiName": json_msg["zone_name"],
                #             "visionBotName": json_msg['botName'],
                #             "timeStamp": time,
                #             "date": date,
                #             "imagePath":temp_path
                "message": text_message,
                "url": temp_path

                },
                "type": "WHATSAPP"}}
        print("send_notification_with_snap",json_msg1)
        notification("192.168.1.2",32400,json_msg1)
        print("send_notification_without_snap_2",json_msg1)


    def inroi(self,x,y,line):
        k=line
        p1 = Point(x,y)
        coords = [(k[0],k[1]), (k[2],k[3]), (k[4],k[5]), (k[6],k[7])]
        poly = Polygon(coords)
        info=p1.within(poly)
        return info

   
    def process_frame(self,frame):
        print("Enter_here_________________")
        
        def real_time_flag_json(exceeding_length, time, queue_count, required_data, sensor_id_new, wait_time, zone_name, isResend, botconfig_id):
            
            flag = False
            que_normal_flag = "false"
            return_real_time_flag = "false"
      
            if exceeding_length<queue_count:
                first_flag = "true"
            else:
                first_flag = "false"
           
            notification_id = required_data["notification_ids"]

            _data = {
                "sensor_id":sensor_id_new,
                "notification_id":notification_id,
                "type":"real_time",
                "roi_name":zone_name,
                "start_time":time,
                "queue_count":queue_count,
                "flag":first_flag
            }


            data = None
            try:
                with open("/home/custom_transforms/real_time"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","r") as final_json_temp:
                    data = json.load(final_json_temp)
                    # print("Data_________________",data)
            except:
                print("create")
                if data == None:
                    with open("/home/custom_transforms/real_time"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","w") as final_json_temp:
                        json.dump(_data, final_json_temp)
                        flag = True

            
            print("flag_________",flag)
            if flag == False:
                with open("/home/custom_transforms/real_time"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","r") as final_json_temp:
                    data = json.load(final_json_temp)
                    # print("past_data_____",data)

               
                    real_time_flag = data["flag"]

                    if first_flag == "true":
                    
                        if real_time_flag == "true":

                            if (time - data["start_time"])/60 > wait_time and isResend == True:

                                return_real_time_flag = "true"

                            else:
                                return_real_time_flag = "false"
                            print("flag_json____real_time",real_time_flag, time, data["start_time"], (time - data["start_time"])/60)
                       

                    if real_time_flag == "false":

                        if first_flag == "true":

                            data["flag"] = "true"

                            return_real_time_flag = "true"

                    if real_time_flag == "true":

                        if first_flag == "false":

                            data["flag"] = "false"

                            que_normal_flag = "true"
                            return_real_time_flag = "false"

                    print("flag_json____first_flag ",first_flag, return_real_time_flag)  

                    if first_flag == "true" and real_time_flag == "true":
                        if  (time - data["start_time"])/60 > wait_time:
                            print("flag_json____enter_1")
                      
                            with open("/home/custom_transforms/real_time"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","w") as final_json_temp:
                                json.dump(_data, final_json_temp)
                                print("flag_json____dump1")

                    if real_time_flag == "false" and first_flag == "true":
                        print("flag_json____enter_2")
                        with open("/home/custom_transforms/real_time"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","w") as final_json_temp:
                                json.dump(_data, final_json_temp)
                                print("flag_json____dump2")

                    if que_normal_flag == "true":
                        print("flag_json____enter_3")
                        with open("/home/custom_transforms/real_time"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","w") as final_json_temp:
                                json.dump(_data, final_json_temp)
                                print("flag_json____dump3")



            return [que_normal_flag, return_real_time_flag,wait_time, time, data["start_time"], (time - data["start_time"])/60] 

        def pro_active_flag_json(exceeding_length, pro_exceeding_length,time, queue_count, required_data, sensor_id_new, zone_name, botconfig_id):
            
            flag = False
            return_pro_active_flag = "false"

            if exceeding_length<queue_count and queue_count<=pro_exceeding_length:
                print("proactive_flag__")
                first_flag = "true"
            else:
                first_flag = "false"
           
            notification_id = required_data["notification_ids"]
        

            _data = {
                "sensor_id":sensor_id_new,
                "notification_id":notification_id,
                "type":"pro_active",
                "roi_name":zone_name,
                "start_time":time,
                "queue_count":queue_count,
                "flag":first_flag
            }


            data = None
            try:
                with open("/home/custom_transforms/pro_active"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","r") as final_json_temp:
                    data = json.load(final_json_temp)
                    # print("Data_________________",data)
            except:
                print("create")
                if data == None:
                    with open("/home/custom_transforms/pro_active"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","w") as final_json_temp:
                        json.dump(_data, final_json_temp)
                        flag = True

            
            print("flag_________",flag)
            if flag == False:
                with open("/home/custom_transforms/pro_active"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","r") as final_json_temp:
                    data = json.load(final_json_temp)
                    # print("past_data_____",data)

               
                    pro_active_flag = data["flag"]


                    if pro_active_flag == "false":

                        if first_flag == "true":

                            data["flag"] = "true"

                            return_pro_active_flag = "true"


                    print("flag_json____pro_active ",first_flag, return_pro_active_flag, queue_count)  

                    if pro_active_flag == "false" and first_flag == "true":
                        print("flag_json____enter_4")
                        with open("/home/custom_transforms/pro_active"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","w") as final_json_temp:
                                json.dump(_data, final_json_temp)
                                print("flag_json____dump4")

                    if pro_active_flag == "true" and first_flag == "false":
                        print("flag_json____enter_5")
                        with open("/home/custom_transforms/pro_active"+str(botconfig_id)+str(notification_id)+str(sensor_id_new)+str(zone_name)+".json","w") as final_json_temp:
                                json.dump(_data, final_json_temp)
                                print("flag_json____dump5")

            print("flag_json____pro_active 2",first_flag, return_pro_active_flag, queue_count)  

            return return_pro_active_flag 
                            
            
       


        def final_json_data(botconfig_id,notification_id, sensor_id, zone_name):
            final_json_data = []

            zone_data = []
            zone_data.append({
                                "roi_name":zone_name,
                                "count":None})
            final_json_data.append({
                        "sensor_id":sensor_id,
                        "zone":zone_data
                })

            past_data = {
                "past_data":final_json_data
            }
            # print("past_data",past_data)
            cwd = os.getcwd()
            print("cwd",cwd)

            data = None
            try:
                with open("/home/custom_transforms/"+str(botconfig_id)+str(sensor_id)+str(zone_name)+str(notification_id)+".json","r") as final_json:
                    data = json.load(final_json)
                    print("Data____",data)
            except:
                print("create")
                if data == None:
                    with open("/home/custom_transforms/"+str(botconfig_id)+str(sensor_id)+str(zone_name)+str(notification_id)+".json","w") as final_json:
                        json.dump(past_data, final_json)

            # with open("/home/custom_transforms/final.json","w") as final_json:
            #     json.dump(past_data, final_json)
            _sensors= []
            _zones = []

            init_count = []
            if data != None:
                
                with open("/home/custom_transforms/"+str(botconfig_id)+str(sensor_id)+str(zone_name)+str(notification_id)+".json","r") as final_json:
                    data = json.load(final_json)
                    # print("past_data_____",past_data)
                    try:

                        for snr in data["past_data"]:
                            _sensors.append(snr["sensor_id"])
                            temp_zones = []
                            temp_count = []
                            for _zone in snr["zone"]:
                                temp_zones.append(_zone["roi_name"])
                                temp_count.append(_zone["count"])
                            _zones.append(temp_zones)
                            init_count.append(temp_count)
                    except Exception as err:
                        print("here_errrr",err)

            print("creates_____ori_zone", zone_name, _zones)
            print("creates_____ori_rtsp", sensor_id, _sensors)

            if [[zone_name]] != _zones or [[sensor_id]] != _sensors:
                print("creates_____")
                with open("/home/custom_transforms/"+str(botconfig_id)+str(sensor_id)+str(zone_name)+str(notification_id)+".json","r") as final_json:
                    data = json.load(final_json)
                    # print("Data____hr",data)

            new_count = []
            for snr in past_data["past_data"]:
                cam_id = snr["sensor_id"]
                cnt= 0
                temp_new_count = []
                for _zone in snr["zone"]:
                    _zone["count"] = self.total_count[botconfig_id][cam_id][cnt][notification_id]
                    temp_new_count.append(_zone["count"])
                new_count.append(temp_new_count)
            # print("new_count",new_count,init_count)
      

            print("createscnt_____ori_zone", new_count, init_count)
            
            if new_count != init_count:
                new_flag = True
                print("new_past_data_1",past_data)
                with open("/home/custom_transforms/"+str(botconfig_id)+str(sensor_id)+str(zone_name)+str(notification_id)+".json","w") as final_json:
                    json.dump(past_data, final_json)
            else:
                # print("new_past_data_2",past_data)
                new_flag = False

            print("Flaggggggg",new_flag)

            return new_flag

        # new_initmethod

        try:
            BOTNAME = "queuemanage"
            new_data = self.new_initmethod(BOTNAME)

            print("new_initmethodnew_initmethod",new_data)
            
        except Exception as error:
            print("Error in new_initmethod:3",error, flush=True)
        for botconfig_data in new_data["botconfig_data"]:
            botconfig_id = botconfig_data["botconfig_id"]
            site_id = botconfig_data["site_id"]
            
            self.capture[botconfig_id] = {}
            self.compliance_capture[botconfig_id] = {}

            try:
                messages=list(frame.messages())
                print("messages",len(messages), flush=True)
                if len(messages)>0:
                    try:
                        detected_centers=[]
                        rects=[]
                        detections = [x for x in frame.regions()]
                        # messages=list(frame.messages())
                        # print("messagesmessages",messages)
                        e = datetime.datetime.now()
                        date='{}/{}/{}'.format(e.day ,e.month, e.year)
                        time='{}:{}:{}'.format(e.hour, e.minute, e.second)
                        # time='{}:{}:{}'.format(e.hour, e.minute, e.second)
                        # if len(messages)>0:
                        json_msg = json.loads(messages[0])  
                        for l in json_msg:
                            if l=='objects':
                                #print(json_msg,flush=True)
                                dic=json_msg[l]
                                for j in range(len(dic)):
                                    if dic[j]['detection']['label']=='person':
                                        x_max=dic[j]['x']+dic[j]['w']
                                        y_max=dic[j]['y']+dic[j]['h']
                                        x=dic[j]['x']
                                        y=dic[j]['y']
                                        rects.append([x,y,x_max,y_max])
                            
                                break
                        else:
                            json_msg={}
                        detected_centers,_=self.tracker.update(rects)
                    except Exception as error:
                        print("wrong in starting:{}".format(error),flush=True)
                   
                    print("getting messages for queue-----", flush=True)
                
                    data = botconfig_data
                    json_msg = json.loads(messages[0])
                    self.roi_box=[]
                    for i in data['sensors']:
                        # print("______iiii________",i)
                        #========================CCTV=========================
                        if i["url"]==json_msg['source']:
                            # self.botconfig_id = botconfig_id
                            self.camera_id=i['camera_id']
                            for j in i["roi"]:
                                print("storing roi box",flush=True)
                                self.roi_box.append(j["roi_box"])

                    for i in data['sensors']:
                        print("self.camera_iself.camera_i",self.camera_id)

                        if i["url"]==json_msg['source']:
                            print("self.camera_iself.camera_i__1",self.camera_id)
                            # sensor_id = i["camera_id"]
                            self.capture[botconfig_id][self.camera_id] = {}
                            self.compliance_capture[botconfig_id][self.camera_id] = {}
                                                            
                            snsr = json_msg["tags"]["sensor"]

                            print("iiiiiiiiiiiixxxxx",i)

                            
                            zone_cnt = 0
                            for zone_ in i["roi"]:
                                

                                zone_name = zone_["roi_name"]
                                print("zone_namezone_namezone_name",zone_)
                                self.capture[botconfig_id][self.camera_id][zone_name] = {}
                                self.compliance_capture[botconfig_id][self.camera_id][zone_cnt] = {}
                                
                                print("zone_notificationxx",zone_["notification"])


                                for notifications_  in zone_["notification"]:
                                    try:
                                        notification_id = notifications_["notification_ids"]
                                        # print("notification__",notification_id)
                                        
                                        sensor_other_data = notifications_["other_data"]

                                        zone_names = sensor_other_data["zone_names"]
                                        # print("notification__zone_names",zone_names)
                                        botConfigId = sensor_other_data["botConfigId"]
                                        print("botConfigId",botConfigId)
                                        # site_id = sensor_other_data["site_id"]
                                        # print("_site_id",site_id)
                                        inspectionScore_p = sensor_other_data["inspectionScore_p"]
                                        print("exc",inspectionScore_p)
                                        rtspurls = sensor_other_data["rtspurls"]
                                        print("_sensors",rtspurls)
                                        inspectionScore_n = sensor_other_data["inspectionScore_n"]
                                        print("inspectionScore",inspectionScore_n)
                                        exe = sensor_other_data["exceeding_lengths"]
                                        pro_exe = sensor_other_data["pro_exceeding_lengths"]
                                        wait_time = sensor_other_data["wait_time"]
                                        sensor_ids = sensor_other_data["sensor_ids"]
                                        text_message = sensor_other_data["texts"]
                                        isResend = sensor_other_data["isResend"]
                                        pro_send = sensor_other_data["pro_send"]
                                        pro_snapshot = sensor_other_data["pro_snapshot"]
                                        real_send = sensor_other_data["real_send"]
                                        real_snapshot = sensor_other_data["real_snapshot"]
                                        normal_send = sensor_other_data["normal_send"]
                                        normal_snapshot = sensor_other_data["normal_snapshot"]
                                        node_name = sensor_other_data["node_name"]
                                        to = sensor_other_data["to"]
                                        print("text_message: ",to)
                                        # print("notification______exe",exe)

                                        try:
                                            print("notification__",botconfig_id,notification_id, self.camera_id, zone_name)
                                            new = final_json_data(botconfig_id,notification_id, self.camera_id, zone_name)
                                            # new = True
                                        except Exception as error:
                                            print("Error in final_json_data: ",error)
                                    
                                        self.capture[botconfig_id][self.camera_id][zone_name][notification_id] = {}
                                        self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id] = {}
                                   
                                        import time
                                        _time = time.time()
                                        e = datetime.datetime.now()
                                        date='{}/{}/{}'.format(e.day ,e.month, e.year)
                                        time_='{}:{}:{}'.format(e.hour, e.minute, e.second)
                                    
                                        # print("notification__mewwww__flag___",type(new), new)
                                        self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["timestamp"] = _time
                                        self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["node_name"] = node_name
                                        self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["sensor_id"] = self.camera_id
                                        self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["botname"] = BOTNAME
                                        
                                        if new == True:
                                            # print("notification__mewwww",new)
                                            json_msg["notification_id"] = notification_id
                                            json_msg["camera"]=0
                                            json_msg["roi"]=self.roi_box
                                            json_msg["time1"] = _time
                                            json_msg["zone_name"] = zone_name

                                            json_msg["roiName"] = zone_name  
                                            json_msg["queueLength"]=self.total_count[botconfig_id][self.camera_id][zone_cnt][notification_id]
                                            json_msg["sensorId"]=self.camera_id 
                                            json_msg["botConfigId"] = botConfigId 
                                            json_msg["siteId"] = site_id  
                                            print("mewwww__1",new)
                                            if self.total_count[botconfig_id][self.camera_id][zone_cnt][notification_id] > int(exe):
                                                json_msg["compliance"] = False 
                                                json_msg["inspectionScore"] =inspectionScore_n 
                                                imgpath = "http://122.169.112.242/images/"+str(node_name)+"/"+str(self.camera_id)+"/"+str(BOTNAME)+"/"+"img_"+str(_time)+".jpeg"
                                                json_msg["imagePath"] = imgpath
                                                self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["imagePath"] = str(node_name)+"/"+str(self.camera_id)+"/"+str(BOTNAME)+"/"+"img_"+str(_time)
                                                self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["image"] = True                                                                                
                                            else:
                                                self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["imagePath"] = None
                                                json_msg["compliance"] = True 
                                                json_msg["inspectionScore"] =inspectionScore_p
                                                self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["image"] = False

                                            # json_msg["video_path"] = "None"
                                            # try:
                                            #     time_stamps = []
                                            #     for a  in self.dba.search("sensor='"+snsr+"'"):
                                            #         r = list(self.dbq.search("sensor='"+snsr+"'and time>"+str(a["_source"]["time1"])))
                                                
                                            #         for _r in r:
                                            #             time_stamps.append(_r["_source"]["time"])
                                            #         min_timestamp = max(time_stamps)

                                            #         reco_index = time_stamps.index(min_timestamp)

                                            #         path_r = r[reco_index]["_source"]["path"]

                                            #         path_r = "/home/desktop6/Desktop/dhaval/Dhaval/video-pv/"+path_r
                                                                                    
                                            # except Exception as err:
                                            #     print("Error in db quary",err)

                                            # if len(time_stamps) > 0:
                                            #     print("path_r",path_r,flush=True)
                                            #     json_msg["video_path"] = str(path_r) 
                                            
                                            json_msg["checklist"]="WRK-COM"
                                            json_msg['botName']=BOTNAME 
                                            # print("notification__mewwww__2",new)
                                            try:

                                                frame.remove_message(messages[0])
                                            except Exception as error:
                                                print("notification_remove_frame error",error)

                                            frame.add_message(json.dumps(json_msg))

                                        else:
                                            self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["imagePath"] = None
                                            self.compliance_capture[botconfig_id][self.camera_id][zone_cnt][notification_id]["image"] = False                              
                                        #     print("else____")
                                        #     json_msg["roiName"] = "None"  
                                        #     json_msg["queue_length"]="None"  
                                        #     print("queueLength_2_check____1",self.total_count[botconfig_id][notification_id],time.time(),flush=True)
                                        #     json_msg["sensorId"]="None" 
                                        #     json_msg["botConfigId"] = "None" 
                                        #     json_msg["siteId"] = "None"  
                                        #     json_msg["complaince"] = "None" 
                                        #     json_msg["inspectionScore"] = "None" 
                                        #     json_msg["video_path"] = "None"
                                        #     json_msg["checklist"]="None" 
                                        #     json_msg['botName']="None" 
                                            try:

                                                frame.remove_message(messages[0])
                                            except Exception as error:
                                                print("notification_remove_frame error",error)
                                        #     frame.add_message(json.dumps(json_msg))

                                        # print("notification____entered__")
                                        
                                        
                                        try:
                                                
                                            # print("notification__total_counttotal_counttotal_counttotal_counttotal_counttotal_count",self.total_count)
                                            queue_count = self.total_count[botconfig_id][self.camera_id][zone_cnt][notification_id]

                                            # print("notification__queue_countqueue_countqueue_count",queue_count)

                                            ############################################################ Notification ########################################################################

                                            que_normal_flag, _real_time_flag_json, wait_time_, time__, start_time, diff = real_time_flag_json(exe, _time, self.total_count[botconfig_id][self.camera_id][zone_cnt][notification_id], notifications_, self.camera_id, wait_time,zone_name, isResend, botconfig_id)
                                            
                                            _pro_activation_flag = pro_active_flag_json(exe,pro_exe, _time, self.total_count[botconfig_id][self.camera_id][zone_cnt][notification_id], notifications_, self.camera_id, zone_name, botconfig_id)

                                            self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["timestamp"] = _time
                                            self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["node_name"] = node_name
                                            self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["sensor_id"] = self.camera_id
                                            self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["botname"] = BOTNAME

                                            text_message = text_message.replace("<COUNTER NAME>", str(zone_name))
                                            text_message = text_message.replace("<EVENT DATE & TIME>", str(date))
                                            text_message = text_message.replace("<QUEUE LENGTH>", str(queue_count))
                                            text_message = text_message.replace("<QUEUE THRESHOLD>",str(exe))
                                            # a = "Queue length for <COUNTER NAME> queue is <TYPE OF NOTIFICATION> at <EVENT DATE & TIME>. Allowed Queue Length : <QUEUE THRESHOLD>, Current Queue Length : <QUEUE LENGTH>"



                                            ## Real Time Notification ##
                                            print("notification__count ",queue_count, "notification__id__",notification_id, wait_time_, time__, start_time, diff, zone_name, botconfig_id, "real_case_flag ", real_send, real_snapshot,"pro_case_flag ",pro_send, pro_snapshot, "normal_case_flag", normal_send, normal_snapshot)
                                            if real_send == "true":
                                                real_text_message = text_message.replace("<TYPE OF NOTIFICATION>", "exceeded the allowed queue length")
                                                if real_snapshot == "true":
                                                    if _real_time_flag_json == "true":
                                                        self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["realtime"] = True
                                                        print("notification__send_with_snap_____real_case", queue_count, real_text_message)
                                                        self.send_notification_with_snap(to, json_msg,time_,date, node_name, self.camera_id, BOTNAME, _time, real_text_message)
                                                        # self.write_image(self,buffer, timestamp, node_name, sensor_id, botname)
                                                    else:
                                                        self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["realtime"] = False
                                                elif _real_time_flag_json == "true":
                                                    print("notification__send_without_snap___real_case", queue_count, real_text_message)
                                                    self.send_notification_without_snap(to,json_msg,time_,date, real_text_message)
                                                    self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["realtime"] = False
                                                else:
                                                    self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["realtime"] = False
                                            else:
                                                self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["realtime"] = False
                                            

                                            #############################


                                            ## Real Time Notification For Normal Queue ##

                                            if normal_send == "true":
                                                norm_text_message = text_message.replace("<TYPE OF NOTIFICATION>", "back to normal")
                                                if normal_snapshot == "true":
                                                    if que_normal_flag == "true":
                                                        self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["normal"] = True
                                                        print("notification__send_with_snap_____normal_case", queue_count, norm_text_message)
                                                        self.send_notification_with_snap(to, json_msg,time_,date, node_name, self.camera_id, BOTNAME, _time, norm_text_message)
                                                    else:
                                                        self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["normal"] = False
                                                elif que_normal_flag == "true":
                                                    self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["normal"] = False
                                                    print("notification__send_without_snap___normal_case", queue_count, norm_text_message)
                                                    self.send_notification_without_snap(to,json_msg,time_,date, norm_text_message)
                                                else:
                                                    self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["normal"] = False
                                            else:
                                                self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["normal"] = False
                                            
                                            ##############################################


                                            ## Pro Active Notification ##
                                            print("flag_json____pro_active 3",_pro_activation_flag, queue_count)
                                            if pro_send == "true":
                                                pro_text_message = text_message.replace("<TYPE OF NOTIFICATION>", "about to exceed the allowed queue length")
                                                if pro_snapshot == "true":
                                                    if _pro_activation_flag == "true":
                                                        self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["proactive"] = True
                                                        print("notification__send_with_snap_____pro_case", queue_count, pro_text_message)
                                                        self.send_notification_with_snap(to, json_msg,time_,date, node_name, self.camera_id, BOTNAME, _time, pro_text_message)
                                                    else:
                                                        self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["proactive"] = False
                                                elif _pro_activation_flag == "true":
                                                    print("notification__send_without_snap___pro_case", queue_count, pro_text_message)
                                                    self.send_notification_without_snap(to,json_msg,time_,date, pro_text_message)
                                                    self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["proactive"] = False
                                                else:
                                                    self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["proactive"] = False
                                            else:
                                                self.capture[botconfig_id][self.camera_id][zone_name][notification_id]["proactive"] = False
                                        except Exception as error:
                                            print("wrong in notification", error)
                                            
                                        # ################################

                                        print("self.total_countself.total_count_-1",self.roi_box)
                                        for k in range(len(self.roi_box)):

                                            # print("xxxxxxxxxxxxx.queue_count", self.total_count[notification_id][self.camera_id][i].queue_count)

                                            # print("self.total_countself.total_count_0",k)

                                            # print("self.total_countself.total_count",self.total_count)
                                            # print("self.total_countself.total_count_1",self.total_count[notification_id])
                                            # print("self.total_countself.total_count_2",self.total_count[notification_id][self.camera_id])
                                            # print("self.total_countself.total_count_3",self.total_count[notification_id][self.camera_id][k])
                                        
                                            self.queue[botconfig_id][self.camera_id][k].queue_count=0
                                            print("xxxxxxxxx.queue_count__1")


                                        # try:
                                        #     detected_centers=[]
                                        #     rects=[]
                                        #     detections = [x for x in frame.regions()]
                                        #     messages=list(frame.messages())
                                        #     print("messagesmessages",messages)
                                        #     e = datetime.datetime.now()
                                        #     date='{}/{}/{}'.format(e.day ,e.month, e.year)
                                        #     time='{}:{}:{}'.format(e.hour, e.minute, e.second)
                                        #     # time='{}:{}:{}'.format(e.hour, e.minute, e.second)
                                        #     if len(messages)>0:
                                        #         json_msg = json.loads(messages[0])  
                                        #         for l in json_msg:
                                        #             if l=='objects':
                                        #                 #print(json_msg,flush=True)
                                        #                 dic=json_msg[l]
                                        #                 for j in range(len(dic)):
                                        #                     if dic[j]['detection']['label']=='person':
                                        #                         x_max=dic[j]['x']+dic[j]['w']
                                        #                         y_max=dic[j]['y']+dic[j]['h']
                                        #                         x=dic[j]['x']
                                        #                         y=dic[j]['y']
                                        #                         rects.append([x,y,x_max,y_max])
                                                    
                                        #                 break
                                        #     else:
                                        #         json_msg={}
                                        #     detected_centers,_=self.tracker.update(rects)
                                        # except Exception as error:
                                        #     print("wrong in starting:{}".format(error),flush=True)

                                        for m in list(detected_centers.keys()):
                                            try:
                                                x=detected_centers[m][0]
                                                y=detected_centers[m][1]
                                            except Exception as error:
                                                print("wrong in tracker:{}".format(error),flush=True)
                                            
                                            for j in range(len(self.queue[botconfig_id][self.camera_id])):
                                                try:
                                                    info=self.inroi(x,y,self.queue[botconfig_id][self.camera_id][j].roi)
                                                except Exception as error:
                                                    print("wrong in tracker:{}".format(error),flush=True)
                                                print("infoinfoinfoinfo",info)
                                                try:
                                                    if info==True:
                                                        if j not in self.queue[botconfig_id][self.camera_id][j].entry:
                                                            self.queue[botconfig_id][self.camera_id][j].entry.append(j)
                                                            self.tracker.start_time[j]=time      
                                                        
                                                        self.queue[botconfig_id][self.camera_id][j].queue_count=self.queue[botconfig_id][self.camera_id][j].queue_count+1
                                                        self.tracker.end_time[j]=time  
                                                    
                                                        
                                                    else:
                                                        if j in self.queue[botconfig_id][self.camera_id][j].entry and j not in self.queue[botconfig_id][self.camera_id][j].exit:
                                                            self.tracker.end_time[j]=time 
                                                            # spend_time=datetime.datetime.strptime(self.tracker.end_time[j],'%H:%M:%S') - datetime.datetime.strptime(self.tracker.start_time[j],'%H:%M:%S')   
                                                    
                                                except Exception as error:
                                                    print("wrong in new entry:{}".format(error),flush=True)
                                        
                                        try:
                                            for j in range(len(self.queue[botconfig_id][self.camera_id])):
                                                
                                                self.total_count[botconfig_id][self.camera_id][j][notification_id]=self.queue[botconfig_id][self.camera_id][j].queue_count
                                        

                                                self.entry_count[botconfig_id][self.camera_id][j][notification_id]=len(self.queue[botconfig_id][self.camera_id][j].entry)
                                                self.exit_count[botconfig_id][self.camera_id][j][notification_id]=self.entry_count[botconfig_id][self.camera_id][j][notification_id]-self.total_count[botconfig_id][self.camera_id][j][notification_id]
                                                
                                        except Exception as error:
                                            print("wrong in error in:{}".format(error),flush=True) 

                                        # for notifications_  in zone_["notification"]:
                                        #     temp_notification_id = notifications_["notification_ids"]
                            
                                        #     try:
                                        #         for j in range(len(self.queue[botconfig_id][self.camera_id])):
                                                    
                                        #             self.total_count[botconfig_id][self.camera_id][j][temp_notification_id]=self.queue[botconfig_id][self.camera_id][j].queue_count
                                            

                                        #             self.entry_count[temp_notification_id][self.camera_id][j][temp_notification_id]=len(self.queue[botconfig_id][self.camera_id][j].entry)
                                        #             self.exit_count[temp_notification_id][self.camera_id][j][temp_notification_id]=self.entry_count[temp_notification_id][self.camera_id][j][temp_notification_id]-self.total_count[botconfig_id][self.camera_id][j][temp_notification_id]
                                                    
                                        #     except Exception as error:
                                        #         print("wrong in error in:{}".format(error),flush=True) 

                                        self.queue_count=self.total_count[botconfig_id][self.camera_id]
                                        print("queue_countqueue_countqueue_countqueue_countqueue_count",self.queue_count)
                                        keys_list=list(self.queue_count.values())
                                        value1=keys_list[0]

                                        # json_msg["queue_count"]=self.total_count[botconfig_id][self.camera_id]
                                        # #json_msg["queue_count1"]=self.total_count
                                        # #json_msg["queue_length"]=value
                                        # json_msg["camera"]=self.camera_id
                                        # json_msg["exit_count"]=self.exit_count[botconfig_id][self.camera_id]
                                        # json_msg["entry_count"]=self.entry_count[botconfig_id][self.camera_id] 
                                        if len(messages)>0:           
                                            # frame.remove_message(messages[0])
                                            try:
                                                for key, value in self.tracker.index.items(): 
                                                    for j in range(len(dic)):
                                                        if j==value:
                                                            dic[j]['detection']['id']=key
                                                # json_msg["objects"]=dic
                                            except Exception as error:
                                                print("wrong in error  in mapping id:{}".format(error),flush=True)

                                        # frame.add_message(json.dumps(json_msg))

                            
                                    
                                    except Exception as error:
                                        print("notification__wrong in roi",error)
                                zone_cnt += 1 

                                    


                                  
                                    ######################################################################################################################################################
                                   

                    # for i in range(len(self.roi_box)):
                    #     self.queue[botconfig_id][self.camera_id][i].queue_count=0
                    
                    # self.get_queue_count(frame)
                    

            except Exception as error:
                print("wrong in processing_frame:{}".format(error),flush=True)
        return True

    # def inroi(self,x,y,line):
    #     k=line
    #     p1 = Point(x,y)
    #     coords = [(k[0],k[1]), (k[2],k[3]), (k[4],k[5]), (k[6],k[7])]
    #     poly = Polygon(coords)
    #     info=p1.within(poly)
    #     return info

    @classmethod
    def give_capture(cls):
        return cls.capture

    @classmethod
    def give_compliance_capture(cls):
        return cls.compliance_capture 
    


   

class Capture(object):
    def __init__(self):
        self.timestamp=0
        # self.pathv=" "
        self.pathi=" "
    
    def write_image(self,buffer, timestamp, node_name, sensor_id, botname):
        #print("enter write image",flush=True)
        with gst_buffer_data(buffer, Gst.MapFlags.READ) as data:
            path1=os.getcwd()
            #print(path1,flush=True)
            # self.timestamp=json_msg['timestamp']
            path2=os.path.join(path1,"screenshot/"+str(node_name)+"/"+str(sensor_id)+"/"+str(botname),"img_"+str(timestamp))
            #path2=os.path.join(path1,"screenshot/","img_"+str(timestamp))
            #print(path2,flush=True)
            self.pathi="{}.jpeg".format(path2)
            #print(pathi,flush=True)
            os.makedirs(os.path.dirname(self.pathi), exist_ok=True)
            with open(self.pathi,"wb",0) as output:
                #print("write",flush=True)
                output.write(data)

    def capture_write_image(self,buffer, path):
        #print("enter write image",flush=True)
        with gst_buffer_data(buffer, Gst.MapFlags.READ) as data:
            path1=os.getcwd()
            #print(path1,flush=True)
            # self.timestamp=json_msg['timestamp']
            path2=os.path.join(path1,"screenshot/"+path)
            
            #path2=os.path.join(path1,"screenshot/","img_"+str(timestamp))
            #print(path2,flush=True)
            self.pathi="{}.jpeg".format(path2)
            print("capture_path__",self.pathi)
            #print(pathi,flush=True)
            os.makedirs(os.path.dirname(self.pathi), exist_ok=True)
            with open(self.pathi,"wb",0) as output:
                #print("write",flush=True)
                output.write(data)


    

    # def send_notification_without_snap(self,json_msg,time,date):
    #     # zone_names = self.required_data[1]
    #     # texts = self.required_data[8]
    #     json_msg1={"mqttEventName": "NOTIFICATION",
    #     "textMessage": json_msg["text_message"],
    #     "roiName": json_msg["zone_name"],
    #     "visionBotName": json_msg['botName'],
    #     "timeStamp": time,
    #     "date": date,
    #     "imagePath":"/home/Desktop/dhaval/Dhaval/"+self.pathi[6:],
    #     "videoPath":json_msg["video_path"],
    #     "analytics": "none"
    #     }
    #     print("send_notification_without_snap",json_msg1)
    #     notification("192.168.1.36",32571,json_msg1)
    #     print("send_notification_without_snap_1",json_msg1)


    
    
    #  def send_notification_with_snap(self,json_msg,time,date):
    #     #print("enter  send_notication_with_snap",flush=True)
    #     json_msg1={"mqttEventName": "NOTIFICATION",
    #     "textMessage": json_msg["text_message"],
    #     "roiName": json_msg["zone_name"],
    #     "visionBotName": json_msg['botName'],
    #     "timeStamp": time,
    #     "date": date,
    #     "imagePath":"/home/Desktop/dhaval/Dhaval/"+self.pathi[6:],
    #     "videoPath":json_msg["video_path"],
    #     "analytics": "none"
    #     }
    #     print("send_notification_with_snap",json_msg1)
    #     notification("192.168.1.36",32571,json_msg1)
    #     print("send_notification_without_snap_2",json_msg1)



    def process_frame(self,frame):
        messages=list(frame.messages())
        e = datetime.datetime.now()
        date='{}/{}/{}'.format(e.day ,e.month, e.year)
        time='{}:{}:{}'.format(e.hour, e.minute, e.second)
        queues=QueueCounting.give_queue()
        print("Enter__here__inCapture")
        compliance_capture = QueueCounting.give_compliance_capture()
        screenshot = QueueCounting.give_capture()
        print("screenshot____",screenshot)
        buffer = frame._VideoFrame__buffer
        print("bufferbufferbufferbuffer",buffer)
        print("mmessage___0")
        # if len(messages)>0:
        print("mmessage___1")
        for botconfig in list(screenshot.keys()):
            print("botconfigbotconfig",botconfig)
            botconfig = screenshot[botconfig]
            print("botconfigbotconfig",botconfig)
            for sensor in list(botconfig.keys()):
                print("sensorsensor",sensor)
                try:
                    sensor = botconfig[sensor]
                    for zone in list(sensor.keys()):
                        zone = sensor[zone]
                        print("zonezone",zone)
                        for name in list(zone.keys()):
                            _type = zone[name]
                            print("_type____",_type)
                            try:
                                time_ = _type["timestamp"]
                                node_name = _type["node_name"]
                                sensor_id = _type["sensor_id"]
                                botname = _type["botname"]
                            except:
                                Ignore = None

                            try:
                                if _type["normal"] == True:
                                    self.write_image(buffer, time_, node_name, sensor_id, botname)
                            except:
                                Ignore = None

                            try:
                                if _type["realtime"] == True:
                                    self.write_image(buffer, time_, node_name, sensor_id, botname)
                            except Exception as error:
                                print("notification__error_0",error)

                            try:
                                if _type["proactive"] == True:
                                    self.write_image(buffer, time_, node_name, sensor_id, botname)
                            except:
                                Ignore = None
                except Exception as error:
                    print("notification__error",error)

        try:

            for botconfig in list(compliance_capture.keys()):
                print("sensorsensor",botconfig)
                try:
                    botconfig = compliance_capture[botconfig]
                    for sensor in list(botconfig.keys()):
                        sensor = botconfig[sensor]
                        for zone in list(sensor.keys()):
                            zone = sensor[zone]
                            for images in list(zone.keys()):
                                image_data = zone[images]

                                try:
                                    print("image_dataimage_dataimage_data",image_data)
                                    time_1 = image_data["timestamp"]
                                    node_name = image_data["node_name"]
                                    sensor_id = image_data["sensor_id"]
                                    botname = image_data["botname"]
                                    
                                except:
                                    print("wrong in write_image_error0", err)
                                try:
                                    if image_data["image"] == True:
                                        image_path = image_data["imagePath"]
                                        self.capture_write_image(buffer, image_path)
                                        temp_path = "http://122.169.112.242/images/"+str(node_name)+"/"+str(sensor_id)+"/"+str(botname)+"/"+"img_"+str(time_1)+".jpeg"
                                        print("imageimageimageimageimageimage",temp_path)

                                    print("imageimageimageimageimageimage",image_data["image"])
                                except:
                                    print("wrong in write_image_error1", err)
                                
                except Exception as err:
                    print("wrong in write_image_error2", err)
        except:
            print("wrong in write_image_error3")




        # if len(messages)>0:
        #     json_msg = json.loads(messages[0])
        #     print("screen",flush=True)
  
            
        return True
