try:
    import gstgva  
    from gstgva.util import libgst, gst_buffer_data
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    from db_query import DBQuery
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
    # import datetime as dt
    # from datetime import datetime
    # from datetime import date

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
    def __init__(self,data,camera_id=0):
        self.camera_id=camera_id
        self.data=data
        self.min_people=self.data["min_people"]
        self.score_true=self.data["score_true"]
        self.score_false=self.data["score_false"]
        self.tracking=self.data["tracking"]
        self.roi=self.data["roi_box"]
        #self.roiname=self.data["roiname"]
        #self.siteId=self.data["siteId"]
        #self.checklist=self.data["checklist"]
        self.queue_count=0
        self.allowed_length=2
        self.entry=[]
        self.wait_time=0
        self.exit=[]
        self.pro_active_notification_snapshot="false"
        self.real_time_notification_queue_exceeded_snapshot="false"
        self.real_time_notification_queue_normal_snapshot="false"
        self.real_time_notification_queue_exceeded_time="false"
        self.compliance=True
        self.Inspection_score=0
        self.exceed_flag=True
        self.pro_flag=True  
        self.normal_flag=True
        self.initmethod()

    def initmethod(self):
        try:
            if self.data["pro_active_notification"]["send"]=="true":
                self.pro_active=self.pro_active_true
                if self.data["pro_active_notification"]['snapshot']=="true":
                    self.pro_active_notification_snapshot="true"

                else:
                    self.pro_active_notification_snapshot="false"
            else:
                self.pro_active=self.pro_active_false
            #######################################################################

            if  self.data["real_time_notification"]["queue_exceeded"]["send"]=="true":
                self.real_time_exceed=self.real_time_exceed_true

                if  self.data["real_time_notification"]["queue_exceeded"]["snapshot"]=="true":
                    self.real_time_notification_queue_exceeded_snapshot="true"
                else:
                    self.real_time_notification_queue_exceeded_snapshot="false"
            else:
                self.real_time_exceed=self.real_time_exceed_false
        

    ####################################################################################################

            if  self.data["real_time_notification"]["queue_normal"]["send"]=="true":
                self.real_time_normal=self.real_time_normal_true
                if  self.data["real_time_notification"]["queue_normal"]["snapshot"]=="true":
                    
                    self.real_time_notification_queue_normal_snapshot="true"
                else:
                    self.real_time_notification_queue_normal_snapshot="false"
            else:
                self.real_time_normal=self.real_time_normal_false
        ##########################################################################################     

            # if  self.data["real_time_notification"]["exceeded_time"]["send"]=="true":
            #     self.real_time_notification_exceeded_time="true"
            #     self.real_time_exceed=self.real_time_exceed_true
            #     if  self.data["real_time_notification"]["exceeded_time"]["snapshot"]=="true":
            #         self.real_time_notification_exceeded_time_snapshot="true"
            #     else:
            #         self.real_time_notification_exceeded_time_snapshot="false"
            # else:
            #     self.real_time_notification_exceeded_time="false"
            #     self.real_time_exceed=self.real_time_exceed_false
        
        except Exception as error:
            print("wrong in initmethod queue:{}".format(error),flush=True)
    
    def pro_active_true(self):
        #print("enter into pro_active_true func",flush=True)
        #print(self.queue_count,flush=True)
        if self.pro_flag==True:
            if self.queue_count>self.data["pro_active_notification"]["exceeding_length"]:
                #print("pro_active_notification_exceeding_length",flush=True)
                self.pro_active_notification="true"
                self.pro_flag=False

            else:
                self.pro_active_notification="false"
        else:
             self.pro_active_notification="false"
        
        if self.queue_count<self.data["pro_active_notification"]["exceeding_length"]:
            self.pro_flag=True
            self.pro_active_notification="false"
             

            

    def pro_active_false(self):
        self.pro_active_notification="false"
         

    def real_time_exceed_true(self):
        #print("enter into real_time_exceed_true",flush=True)
        #print(self.queue_count,flush=True)
        if self.exceed_flag==True:
            if self.queue_count>self.data["real_time_notification"]["queue_exceeded"]["exceed_length"]:
                self.start_time=datetime.datetime.now().time().strftime('%H:%M:%S')
                self.real_time_notification_queue_exceeded="true"
                self.exceed_flag=False
            else:
                self.real_time_notification_queue_exceeded="false"
        else:
            self.real_time_notification_queue_exceeded="false"
            self.end_time=datetime.datetime.now().time().strftime('%H:%M:%S')
            self.exceed_time=datetime.datetime.strptime(self.end_time,'%H:%M:%S') - datetime.datetime.strptime(self.start_time,'%H:%M:%S')
            if (self.exceed_time.seconds/60)>self.data["real_time_notification"]["queue_exceeded"]["exceeded_time"]:
                self.real_time_notification_queue_exceeded_time="True"
            else:
                self.real_time_notification_queue_exceeded_time="false"
            if self.queue_count<self.data["real_time_notification"]["queue_exceeded"]["exceed_length"]:
                self.exceed_flag=True
        

    def real_time_exceed_false(self):
        #print("enter into real_time_exceed_false",flush=True)
        self.real_time_notification_queue_exceeded="false"
        self.real_time_notification_queue_exceeded_time="false"


    def real_time_normal_true(self):
        #print("enter into real_time_normal_true func",flush=True)
        if self.normal_flag==True:
            if self.queue_count<self.data["real_time_notification"]["queue_exceeded"]["exceed_length"]:
                self.real_time_notification_queue_normal="true"
                self.normal_flag=False
            else:
                self.real_time_notification_queue_normal="false"
        else:
            self.real_time_notification_queue_normal="false"
        if self.queue_count>self.data["real_time_notification"]["queue_exceeded"]["exceed_length"]:
            self.normal_flag=True
            self.real_time_notification_queue_normal="false"

    def real_time_normal_false(self):
        self.real_time_notification_queue_normal="false"
        



