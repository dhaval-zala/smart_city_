try:
    import gstgva  
    # from gstgva.util import libgst, gst_buffer_data
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    # import numpy as np
    import json
    import os
    from gstgva.util import libgst, gst_buffer_data
    import numpy
    # import sys

    # import logging
    # import datetime
    # from notification import notification
    # from configuration import env
    # from centroid_tracker import CentroidTracker
    # from memory_profiler import profile
    # from shapely.geometry import Point, Polygon
except Exception as e:
    print("module problem:{}".format(e),flush=True)

# print("_______________Yes___________________", flush = True)

class Trial:

    def __init__(self):
        self.nan = None

    def process_frame(self, frame):
        try:
            messages = list(frame.messages())
            print("Messages:________",messages, flush=True)
            json_msg = json.loads(messages[0])
            print("frmae:_________",frame, flush=True)
            try:
                print("_data_____", frame.data().shape, flush=True)
                # print("_VideoFrame__get_label_by_label_id_____fn", dir(frame._VideoFrame__get_label_by_label_id), flush=True)
            except:
                print("not there", flush=True)
            try:
                print("dddtttaaa___________",frame.data(flag = Gst.MapFlags.WRITE), flush=True)
            except:
                print("nooodttaa")
            try:   
                for x in frame.regions():
                    # for a in x.tensor():
                    #     print(numpy.array(a), flush=True)
                    #     break
                    print("Tensor____",numpy.array(x.tensors()))
                    print("Tensor____",numpy.array(x.tensors()).shape)
                    break
            except:
                print('No tensor')
            try:
                print("Len:_",len(detections))
                print("detections____________",detections[0].region_of_interest.RegionOfInterest(), flush=True)
            except:
                print("no", flush=True)
            # print("json_msg__________: ",json_msg)
            try:
                with gst_buffer_data(frame._VideoFrame__buffer, Gst.MapFlags.READ) as data:
                    arr = numpy.array(data)
                    # numpy.set_printoptions(threshold=sys.maxsize)
                    print("Buffer____",arr[:20], flush=True)
                    print("Buffer____",numpy.array(data).shape, flush=True)
                    print("Buffer____",len(numpy.array(data)), flush=True)
            except:
                print("No buffer")
        except Exception as error:
            print('range____',error, flush=True)
        
        return True

