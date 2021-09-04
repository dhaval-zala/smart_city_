import gstgva  # pylint: disable=import-error  
from gstgva.util import libgst, gst_buffer_data
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import numpy as np
import math
import copy
import json
from munkres import Munkres
import os
from collections import OrderedDict
import logging
import datetime
from notification import notification
from configuration import env
from memory_profiler import profile
from shapely.geometry import Point, Polygon


class Queue:
    def __init__(self,max_people,min_people,max_distance,renotification_time,pre_max,roi,max_exit_distance,camera_id=0):
        self.max_people=max_people
        self.min_people=min_people
        self.max_distance=max_distance
        self.max_exit_distance=max_exit_distance
        self.valid_queue=False
        self.roi=roi
        self.people_count=0
        self.start_time=0
        self.end_time=0
        self.wait_time=0
        self.date=0
        self.flag=True
        self.camera_id=camera_id
        self.renotification_time=renotification_time
        self.entry=[]
        self.exit=[]
        self.pre_max=pre_max
        self.merge_queue=[]

        
    def wait_time(self):
        self.wait_time=datetime.datetime.strptime(self.end_time,'%H:%M:%S') - datetime.datetime.strptime(self.start_time,'%H:%M:%S') 
        return self.wait_time
        
    def total_people(self,queue):
        if len(self.merge_queue)>0:
            for i in self.merge_queue:
                self.people_count=self.people_count+queue[i].people_count
            return self.people_count
        else:
            return self.people_count


