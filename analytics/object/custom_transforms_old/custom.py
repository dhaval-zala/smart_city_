try:
    import gstgva  
    from gstgva import VideoFrame, util
    from gstgva.util import libgst, gst_buffer_data
    from gi.repository import Gst, GObject
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    import cv2
    from argparse import ArgumentParser
    # import numpy as np
    import json
    import os
    from gstgva.util import libgst, gst_buffer_data
    import numpy
    import sys
    import gi
    gi.require_version('GObject', '2.0')
    gi.require_version('Gst', '1.0')
    gi.require_version('GstApp', '1.0')
    gi.require_version('GstVideo', '1.0')
    from gi.repository import Gst, GLib, GstApp, GstVideo

    # import logging
    # import datetime
    # from notification import notification
    # from configuration import env
    # from centroid_tracker import CentroidTracker
    # from memory_profiler import profile
    # from shapely.geometry import Point, Polygon
except Exception as e:
    print("module problem:{}".format(e),flush=True)
Gst.init(sys.argv)
parser = ArgumentParser(add_help=False)

args = parser.parse_args()
class Trial:

    def __init__(self):
        self.nan = None

    def process_frame(self, frame):
        # mat = frame.data()
        # for roi in frame.regions():
            # try:
            #     cv2.putText(mat, 'label', (10, 100 + 10 + 30),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 5)
            # except:
            #     print("No________________________________________",flush=True)
        try:
            messages = list(frame.messages())
            if len(messages)>0:
                json_msg = json.loads(messages[0])
                add = "Nothing"
                json_msg['add'] = "Nothing"
                frame.remove_message(messages[0])
                frame.add_message(json.dumps(json_msg))
                print("message_______",frame.messages())
                messages = list(frame.messages())
                print("messages[0]_____",messages[0])
        except:
            print("No messages________")
        try:
            detections = [x for x in frame.regions()]
            print("Detections____",detections)
        except:
            print('No Detection')
            
    def write_image(self,buffer):
        print("enter write image",flush=True)
        with gst_buffer_data(buffer, Gst.MapFlags.READ) as data:
            print("data.shape_____________",data.shape,flush=True)
    
    def last(self):
        try:
            detections = [x for x in frame.regions()]
            for i in detections:
                buffer = frame._VideoFrame__buffer
                self.write_image(buffer)
        except:
            print("not possible______________", flush=True)

            # path1=os.getcwd()
            # print(path1,flush=True)
            # self.timestamp=json_msg['timestamp']
            # path2=os.path.join(path1,"screenshot","img_"+str(self.timestamp))
            # print(path2,flush=True)
            # pathi="{}.jpeg".format(path2)
            # print(pathi,flush=True)
            # os.makedirs(os.path.dirname(pathi), exist_ok=True)
            # with open(pathi,"wb",0) as output:
            #     print("write",flush=True)
            #     output.write(data)

    # def process_frame(frame: VideoFrame) -> bool:
    #     with frame.data() as mat:
    #         print(type(mat)) # should be numpy array
    #     return True

# def create_launch_string():
#     if "/dev/video" in args.input:
#         source = "v4l2src device"
#     elif "://" in args.input:
#         source = "urisourcebin buffer-size=4096 uri"
#     else:
#         source = "filesrc location"

#     return "{}={} ! decodebin ! \
#     videoconvert n-threads=4 ! capsfilter caps=\"video/x-raw,format=BGRx\" ! \
#     gvadetect model={} device=CPU batch-size=1 ! queue ! \
#     gvaclassify model={} device=CPU batch-size=1 ! queue ! \
#     gvaclassify model={} device=CPU batch-size=1 ! queue ! \
#     gvaclassify model={} batch-size=1 ! queue ! \
#     gvawatermark name=gvawatermark ! videoconvert n-threads=4 ! \
#     fpsdisplaysink video-sink=xvimagesink sync=false".format(source, args.input, args.detection_model,
#                                                              args.classification_model1, args.classification_model2,
#                                                              args.classification_model3)

# def pad_probe_callback(pad, info):
#     with util.GST_PAD_PROBE_INFO_BUFFER(info) as buffer:
#         caps = pad.get_current_caps()
#         frame = VideoFrame(buffer, caps=caps)
#         with frame.data() as mat:
#             print(type(mat)) # mat is numpy array that can handle by cv2
#     return Gst.PadProbeReturn.OK

# def process_frame(frame):
#     Gst.init(sys.argv)
#     args = parser.parse_args()
#     gst_launch_string = create_launch_string()
#     print(gst_launch_string)
#     pipeline = Gst.parse_launch(gst_launch_string)

   

#     pipeline.set_state(Gst.State.PLAYING)



#     print("Exiting")

#     gvawatermark = pipeline.get_by_name("gvawatermark")
#     pad = gvawatermark.get_static_pad("src")
#     pad.add_probe(Gst.PadProbeType.BUFFER, pad_probe_callback)

#     return None