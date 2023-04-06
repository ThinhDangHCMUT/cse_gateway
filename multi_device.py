import serial.tools.list_ports
import paho.mqtt.client as mqttclient
import time
import json
import random

BROKER_ADDRESS = "demo.thingsboard.io"
PORT = 1883
THINGS_BOARD_ACCESS_TOKEN = ["FAekS7wwfaypuQjI6wzQ", "XyWXw29GpXfinUZraksa"]

# topic = "v1/devices/me/rpc/response/+"

def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed...")

autoMode = 0
count = 0 
def recv_message(client, userdata, message):
    print("Device received: ", json.loads(message.payload)['shared']['id'])
    print("Data Received: ", json.loads(message.payload)['shared'])
    cmd = 0
    try:
        jsonobj = json.loads(message.payload)['shared']
        if jsonobj['method'] == "autoMode" and jsonobj['params'] == "active":
            autoMode = 1
        if jsonobj['method'] == "autoMode" and jsonobj['params'] == "inactive":
            autoMode = 0
        if jsonobj['method'] == "setAll" and jsonobj['params'] == "On":
            cmd = 'a'
        if jsonobj['method'] == "setAll" and jsonobj['params'] == "Off":
            cmd = 'b'
        if jsonobj['method'] == "setFan_1" and jsonobj['params'] == "On":
            cmd = 0
        if jsonobj['method'] == "setFan_1" and jsonobj['params'] == "Off":
            cmd = 1 
        if jsonobj['method'] == "setFan_2" and jsonobj['params'] == "On":
            cmd = 2
        if jsonobj['method'] == "setFan_2" and jsonobj['params'] == "Off":
            cmd = 3
       
    except:
        pass
    if isMicrobitConnected:
         ser.write((str(cmd)).encode())


def connected(client, usedata, flags, rc):
    if rc == 0:
        print("Thingsboard connected successfully!!")
        # client.subscribe("v1/devices/me/rpc/request/+")
        client.subscribe("v1/devices/me/rpc/response/1")
        # client.subscribe()
    else:
        print("Connection is failed")

clients = []
for access_token in THINGS_BOARD_ACCESS_TOKEN:
    client = mqttclient.Client("Gateway_Thingsboard")
    client.username_pw_set(access_token)
    clients.append(client)

for client in clients:     
    client.on_connect = connected
    client.connect(BROKER_ADDRESS, 1883)
    client.loop_start()
    client.on_subscribe = subscribed
    client.on_message = recv_message


def getPort():
    ports = serial.tools.list_ports.comports()
    print(ports)
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
        port = ports[i]
        strPort = str(port)
        print(strPort)
        if "USB-SERIAL CH340" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
            print(commPort)
    return commPort


isMicrobitConnected = False
if getPort() != "None":
    ser = serial.Serial( port=getPort(), baudrate=115200)
    isMicrobitConnected = True

# mess = ""
entry_dict = {
    "temperature": "",
    "humidity": "",
}
methodSensor = {
    "method": "SetAll",
    "params": "Off"
}


def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    print(splitData)
    entry_dict["temperature"] = splitData[0]
    entry_dict["humidity"] = splitData[1]
    print(type(entry_dict["humidity"]))
    print(json.dumps(entry_dict))
    # Automatic in gateway
    client.publish("v1/devices/me/telemetry", json.dumps(entry_dict))
    if autoMode == 1:
        if  float(entry_dict["humidity"]) < 60:
            methodSensor["method"] = "setFan"
            methodSensor["params"] = "On"
        if  float(entry_dict["humidity"]) > 80:
            methodSensor["method"] = "setFan"
            methodSensor["params"] = "Off"
        if  float(entry_dict["temperature"]) > 30:
            methodSensor["method"] = "setAir"
            methodSensor["params"] = "On"
        if  float(entry_dict["temperature"]) < 20:
            methodSensor["method"] = "setAir"
            methodSensor["params"] = "Off"
   

mess = ""
def readSerial():
    print("hello")
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]

while True:
    if isMicrobitConnected:
        print("Yolobit access is accepted!")
        readSerial()

    for client in clients:
        print(autoMode)
        if(autoMode == 1):
            client.publish("v1/devices/me/attributes/1", json.dumps(methodSensor))
        client.publish('v1/devices/me/attributes/request/1', '{"sharedKeys":"method,params,id"}')
    time.sleep(5)