class QueueCounting:
    queue={}
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
        # self.final_json()

    def new_initmethod(self):

    
        sensor_ids = []
        rtspurls = []
        # dbp = DBQuery(host=dbhost, index="provisions_45d539626_n122d929569", office=office)
        # for sensor in dbp.search_without_office("algorithm:'Queue Management'"):
        dbp = DBQuery(host=dbhost, index="provisions", office=office)
        for sensor in dbp.search("algorithm:'QueueManagement'"):
            sensor_id = sensor["_id"]
            sensor_ids.append(sensor_id)
            try:
                rtspurl = sensor["_source"]["rtspurl"]
            except:
                rtspurl = "None"
            rtspurls.append(rtspurl)
        print("sensor_ids",sensor_ids)
        print("rtspurls",rtspurls)
        # /home/desktop6/Desktop/dhaval/Dhaval/Smart-City-Sample/analytics/object/custom_transforms/final.json
        coordinates = []
        zone_names = []
        # temp_sensor_id = []
        for sensorid in sensor_ids:
            temp_coordinate = []
            temp_zones = []
            dbz = DBQuery(host=dbhost, index="zones", office=office)
            
            for zones in dbz.search_without_office("botName:'QueueManagement' and sensorId:'"+str(sensorid)+"'"):
                # print("zones____",zones)
                coordinate = zones["_source"]["coordinate"]
                # print("coordinate_______",coordinate)
                # if len(coordinates) == 0:
                #     continue
                # if len(coordinate) > 0:
                #     if len(temp_sensor_id) > 0:
                #         continue
                #     else:
                #         temp_sensor_id.append(sensorid)
                temp_coordinate.append(coordinate)
                zone_name = zones["_source"]["name"]
                temp_zones.append(zone_name)
            coordinates.append(temp_coordinate)
            zone_names.append(temp_zones)
            
        # print("coordinates",coordinates)
        # print("zone_names",zone_names)
        # print("temp_sensor_id",temp_sensor_id)    
        

        dbr = DBQuery(host=dbhost, index="responsetypes", office=office)
        inspectionScores = []
        for responsetypes in dbr.search_without_office("botName:'QueueManagement'"):
            inspectionScore_p = responsetypes["_source"]["trueResponse"]["score"]
            inspectionScore_n = responsetypes["_source"]["falseResponse"]["score"]
            inspectionScores.append(inspectionScore_p)
            if len(inspectionScores) > 0:
                break
        # print("inspectionScores",inspectionScores)
        # print("inspectionScore",inspectionScore, flush=True)
        site_ids = []
        dbb = DBQuery(host = dbhost, index = "botconfigs", office=office)
        for botconfig in dbb.search_without_office("sensorId:'"+str(sensor_ids[0])+"'"):
            # print("botconfig___",botconfig)
            site_id = botconfig["_source"]["siteId"]
            site_ids.append(site_id)
            # print("site_id", site_id, flush=True)
            if len(site_ids) > 0:
                break
        # print("site_id",site_id)

        exceeding_lengths = []
        dbru = DBQuery(host=dbhost, index="rules", office=office)
        for rules in dbru.search_without_office("botName:'QueueManagement'"):
            exceeding_length = rules["_source"]["value"]
            exceeding_lengths.append(exceeding_length)
            if len(exceeding_lengths) > 0:
                break
        # print("exceeding_lengths",exceeding_lengths)

        dbt = DBQuery(host=dbhost, index="templates", office=office)
        texts = []
        for templates in dbt.search_without_office("botName:'QueueManagement'"):
            source = templates["_source"]
            message = source["whatsApp"]["message"]
            texts.append(message)
            if len(texts) > 0:
                break

        dbn = DBQuery(host=dbhost, index="notificationconfigs", office=office)
        pro_sends = []
        pro_snapshots = []
        real_sends = []
        real_snapshots = []
        
        for notification in dbn.search_without_office("botName:'QueueManagement'"):
            _type = notification["_source"]["type"]
            snapshot = notification["_source"]["attachedClip"]
            botConfigId = notification["_source"]["botConfigId"]
            # snapshots.append(snapshot)
            if _type == 1:
                real_sends.append("true")
                if snapshot == True:
                    real_snapshots.append("true")
                if snapshot == False:
                    real_snapshots.append("false")
                pro_sends.append("false")
                pro_snapshots.append("false")
            if _type == 2:
                pro_sends.append("true")
                if snapshot == True:
                    pro_snapshots.append("true")
                if snapshot == False:
                    pro_snapshots.append("flase")
                real_sends.append("false")
                real_snapshots.append("false")
            if len(pro_sends) > 0:
                break
        # print("pro_sends",pro_sends)
        # print("pro_snapshots",pro_snapshots)
        # print("real_sends",real_sends)
        # print("real_snapshots",real_snapshots)

        _sensors = []        
        for sensors_num in range(len(sensor_ids)):
            _rois = coordinates[sensors_num]
            _url = rtspurls[sensors_num]
            rois = []
            for rois_num in range(len(_rois)):

                real_snd = real_sends[0]
                real_snp = real_snapshots[0]
                pro_snd = pro_sends[0]
                pro_snp = pro_snapshots[0]
                exc = exceeding_lengths[0]

                rois.append({
                    "roi_box":_rois[rois_num],
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
                            "send": "true",
                            "snapshot": "false"
                        }
                    }
                })
            _sensors.append({
                "url":_url,
                "camera_id":sensor_ids[sensors_num],
                "roi":rois
            })


        print("_sensors",_sensors)

        json_data = {
            "sensors":_sensors
        }
        print("json_data",json_data)

        if (len(coordinates)) == 0 or len(zone_names) ==0 or len(_sensors) == 0 or len(pro_sends) ==0 or len(pro_snapshots) ==0 or len(real_sends) == 0 or len(real_snapshots)==0 or len(exceeding_lengths) ==0 or len(site_ids) ==0 or len(inspectionScores) ==0 or len(sensor_ids) ==0 or len(rtspurls) == 0:

            raise Exception("Error in new_initmethod")
        
        else:
            return [json_data, zone_names, botConfigId, site_id, inspectionScore_p, rtspurls, inspectionScore_n, exceeding_lengths[0], sensor_ids, texts]
        # return json_data

       

    
    # def final_json(self):
    #     required_data = self.new_initmethod()
    #     zone_names = required_data[1]
    #     rtspurls = required_data[5]

    #     final_json_data = []
    #     for url_num in range(len(rtspurls)):
    #         _zones = zone_names[url_num]

    #         zone_data = []
    #         for zone in _zones:
    #             zone_data.append({
    #                         "roi_name":zone,
    #                         "count":None})
    #         final_json_data.append({
    #                 "rtspurl":rtspurls[url_num],
    #                 "zone":zone_data
    #         })

    #     past_data = {
    #         "past_data":final_json_data
    #     }
    #     print("past_data",past_data)
    #     cwd = os.getcwd()
    #     print("cwd",cwd)
      
    #     with open("/home/custom_transforms/final.json","w") as final_json:
    #         json.dump(past_data, final_json)
    #     with open('/home/custom_transforms/final.json',"r") as final_json:
    #         data = json.load(final_json)
    #         print("Data____",data)
    #         print("Done!")



    def initmethod(self):
        # change_____________
        # f=open('/home/custom_transforms/config.json')
        # # f=open('config.json')
        # data=json.load(f)
        # for i in data['VisionBot']:
        #     if i["visionbotID"]==2:      #BotconfigID
        #         self.roi_path=i['roipath']
        # r=open(self.roi_path)
        # data = json.load(r)
        # change_____________
        try:
            data = self.new_initmethod()[0]           #add...
        except Exception as error:
            print("Error in new_initmethod: ",error, flush=True)
        for ii in data["sensors"]:
            # print("iiiiiiiiii",ii)
            print("cam___id",ii["camera_id"])
            self.camera_id=ii["camera_id"]
            self.queue[self.camera_id]=[]
            self.roi=ii["roi"]
            self.total_count[self.camera_id]={}
            self.exit_count[self.camera_id]={}
            self.entry_count[self.camera_id]={}

            # self.exceed_time[self.camera_id]={}
            for j in range(len(self.roi)):
                q=Queue(self.roi[j],self.camera_id)
                self.queue[self.camera_id].append(q)
                self.total_count[self.camera_id][j]=0
                self.exit_count[self.camera_id][j]=0
                self.entry_count[self.camera_id][j]=0
                # self.exceed_time[self.camera_id][j]=0
                
            
        

    
    @classmethod
    def give_queue(cls):
        return cls.queue 
    
   
    def process_frame(self,frame):
        # # myAlgorithm="QueueManagement"
        # a = self.dbb.get(_id='60d2fd4fbc8b0f3a2cdb2204')
        # print("temp___________",a["_source"])

        # print("JSON_DATA_____________", self.new_initmethod())
        #     print("temp___________",sensor["_source"], flush=True)
        try:

            required_data = self.new_initmethod()
        except Exception as error:
            print("Error in new_initmethod: ",error, flush=True)
        zone_names = required_data[1]
        print("zone_names",zone_names)
        botConfigId = required_data[2]
        # print("botConfigId",botConfigId)
        site_id = required_data[3]
        # print("_site_id",site_id)
        inspectionScore_p = required_data[4]
        # print("exc",inspectionScore_p)
        rtspurls = required_data[5]
        # print("_sensors",rtspurls)
        inspectionScore_n = required_data[6]
        # print("inspectionScore",inspectionScore_n)
        exe = required_data[7]

        sensor_ids = required_data[8]
        print("____exe",exe)


        def final_json_data():
            final_json_data = []
            for snr_num in range(len(sensor_ids)):
                _zones = zone_names[snr_num]

                zone_data = []
                for zone in _zones:
                    zone_data.append({
                                "roi_name":zone,
                                "count":None})
                final_json_data.append({
                        "sensor_id":sensor_ids[snr_num],
                        "zone":zone_data
                })

            past_data = {
                "past_data":final_json_data
            }
            print("past_data",past_data)
            cwd = os.getcwd()
            print("cwd",cwd)

            data = None
            try:
                with open("/home/custom_transforms/final.json","r") as final_json:
                    data = json.load(final_json)
                    print("Data____",data)
            except:
                print("create")
                if data == None:
                    with open("/home/custom_transforms/final.json","w") as final_json:
                        json.dump(past_data, final_json)

            # with open("/home/custom_transforms/final.json","w") as final_json:
            #     json.dump(past_data, final_json)
            _sensors= []
            _zones = []

            init_count = []
            if data != None:
                
                with open("/home/custom_transforms/final.json","r") as final_json:
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

            print("ori_zone", zone_names, _zones)
            print("ori_rtsp", sensor_ids, _sensors)

            if zone_names != _zones or sensor_ids != _sensors:
                print("creates_____")
                with open("/home/custom_transforms/final.json","r") as final_json:
                    data = json.load(final_json)
                    # print("Data____hr",data)

            new_count = []
            for snr in past_data["past_data"]:
                cam_id = snr["sensor_id"]
                cnt= 0
                temp_new_count = []
                for _zone in snr["zone"]:
                    _zone["count"] = self.total_count[cam_id][cnt]
                    temp_new_count.append(_zone["count"])
                new_count.append(temp_new_count)
            # print("new_count",new_count,init_count)
      


            if new_count != init_count:
                new_flag = True
                print("new_past_data_1",past_data)
                with open("/home/custom_transforms/final.json","w") as final_json:
                    json.dump(past_data, final_json)
            else:
                print("new_past_data_2",past_data)
                new_flag = False

            print("Flaggggggg",new_flag)

            return new_flag

        # print("timestamp____",json_msg["timestamp"])
        # try:
        #     print("timestamp____",final_json_data())
        # except Exception as err:
        #     print("timestamp____1",err)
        # print("timestamp____t",self.total_count)

        # new = final_json_data()
        # ad = self.add.append(new)
        # print("nnnn____ad",ad)
        # print("nnnn",new, type(new))


        try:
            #print("processing frames for queue----------", flush=True)
            messages=list(frame.messages())
            print("messages",len(messages), flush=True)
            if len(messages)>0:
                try:

                    new = final_json_data()
                    # print("nnnn",new, type(new))
                except Exception as error:
                    print("Error in final_json_data: ",error)
                print("getting messages for queue-----", flush=True)
                # r=open(self.roi_path)
                # data = json.load(r)
                data = required_data[0] 
                print("Data_______________",data)
                json_msg = json.loads(messages[0])
                self.roi_box=[]
                for i in data['sensors']:
                    # print("iiiiiiiiii____________________",i)
                    # print("cam___iddddddddddddd",i["camera_id"])
                    #========================CCTV=========================
                    if i["url"]==json_msg['source']:
                        self.camera_id=i['camera_id']
                        #self.checklist=i["checklist"]
                        #self.siteId=i["siteId"]
                        for j in i["roi"]:
                            print("storing roi box",flush=True)
                            self.roi_box.append(j["roi_box"])
                            #self.roiname=j["roiname"]

                for i in data['sensors']:
                    if i["url"]==json_msg['source']:
                                                        
                        snsr = json_msg["tags"]["sensor"]
                        # print("snsr",snsr, flush=True)
                        

                        sensor_index = rtspurls.index(i["url"])
                        # print("sensor_index",sensor_index, flush=True)
                        sensor_zone = zone_names[sensor_index]
                        # print("sensor_zone",sensor_zone, flush=True)
                        zone_cnt = 0
                        # print("sensor_zone",sensor_zone)
                        for zone_name in sensor_zone:

                            json_msg["roi"]=self.roi_box
                            json_msg["queue_count"]=self.total_count
                            json_msg["exceed_time"]=0
                            json_msg["camera"]=self.camera_id 
                            json_msg["time"] = time.time()

                            # if new_flag == True:
                            print("nnnn_______2",new, type(new))
                            if new == True:
                                print("newwww",new)
                                json_msg["roiName"] = zone_name  
                                json_msg["queue_length"]=self.total_count[self.camera_id][zone_cnt]  
                                print("queueLength_1",self.total_count,time.time(),flush=True)
                                # json_msg["exceed_time"]=0                     #change..
                                # json_msg["queueLength"] = exc
                                json_msg["sensorId"]=self.camera_id 
                                json_msg["botConfigId"] = botConfigId 
                                json_msg["siteId"] = site_id  
                                if self.total_count[self.camera_id][zone_cnt] > int(exe):
                                    json_msg["complaince"] = False 
                                    json_msg["inspectionScore"] =inspectionScore_n 
                                else:
                                    json_msg["complaince"] = True 
                                    json_msg["inspectionScore"] =inspectionScore_p 
                                json_msg["video_path"] = None
                                try:
                                    time_stamps = []
                                    # r = list(self.dbq.search("sensor='"+snsr+"'"))# and time>"+str(a["_source"]["time"])))#+" and duration>"+ str(a["_source"]["time"]+a["_source"]["duration"]*1000) +" ) ", size=1))
                                    # print("rrrrrrrrrr",r, flush=True)
                                    for a  in self.dba.search("sensor='"+snsr+"'"):
                                        # print("aaaaaaa",a)
                                        r = list(self.dbq.search("sensor='"+snsr+"'and time>"+str(a["_source"]["time1"])))#+" and duration>"+ str(a["_source"]["time"]+a["_source"]["duration"]*1000) +" ) ", size=1))
                                        # print("rrrrrrrrrr",r, flush=True)
                                    
                                        for _r in r:
                                            time_stamps.append(_r["_source"]["time"])
                                        min_timestamp = max(time_stamps)

                                        reco_index = time_stamps.index(min_timestamp)

                                        path_r = r[reco_index]["_source"]["path"]
                                        # print("time_stamps___________",time_stamps)
                                                                        
                                except Exception as err:
                                    print("Error in db quary",err)

                                if len(time_stamps) > 0:
                                    print("path_r",path_r,flush=True)
                                    json_msg["video_path"] = str(path_r) 
                                
                                json_msg["checklist"]="WRK_COM" 
                                json_msg['botName']="QueueManagement" 
                                frame.remove_message(messages[0])
                                frame.add_message(json.dumps(json_msg))
                                print(":json_msg",final_json_data())
                                print(":json_msg",json_msg)

                            else:
                                print("else____")
                                json_msg["roiName"] = "None"  
                                json_msg["queue_length"]="None"  
                                print("queueLength_2",self.total_count,time.time(),flush=True)
                                # json_msg["exceed_time"]=0                     #change..
                                # json_msg["queueLength"] = exc
                                json_msg["sensorId"]="None" 
                                json_msg["botConfigId"] = "None" 
                                json_msg["siteId"] = "None"  
                                json_msg["complaince"] = "None" 
                                json_msg["inspectionScore"] = "None" 
                                json_msg["video_path"] = "None"
                                json_msg["checklist"]="None" 
                                json_msg['botName']="None" 
                                frame.remove_message(messages[0])
                                frame.add_message(json.dumps(json_msg))
                            
                            zone_cnt += 1    
                            
                    #==================================================
                    #=======================VIDEOS=========================
                    #self.camera_id=0
                    #for j in i["roi"]:
                    #    print("storing roi box",flush=True)
                    #    self.roi_box.append(j["roi_box"])
                    #break
                    #==================================================
                #print(self.roi_box,flush=True)
                # json_msg["queue_count"]=self.total_count
                # json_msg["queue_length"]=self.total_count
                # json_msg["roi"]=self.roi_box
                # json_msg["exceed_time"]=0
                # json_msg["camera"]=self.camera_id
                # json_msg["roiName"]="HelpDesk",
                # json_msg["checklist"]="WRK_COM",
                # json_msg['siteId']="60c9c1f71e41fd0aecb0c4f9",
                # json_msg['botName']="queue-mgmt",
                # json_msg['sensorId']="60d2f9a2bc8b0f3a2cdb21fc",
                # json_msg['botConfigId']="60d2fd4fbc8b0f3a2cdb2204",
                # frame.remove_message(messages[0])
                # frame.add_message(json.dumps(json_msg))
                for i in range(len(self.roi_box)):
                    #print("it is reinitalizing ",flush=True)
                    self.queue[self.camera_id][i].queue_count=0
                   
                self.get_queue_count(frame)
                

        except Exception as error:
            print("wrong in processing_frame:{}".format(error),flush=True)
        return True

    def inroi(self,x,y,line):
        k=line
        p1 = Point(x,y)
        coords = [(k[0],k[1]), (k[2],k[3]), (k[4],k[5]), (k[6],k[7])]
        poly = Polygon(coords)
        info=p1.within(poly)
        return info
        


    def get_queue_count(self,frame):
        try:
            detected_centers=[]
            rects=[]
            detections = [x for x in frame.regions()]
            messages=list(frame.messages())
            e = datetime.datetime.now()
            date='{}/{}/{}'.format(e.day ,e.month, e.year)
            time='{}:{}:{}'.format(e.hour, e.minute, e.second)
            # time='{}:{}:{}'.format(e.hour, e.minute, e.second)
            if len(messages)>0:
                json_msg = json.loads(messages[0])  
                for i in json_msg:
                    if i=='objects':
                        #print(json_msg,flush=True)
                        dic=json_msg[i]
                        for j in range(len(dic)):
                            if dic[j]['detection']['label']=='person':
                                x_max=dic[j]['x']+dic[j]['w']
                                y_max=dic[j]['y']+dic[j]['h']
                                x=dic[j]['x']
                                y=dic[j]['y']
                                rects.append([x,y,x_max,y_max])
                                # if self.centroid_tracking:
                                #     x_c=(x_max+x)/2
                                #     y_c=(y_max+y)/2
                                # else:
                                #     x_c=(x_max+x)/2
                                #     y_c=y_max
                                # detected_centers.append([x_c,y_c])
                        break
            else:
                json_msg={}
            detected_centers,_=self.tracker.update(rects)
            #print("total number of people detected",flush=True)
            #print(list(detected_centers.keys()),flush=True)
        except Exception as error:
            print("wrong in starting:{}".format(error),flush=True)
        for i in list(detected_centers.keys()):
            # for i in detected_centers:
            # print("1&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&",flush=True)
            #print(detected_centers.keys(),flush=True)
            try:
                x=detected_centers[i][0]
                y=detected_centers[i][1]
            except Exception as error:
                print("wrong in tracker:{}".format(error),flush=True)
            #print("shsunksdksd",flush=True)
            print("camera_______________",self.camera_id)
            print("len_________",len(self.queue[self.camera_id]))
            for j in range(len(self.queue[self.camera_id])):
                print("jjjjjjjjjj",j)
                try:
                    info=self.inroi(x,y,self.queue[self.camera_id][j].roi)
                    print("roiiiiiiiii",self.queue[self.camera_id][j].roi)
                    print("total__________",self.queue[self.camera_id][j])
                    print("info____________",info)
                except Exception as error:
                    print("wrong in tracker:{}".format(error),flush=True)

                #print(info,flush=True)
                try:
                    if info==True:
                        if i not in self.queue[self.camera_id][j].entry:
                            #print("NO of people entered",flush=True)
                            #print(self.queue[self.camera_id][j].entry,flush=True)
                            self.queue[self.camera_id][j].entry.append(i)
                            self.tracker.start_time[i]=time      
                        #print("NO of people entered in queue:{}".format(self.queue[self.camera_id][j].queue_count),flush=True)
                        self.queue[self.camera_id][j].queue_count=self.queue[self.camera_id][j].queue_count+1
                        self.tracker.end_time[i]=time  
                        # spend_time=datetime.datetime.strptime(self.tracker.end_time[i],'%H:%M:%S') - datetime.datetime.strptime(self.tracker.start_time[i],'%H:%M:%S')
                        # json_msg['objects'][self.tracker.index[i]]['detection']['wait']=spend_time
                        
                    else:
                        if i in self.queue  [self.camera_id][j].entry and i not in self.queue[self.camera_id][j].exit:
                            self.tracker.end_time[i]=time 
                            # self.queue[self.camera_id][j].exit.append(i)
                            spend_time=datetime.datetime.strptime(self.tracker.end_time[i],'%H:%M:%S') - datetime.datetime.strptime(self.tracker.start_time[i],'%H:%M:%S')   
                    
                except Exception as error:
                    print("new entry:{}".format(error),flush=True)
                        
                   
                    

        try:
            for j in range(len(self.queue[self.camera_id])):
                self.allowed_length=2
                self.total_count[self.camera_id][j]=self.queue[self.camera_id][j].queue_count
                #if self.total_count>=self.allowed_length and self.compliance==True:
                #    self.compliance=False
                #    json_msg["compliance"]=self.compliance
                #    json_msg["Inspection_Score"]="-10"
                #else:
                    #self.compliance=True
                    #json_msg["compliance"]=self.compliance
                    #json_msg["Inspection_Score"]="0"

                self.entry_count[self.camera_id][j]=len(self.queue[self.camera_id][j].entry)
                self.exit_count[self.camera_id][j]=self.entry_count[self.camera_id][j]-self.total_count[self.camera_id][j]
                
                self.queue[self.camera_id][j].pro_active()
                self.queue[self.camera_id][j].real_time_exceed()
                self.queue[self.camera_id][j].real_time_normal()

                # if self.queue[self.camera_id][j].people_count>self.queue[self.camera_id][j].min_people and self.queue[self.camera_id][j].people_count<88=self.queue[self.camera_id][j].max_people:
                #     if self.queue[self.camera_id][j].people_count>self.queue[self.camera_id][j].pre_max:
                #         # json_msg["notification"]="yes_pre"
                #         json_msg["notification_roi_id"][j]="yes_pre"
                #     if self.queue[self.camera_id][j].flag==False:
                #         self.queue[self.camera_id][j].end_time=datetime.datetime.now().time().strftime('%H:%M:%S')
                #         self.queue[self.camera_id][j].wait_time=datetime.datetime.strptime(self.queue[self.camera_id][j].end_time,'%H:%M:%S') - datetime.datetime.strptime(self.queue[self.camera_id][j].start_time,'%H:%M:%S') 
                #         print("wait_time123332",flush=True)
                #         print(wait_time,flush=True)
                #         # json_msg["notification"]="yes_exit"
                #         json_msg["notification_roi_id"][j]="yes_exit"
                #         json_msg["exceed_time"]=str(self.queue[self.camera_id][j].wait_time.total_seconds())
                #         json_msg["time_end"]=self.queue[self.camera_id][j].end_time
                #         self.queue[self.camera_id][j].flag=True

                # if self.queue[self.camera_id][j].people_count>self.queue[self.camera_id][j].max_people:
        
                #     if self.queue[self.camera_id][j].flag==False:
                #         wait_time=datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'),'%H:%M:%S') - datetime.datetime.strptime(self.queue[self.camera_id][j].start_time,'%H:%M:%S') 
                #         json_msg["exceed_time"]=str(wait_time.total_seconds())
                #         if wait_time.seconds>self.queue[self.camera_id][j].renotification_time:
                #             # json_msg["notification"]="yes_entry"
                #             json_msg["notification_roi_id"][j]="yes_entry"
                #     if self.queue[self.camera_id][j].flag==True:
                #         # json_msg["notification"]="yes_entry"
                #         json_msg["notification_roi_id"][j]="yes_entry"
                #         self.queue[self.camera_id][j].start_time=datetime.datetime.now().time().strftime('%H:%M:%S')
                #         json_msg["time_start"]=self.queue[self.camera_id][j].start_time
                #         self.queue[self.camera_id][j].flag=False
                #     print("Send alert or whatsapp message",flush=True)
        except Exception as error:
            print("error in:{}".format(error),flush=True)

        self.queue_count=self.total_count[self.camera_id]
        # keys_list=list(self.queue_count.values())
        # value1=keys_list[0]
        #val = self.queue_count.items()
        print("prrinting self.queue------", self.queue_count, flush=True)
        # print("printing value", value1, flush=True)
        #print("printing total_count------", self.total_count, flush=True)
        #print("printing self.total_count[self.camera_id]",  self.total_count[self.camera_id], flush=True)
        
        # if value1>=self.allowed_length and self.compliance==True:
        #     print("printing, compliance is false, queue is exceeded with----", value1, flush=True)
        #     self.compliance=False
        #     compliance=False
        #     json_msg["compliance"]=compliance
        #     json_msg["Inspection_Score"]=-10
        #     json_msg["queue_length"]=value1
        # else:
        #     print("printing, compliance is True, queue is NOT exceeded with----", value1, flush=True)
        #     self.compliance=True
        #     compliance=True
        #     json_msg["compliance"]=compliance
        #     json_msg["inspectionScore"]=10
        #     json_msg["queueLength"]=value1

        json_msg["queue_count"]=self.total_count[self.camera_id]
        #json_msg["queue_count1"]=self.total_count
        #json_msg["queue_length"]=value
        json_msg["camera"]=self.camera_id
        json_msg["exit_count"]=self.exit_count[self.camera_id]
        json_msg["entry_count"]=self.entry_count[self.camera_id] 
        if len(messages)>0:           
            frame.remove_message(messages[0])
            try:
                for key, value in self.tracker.index.items(): 
                    for j in range(len(dic)):
                        if j==value:
                            dic[j]['detection']['id']=key
                json_msg["objects"]=dic
            except Exception as error:
                print("error  in mapping id:{}".format(error),flush=True)

        frame.add_message(json.dumps(json_msg))
        #print(json_msg,flush=True)
                            
        return True
    