class QueueCounting:

    def __init__(self):
        # Array of Gallery Objects - {embeddings(numpy array), timestamp}
        self.identities = []
        self.reid_threshold = 0.5
        self.matcher = Munkres()
        self.timestamp = 0
        self.objectID=0
        self.end_time=OrderedDict()
        self.start_time=OrderedDict()

        #######################################################
        self.max_people=3
        self.min_people=1
        self.max_distance=[180,180]
        self.max_exit_distance=[250,250]
        self.thr_spend_time_min=10
        self.broker="192.168.1.22"
        self.port= 30793
        self.roi=[[569,597,1245,261,1637,406,1048,856,0]]
        # self.roi_line=[[803,716,1348,339,0]]
        # self.roi_line=[[565,0,565,334,0]]  #video
        # self.roi_line=[[753,755,1265,447,0]] #video2
        self.roi_line=[[185,604,351,284,0],[981,520,918,255,1]]
        self.roi_box=[[697,101,1039,122,1278,590,704,594,0],[63,546,327,141,608,156,530,688,1]]
        self.total_count={}
        self.exit_count={}
        self.entry_count={}
        self.centroid_tracking=True
        self.method="distance_from_line"
        self.method="cross_line"
        # self.queue={}   #for cctv
        self.queue=[]    #for video
        self.camera_id=0
        self.renotification_time=[120,120]
        self.pre_max=[2,2]
        self.initmethod()

    def initmethod(self):
        # f=open('/home/custom_transforms/config.json')
        # data=json.load(f)
        # self.roi_path=data['VisionBot']['roipath']
        # r=open(self.roi_path)
        # data = json.load(r)
        # for cctv camera
        # for i in data["sensors"]:
        #     self.queue[i]=[]
        #     self.total_count[i]={}
        #     for j in i["roi"]:
        #         q=Queue(i["max_people"][j],i["min_people"][j],i["max_distance"][j],i["roi"][j],i["camera_id"])
        #         self.queue[i].append(q)
        #         self.total_count[i][j]=0
        try:
            ########################################################
            for i in range(len(self.roi_box)):
                q=Queue(self.max_people,self.min_people,self.max_distance[i],self.renotification_time[i],self.pre_max[i],self.roi_box[i],self.max_exit_distance[i])
                print("first stage",flush=True)
                print(q,flush=True)
                self.queue.append(q)
                self.total_count[i]=0
                self.exit_count[i]=0
                self.entry_count[i]=0
        except Exception as error:
                print("wrong at starting:{}".format(error),flush=True)

    def process_frame(self, frame):
        messages = list(frame.messages())
        if len(messages) > 0:
            json_msg = json.loads(messages[0])
            # json_msg["count"] = {"people": len(self.identities)}
            self.timestamp = int(json_msg["timestamp"]) / 1000000000
            json_msg["queue_count"]=self.total_count
            json_msg["roi"]=self.roi_line
            json_msg["notification"]='no'
            for i in range(len(self.roi_line)):
                self.queue[i].people_count=0
            frame.remove_message(messages[0])
            frame.add_message(json.dumps(json_msg))

            self.get_ids_by_embeddings(frame)
            self.get_queue(frame)
        return True

    @staticmethod
    def compute_reid_distance(test_embedding, reference_embedding):
        xx = np.dot(test_embedding, test_embedding)
        yy = np.dot(reference_embedding, reference_embedding)
        xy = np.dot(test_embedding, reference_embedding)
        norm = math.sqrt(xx * yy) + 1e-6
        return np.float32(1.0) - xy / norm

    def distance_from_line(self,x,y,line):
        # A=line[3]-line[1]
        # B=line[0]-line[2]
        # C=line[1]*(-B)+line[2]*(-A)
        # dist=(A*x+B*y+C)/(A**2+B**2)**0.5
        k=line
        p1 = Point(x,y)
        coords = [(k[0],k[1]), (k[2],k[3]), (k[4],k[5]), (k[6],k[7])]
        poly = Polygon(coords)
        info_2=p1.within(poly)
        return info_2
        # return abs(dist)

    def get_ids_by_embeddings(self, frame):
        try:
            detected_tensors = []
            detection_ids = []
            detections = [x for x in frame.regions()]
            self.detected_centers=[]
            messages=list(frame.messages())
            for i, detection in enumerate(detections):
                bbox=detection.rect()
                if detection.label() == "person":
                    for j, tensor in enumerate(detection.tensors()):
                        if tensor.name() == "face_feature" and tensor.format() == "cosine_distance":
                            detected_tensors.append(tensor.data())
                            detection_ids.append(i)
                            print("garg",flush=True)
                            # x=(bbox[0]+bbox[2]+bbox[0])/2
                            # y=bbox[1]+bbox[3]
                            # self.detected_centers.append([x,y])
            if len(messages)>0:
                json_msg = json.loads(messages[0])  
                for i in json_msg:
                    if i=='objects':
                        print(json_msg,flush=True)
                        self.dic=json_msg[i]
                        for j in range(len(self.dic)):
                            if self.dic[j]['detection']['label']=='person':
                                x_max=self.dic[j]['x']+self.dic[j]['w']
                                y_max=self.dic[j]['y']+self.dic[j]['h']
                                x=self.dic[j]['x']
                                y=self.dic[j]['y']
                                # rects.append([x,y,x_max,y_max])
                                if self.centroid_tracking:
                                    x_c=(x_max+x)/2
                                    y_c=(y_max+y)/2
                                else:
                                    x_c=(x_max+x)/2
                                    y_c=y_max
                                self.detected_centers.append([x_c,y_c])
                        break


            if len(detected_tensors) == 0:
                return
            if len(self.identities) == 0:
                for i in range(len(detected_tensors)):
                    self.identities.append({"embedding": copy.deepcopy(
                        detected_tensors[i]), "timestamp": self.timestamp,"coordinate":self.detected_centers[i],"id":self.objectID,"index":i})
                    self.objectID += 1
                return
            distances = np.empty(
                [len(detected_tensors), len(self.identities)], dtype=np.float32)

            for i in range(len(detected_tensors)):
                for j in range(len(self.identities)):
                    distances[i][j] = QueueCounting.compute_reid_distance(
                        detected_tensors[i], self.identities[j]["embedding"])

            matched_indexes = self.matcher.compute(distances.tolist())
            matched_detections = set()

            for match in matched_indexes:
                print("distance for matching:{}".format(distances[match[0]][match[1]]),flush=True)
                print("match detection:{} and identities:{}".format(match[0],match[1]) )
                if distances[match[0]][match[1]] <= self.reid_threshold:
                    self.identities[match[1]]["timestamp"] = self.timestamp
                    self.identities[match[1]]["coordinate"] = self.detected_centers[match[0]]
                    self.identities[match[1]]["index"]=match[0]
                    matched_detections.add(match[0]) 

            for i in range(len(detected_tensors)):
                if i not in matched_detections:
                    self.identities.append({"embedding": copy.deepcopy(
                        detected_tensors[i]), "timestamp": self.timestamp,"coordinate":self.detected_centers[i],"id":self.objectID,"index":i})
                    self.objectID += 1
            n = len(self.identities)
            i = n - 1
            while i >= 0:
                # overdue if pass the last 5 seconds
                if int(self.timestamp - int(self.identities[i]["timestamp"])) > :
                    self.identities[i] = self.identities[n - 1]
                    self.identities.pop(n - 1)
                    n -= 1
                i -= 1
        except Exception as e:
            print("error:{}".format(e),flush=True)

        print("dfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsfsdfsd",flush=True)

    def get_queue(self, frame):
        e = datetime.datetime.now()
        date='{}/{}/{}'.format(e.day ,e.month, e.year)
        time='{}:{}:{}'.format(e.hour, e.minute, e.second)
        messages = list(frame.messages())
        if len(messages)>0:
            json_msg = json.loads(messages[0]) 
        else:
            json_msg ={}
        n = len(self.identities)
        print(n,flush=True)
        for i in range(n):
            try:
                x=self.identities[i]["coordinate"][0]
                y=self.identities[i]["coordinate"][1]
                obj=self.identities[i]["id"]
            except Exception as error:
                print("wrong in identities:{}".format(error),flush=True)
            print("shsunksdksd",flush=True)
            for j in range(len(self.queue)):
                dist=self.distance_from_line(x,y,self.queue[j].roi)
                print("Distance from line"+str(j)+"of"+str(obj),flush=True)
                print(dist,flush=True)
                info=dist
                # if dist<self.queue[j].max_distance:
                #     info=True
                # else:
                #     info=False
                # if dist>self.queue[j].max_exit_distance:
                #     info1=True
                # else:
                #     info1=False

                print(info,flush=True)
                try:
                    if info==True:
                        if obj not in self.queue[j].entry:
                            self.queue[j].entry.append(obj)
                            self.start_time[obj]=time      
                        self.queue[j].people_count=self.queue[j].people_count+1
                        self.end_time[obj]=time  
                        spend_time=datetime.datetime.strptime(self.end_time[obj],'%H:%M:%S') - datetime.datetime.strptime(self.start_time[obj],'%H:%M:%S')
                        # json_msg['objects'][self.tracker.index[i]]['detection']['wait']=spend_time
                        break

                    else:
                        if obj in self.queue[j].entry and obj not in self.queue[j].exit:
                            self.queue[j].exit.append(obj)
                            self.end_time[obj]=time 
                            spend_time=datetime.datetime.strptime(self.end_time[obj],'%H:%M:%S') - datetime.datetime.strptime(self.start_time[obj],'%H:%M:%S') 
                            # json_msg['objects'][self.tracker.index[i]]['detection']['wait']=spend_time
                            print("spend_time in total_seconds:{}".format(spend_time.total_seconds()),flush=True)
                            # if spend_time.total_seconds()<self.thr_spend_time_min:
                            #     self.queue[j].people_count=self.queue[j].people_count-1
                            #     self.queue[j].entry.remove(i)
                            #     self.queue[j].exit.remove(i)
                            print("spend_time",flush=True) 
                            print(spend_time,flush=True) 
                except Exception as error:
                    print("new entry:{}".format(error),flush=True)
                        
                   
                    

        try:
            for j in range(len(self.queue)):
                # self.total_count[j]=self.queue[j].people_count
                self.entry_count[j]=len(self.queue[j].entry)
                self.exit_count[j]=len(self.queue[j].exit)
                self.total_count[j]=len(self.queue[j].entry)-len(self.queue[j].exit)

                if self.queue[j].people_count>self.queue[j].min_people and self.queue[j].people_count<=self.queue[j].max_people:
                    if self.queue[j].people_count>self.queue[j].pre_max:
                        json_msg["notification"]="yes_pre"
                    if self.queue[j].flag==False:
                        self.queue[j].end_time=datetime.datetime.now().time().strftime('%H:%M:%S')
                        wait_time=datetime.datetime.strptime(self.queue[j].end_time,'%H:%M:%S') - datetime.datetime.strptime(self.queue[j].start_time,'%H:%M:%S') 
                        print("wait_time123332",flush=True)
                        print(wait_time,flush=True)
                        json_msg["notification"]="yes_exit"
                        json_msg["wait_time"]=str(wait_time)
                        json_msg["time_end"]=self.queue[j].end_time
                        self.queue[j].flag=True

                if self.queue[j].people_count>self.queue[j].max_people:
                    
                    if self.queue[j].flag==False:
                        wait_time=datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'),'%H:%M:%S') - datetime.datetime.strptime(self.queue[j].start_time,'%H:%M:%S') 
                        # json_msg["wait_time"]=str(wait_time)
                        if wait_time.seconds>self.queue[j].renotification_time:
                            json_msg["notification"]="yes_entry"
                            
                    if self.queue[j].flag==True:
                        json_msg["notification"]="yes_entry"
                        self.queue[j].start_time=datetime.datetime.now().time().strftime('%H:%M:%S')
                        json_msg["time_start"]=self.queue[j].start_time
                        self.queue[j].flag=False
                    print("Send alert or whatsapp message",flush=True)
        except Exception as error:
            print("error in:{}".format(error),flush=True)

        json_msg["queue_count"]=self.total_count
        json_msg["camera"]=self.camera_id
        json_msg["roi"]=self.roi_line
        json_msg["exit_count"]=self.exit_count
        json_msg["entry_count"]=self.entry_count 
        if len(messages)>0:           
            frame.remove_message(messages[0])
            try:
                for i in range(len(self.identities)): 
                    for j in range(len(self.detected_centers)):
                        if j==self.identities[i]["index"]:
                            self.dic[j]['detection']['id']=self.identities[i]["id"]
                json_msg["objects"]=self.dic
            except Exception as error:
                print("error  in mapping id:{}".format(error),flush=True)

        frame.add_message(json.dumps(json_msg))
        print(json_msg,flush=True)
                            
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

    def process_frame(self,frame):
        messages=list(frame.messages())
        e = datetime.datetime.now()
        date='{}/{}/{}'.format(e.day ,e.month, e.year)
        time='{}:{}:{}'.format(e.hour, e.minute, e.second)
        if len(messages)>0:
            json_msg = json.loads(messages[0])
            print("screen",flush=True)
        try:
            for region in frame.regions():
                print("capture",flush=True)
                self.timestamp=json_msg['timestamp']
                for tensor in region.tensors():
                    print(tensor.has_field('format'),flush=True)
                    if tensor.has_field('format'):
                        print(tensor['format'],flush=True)
                        if tensor['format'] == "cosine_distance":
                            print(json_msg['notification'],flush=True)
                            buffer = frame._VideoFrame__buffer
                            if json_msg['notification']=="yes_entry":
                                text="Queue exceed from its limit"
                            if json_msg['notification']=="yes_exit":
                                text="Queue come under its limit"
                            if json_msg['notification']=="yes_entry" or json_msg['notification']=="yes_exit":
                                buffer = frame._VideoFrame__buffer    
                                with gst_buffer_data(buffer, Gst.MapFlags.READ) as data:
                                    path1=os.getcwd()
                                    print(path1,flush=True)
                                    self.timestamp=json_msg['timestamp']
                                    path2=os.path.join(path1,"screenshot","img_"+str(self.timestamp))
                                    print(path2,flush=True)
                                    pathi="{}.jpeg".format(path2)
                                    print(pathi,flush=True)
                                    # os.makedirs(os.path.dirname(pathi), exist_ok=True)
                                    # with open(pathi,"wb",0) as output:
                                    #     print("write",flush=True)
                                    #     output.write(data)

                                json_msg1={"mqttEventName": "NOTIFICATION",
                                "eventName": "AGGRESIVEBEHAVIOR",
                                "notificationType": "TEXT",
                                "eventCode": "EVN001",
                                "eventId": "d62a7842-2053-4e1b-9ba9-a1dca1ca8f5d",
                                "textMessage": text,
                                "cameraID": 1,
                                "roiId":0,
                                "roiName": "Counter"+str(0),
                                "visionBotName": "Queue Counting",
                                "visionBotId": "1",
                                "timeStamp": time,
                                "date": date,
                                "location": "Office1",
                                "locationId": "1",
                                "orgId": "1",
                                "imagePath":"",
                                "videoPath":"",
                                "visualisations": "none",
                                "analytics": "none"
                                }
                                print("update",flush=True)
                                notification(self.broker,self.port,json_msg1)
        except Exception as error:
            print("Error processing frame: {}".format(error))
            
        return True
