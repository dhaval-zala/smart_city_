import json
import paho.mqtt.client as paho

# f=open('/home/custom_transforms/config.json')
# data=json.load(f)
# msg_data=data["VisionBot"]["json_msg"]

def on_publish(client,userdata,result):  #create function for callback
    print("data published \n",flush=True)
    pass


def notification(broker,port,msg_data):
    client1= paho.Client("control1")     #create client object
    client1.on_publish = on_publish      #assign function to callback
    client1.connect(broker,port)
    json_msg=json.dumps(msg_data)
    ret= client1.publish("notification",json_msg)
    pass