class Capture(object):
    def __init__(self):
        self.timestamp=0
        self.pathv=" "
        self.path1=" "
        f=open('/home/custom_transforms/config.json')
        data=json.load(f)
        for i in data['VisionBot']:
            if i["visionbotID"]==2:
                self.roi_path=i['roipath']
                self.broker=i['mqtt']['host']
                self.port=i['mqtt']['port']
                self.video_url=i['videourl']
                self.image_url=i['imageurl']

    def write_image(self,buffer,json_msg):
        #print("enter write image",flush=True)
        with gst_buffer_data(buffer, Gst.MapFlags.READ) as data:
            path1=os.getcwd()
            #print(path1,flush=True)
            self.timestamp=json_msg['timestamp']
            path2=os.path.join(path1,"screenshot","img_"+str(self.timestamp))
            #print(path2,flush=True)
            pathi="{}.jpeg".format(path2)
            #print(pathi,flush=True)
            os.makedirs(os.path.dirname(pathi), exist_ok=True)
            with open(pathi,"wb",0) as output:
                #print("write",flush=True)
                output.write(data)


    # def send_notification_without_snap(self,json_msg,text,time,date,i):
    #     #print("enter  send_notication_without_snap",flush=True)
    #     json_msg1={"mqttEventName": "NOTIFICATION",
    #     #"eventName": "AGGRESIVEBEHAVIOR",
    #     # "notificationType": "TEXT",
    #     # "eventCode": "EVN001",
    #     # "eventId": "d62a7842-2053-4e1b-9ba9-a1dca1ca8f5d",
    #     "textMessage": text,
    #     # "cameraID":json_msg["camera"],
    #     # "roiId":i,
    #     "roiName": "Counter"+str(i),
    #     "visionBotName": "Queue Counting",
    #     # "visionBotId": "1",
    #     "timeStamp": time,
    #     "date": date,
    #     # "location": "Office1",
    #     # "locationId": "1",
    #     # "orgId": "1",
    #     "imagePath":"",
    #     "videoPath":"",
    #     # "visualisations": "none",
    #     "analytics": "none"
    #     }
    #     #print("update",flush=True)
    #     notification(self.broker,self.port,json_msg1)

    def send_notification_without_snap(self,json_msg,text,time,date,i):
        json_msg1={"mqttEventName": "NOTIFICATION",
        "textMessage": text,
        "roiName": "Counter"+str(i),
        "visionBotName": "Queue Counting",
        "timeStamp": time,
        "date": date,
        "imagePath":"",
        "videoPath":json_msg["video_path"],
        "analytics": "none"
        }
        print("send_notification_without_snap",json_msg1)
        notification(self.broker,self.port,json_msg1)

    def send_notification_with_snap(self,json_msg,text,time,date,i):
        #print("enter  send_notication_with_snap",flush=True)
        json_msg1={"mqttEventName": "NOTIFICATION",
        "eventName": "AGGRESIVEBEHAVIOR",
        "notificationType": "TEXT",
        "eventCode": "EVN001",
        "eventId": "d62a7842-2053-4e1b-9ba9-a1dca1ca8f5d",
        "textMessage": text,
        "cameraID":json_msg["camera"],
        "roiId":i,
        "roiName": "Counter"+str(i),
        "visionBotName": "Queue Counting",
        "visionBotId": "1",
        "timeStamp": time,
        "date": date,
        "location": "Office1",
        "locationId": "1",
        "orgId": "1",
        "imagePath":self.image_url+str(self.timestamp)+'.jpeg',
        "videoPath":"",
        "visualisations": "none",
        "analytics": "none"
        }
        #print("update",flush=True)
        notification(self.broker,self.port,json_msg1)


    def process_frame(self,frame):
        messages=list(frame.messages())
        e = datetime.datetime.now()
        date='{}/{}/{}'.format(e.day ,e.month, e.year)
        time='{}:{}:{}'.format(e.hour, e.minute, e.second)
        queues=QueueCounting.give_queue()
        if len(messages)>0:
            json_msg = json.loads(messages[0])
            #print("screen",flush=True)
        try:
            for region in frame.regions():
                #print("capture",flush=True)
                self.timestamp=json_msg['timestamp']
                for tensor in region.tensors():
                    #print(tensor.has_field('format'),flush=True)
                    # if tensor.has_field('format'):
                    # print(tensor['format'],flush=True)
                    # if tensor['format'] == "cosine_distance": work when reiidentification 
                    buffer = frame._VideoFrame__buffer
                    camera=json_msg["camera"]
                    # for i in queues.keys():
                        # print("enter into capture queue loop",flush=True)
                    for roi_id,queue in enumerate(queues[camera]):
                        #print("enter into capture queue loop 2",flush=True)
                        #print(queue.pro_active_notification,flush=True)
                        #print(queue.queue_count,flush=True)
                        if queue.pro_active_notification=="true":
                            text="Queue about to exceed from its limit"
                            #print(text,flush=True)
                            if queue.pro_active_notification_snapshot=="true":
                                self.write_image(buffer,json_msg)
                                self.send_notification_with_snap(json_msg,text,time,date,roi_id)
                            else:
                                self.send_notification_without_snap(json_msg,text,time,date,roi_id)

                        if queue.real_time_notification_queue_exceeded=="true":
                            text="Queue exceed from its limit"
                            #print(text,flush=True)
                            if queue.real_time_notification_queue_exceeded_snapshot=="true":
                                self.write_image(buffer,json_msg)
                                self.send_notification_with_snap(json_msg,text,time,date,roi_id)
                            else:
                                self.send_notification_without_snap(json_msg,text,time,date,roi_id)

                        if queue.real_time_notification_queue_exceeded_time=="true":
                            text="Queue remain exceeded for"+str(queue.data["real_time_notification"]["queue_exceeded"]["exceeded_time"])+"minute"
                            #print(text,flush=True)
                            if queue.real_time_notification_queue_exceeded_snapshot=="true":
                                self.write_image(buffer,json_msg)
                                self.send_notification_with_snap(json_msg,text,time,date,roi_id)
                            else:
                                self.send_notification_without_snap(json_msg,text,time,date,roi_id)


                        if queue.real_time_notification_queue_normal=="true":
                            text="Queue come under its limit"
                            if queue.real_time_notification_queue_normal_snapshot=="true":
                                self.write_image(buffer,json_msg)
                                self.send_notification_with_snap(json_msg,text,time,date,roi_id)
                            else:
                                self.send_notification_without_snap(json_msg,text,time,date,roi_id)



                            
        except Exception as error:
            print("Error processing frame: {}".format(error))
            
        return True