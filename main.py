# Frederic Rocha
# January 2018
# Zafir Inc
# Overview
"""
INIT
    connect WiFi
    connect mqtt Server
    connect CAN
    manage local time
    start ftp server
LOOP
    receive CAN Message
    send data on MQTTserver
    save data on memory card
    send CAN frame
 ON EVENT
    receive MQTT data

"""

import sys
import uos
import os
import pycom
import time
import utime
from network import WLAN
import uos
import machine
from mqtt import MQTTClient
from array import array


#Definition of global variables
#__Command Variables
HvacOnOff = 1
SetPoint = 23
BlowerSpeedReq = 0
pin16 = 1  #to control pin 16 to turn on a demo LED
#__Status Variables
CabinTemp = 25
EvapTemp = 5
OutsideTemp = 0
BlowerSpeedSts = 0
WaterVSts = 0
Clutch = 0
Error = 0
#__Other
ipaddress = '0.0.0.0'

class FrameObj:
    p  = 0      #pointer in the table
    data=[]     #temporary table
    frame=[]    #frame detected
    id = 0
    noider = 0  #counter to detect if id is present or not

    def __init__(self,idx):
        self.p = 0
        self.id = idx
        self.data=[0,0,0,0,0,0,0,0]

    def printinfo(self):
        print('# frame                ', self.data)
        print('# frame                ', self.id)
        print('# pointer              ', self.p)
        print('# current buffer length',len(self.data))

    def filter(self,buffer):
        self.pb=0
        b=0
        self.frame = [] #empty previous frame

        if buffer != '':  #do not execute if buffer is empty

            for b in buffer:
                #print('#_',b)
                if self.p == 0:  # searching begining of the frame/synchronisation
                    if b == self.id:
                        self.data[self.p]=b
                        self.p+=1
                    else:
                        self.noider +=1
                        if self.noider > 700:
                            print('!! ID has not been found in the last 700 bytes')
                            self.noider = 0  #reinitialize counter
                        #print('>> synchronizing')
                elif self.p < 7:
                    self.data[self.p]=b
                    self.p+=1
                elif self.p == 7:
                    self.data[self.p]=b  # last element of the frame
                    self.p=0    # reinit the pointer
                    # should calculate checksum to validate the frame!
                    self.frame = self.data
                    #print('>> Frame Recognized',self.data)
                    self.noider = 0  #reinitialize counter
                else:
                    print('!! nothing') # should never enter here

        return self.frame

def convertSP(x):
    # converts a temperature setpoint value in degre C into the corresponding index matching the CAN definition
    # input: temperature range  from 15.5 to 32
    # output: index value from 0 to 30

    x=min(x,32)             # Make sure it is not above setpoint range
    x=max(x,15.5)             # Limit to the lowest value
    index = 1.8*x-28        # calculate index
    index=int(round(index,0))    #ROUND INDEX
    return index

def TimeFormat(time=0):
    mytuple = utime.localtime(time)
    string = ''
    string += str(mytuple[3])+'h_'
    string += str(mytuple[4])+'m_'
    string += str(mytuple[5])+'s'
    return string

def ManageTime():
    from machine import RTC
    global rtc
    rtc=RTC()
    #initialize the time
    print('>> initialize real time clock')
    try:
        rtc.ntp_sync("pool.ntp.org")
        mytuple = rtc.now()
        print(mytuple)
    except:
        rtc.init((2018, 1, 1, 0, 0, 0, 0, 0))
        mytuple = rtc.now()
        print(mytuple)

    string = ''
    string += str(mytuple[0])+'Y_'
    string += str(mytuple[1])+'M_'
    string += str(mytuple[2])+'D_'
    string += str(mytuple[3])+'h_'
    string += str(mytuple[4])+'m_'
    string += str(mytuple[5])+'s'
    print(string)

def LEDblink(btype = 'red'):
    # 0 = Red, 1 = Yelloe, Other = blue
    # Yellow = receive serial message from ATC
    # Blue   = receive message from MQTT server
    # Red    = Issue appeared
    #To blink the LED when a message is received or sent
    pycom.heartbeat(False)

    if btype == 'red': # for received message
        #print('Red')
        pycom.rgbled(0x1f0000)  #Red LED
        time.sleep(0.1)
        pycom.rgbled(0x000000)  #LED OFF
        time.sleep(0.1)
        pycom.rgbled(0x1f0000)  #Red LED
        time.sleep(0.1)
        pycom.rgbled(0x000000)  #LED OFF
    elif btype == 'yellow':
        #print('yellow')
        pycom.rgbled(0x1f1f00)  #Yellow LED
        time.sleep(0.1)
        pycom.rgbled(0x000000)  #LED OFF
        time.sleep(0.1)
        pycom.rgbled(0x1f1f00)  #Yellow LED
        time.sleep(0.1)
        pycom.rgbled(0x000000)  #LED OFF
    else:
        #print('blue')
        pycom.rgbled(0x00001f)  #Blue LED
        time.sleep(0.1)
        pycom.rgbled(0x000000)  #LED OFF
        time.sleep(0.1)
        pycom.rgbled(0x00001f)  #Blue LED
        time.sleep(0.1)
        pycom.rgbled(0x000000)  #LED OFF

def LEDthread():
        # To manage LED blinking separatly
        print('rien')

def SDcard(data='nodata'):
    from machine import SD
    import uos

    sd = SD()
    try:
        os.mount(sd, '/sd')
    except:
        print('?????? Impossible to mount SD card or card already mounted')

    #    check the content
    uos.chdir('/sd')
    dira = os.listdir()
    for x in dira:
        print('__',x)

    # try some standard file operations
    f = open('/sd/test.txt', 'r')
    if (f.read(4)) != 'file':  #Need to initialize the file
        f.close()
        f = open('/sd/test.txt', 'w')
        f.write('file created on March 2018 on Pycom device X01\n')
        f.write('Time SetPoint CabTemp EvapTemp BlowerSpeed\n')

    f.close()
    f = open('/sd/test.txt', 'a')        # ready to append Data
    f.write(data)
    f.close()

    f = open('/sd/test.txt', 'r')
    info = uos.stat("test.txt")
    filesize = info[6]
    print('filesize= ',filesize)

    print(f.readall())
    f.close()

def ConnectWifi():
    global ipaddress
    print('######### Connection to Wifi ###########\n')
    #The WLAN network class always boots in WLAN.AP mode;
    #to connect it to an existing network, the WiFi class must be configured as a station:
    wlan = WLAN(mode=WLAN.STA)
    #scan and print all available wifi

    wifi={'2298NET':'malabarus', 'Bergstrom Guest':'NumeraCY*9'}

    #for bergstrom guest It will be automatically connected because it MAC is registered

    if wlan.isconnected():
        print(">>>> Already connected")
        print(">>>> Connected to :",wlan.ssid())
        ipaddress = wlan.ifconfig()[0]
        print(">>>> IP Address is: ",ipaddress,'\n')

    else:
        nets = wlan.scan()
        found=False
        for net in nets:
            print(net.ssid)
            if net.ssid in wifi:
                print('>>>> Network found!')
                found=True
                mdp = wifi[net.ssid]
                wlan.connect(net.ssid, auth=(net.sec, mdp), timeout=5000)
                while not wlan.isconnected():
                    #machine.idle() # save power while waiting
                    print('getting connected')
                    time.sleep_ms(200)
                print('>>>> WLAN connection succeeded!')
                print(wlan.ifconfig())
                ipaddress = wlan.ifconfig()[0]
                break
        if found==False:
            print('!!!! Wifi Network Not Found !!')

def DataAcq():
    print("#########  Data acquisition  ##########")

    data=[]
    #from pysense import pysense
    tp = SI7006A20(pysense = None, sda = 'P22', scl = 'P21')
    x=tp.humidity()
    data.append(x)
    x=tp.temperature()
    data.append(x)

    #need to do separatly because they are using the same spi and seems there is no distinction adress on the bus
    PRESSURE = const(1)
    pat = MPL3115A2(pysense = None, sda = 'P22', scl = 'P21', mode= PRESSURE)
    x=pat.pressure()
    data.append(x)
    x=pat.temperature()
    data.append(x)

    print("humidity=",data[0], "   Temperature=", data[1], "  Pressure=",data[2], "   Temperature2=", data[3])

    return data

def ftpServer():
    # to allow FTP and Telnet server
    import network
    global server
    server = network.Server()
    server.deinit() # disable the server
    # enable the server again with new settings
    server.init(login=('pycom', 'password'), timeout=600)
    # same credentials for telnet and ftp
    print(server.isrunning()) # check whether the server is running or not

def ConnectMQTT():
    global client
    try:
        client = MQTTClient("frocha", "m11.cloudmqtt.com",user="kyfylcvw", password="X-vhsAL9DNBD", port=17334)
        client.set_callback(CallbackMQTT)
        resp = client.connect()
        print('Connect result = :',resp)
        client.subscribe(topic="OnOff",qos=0)
        client.subscribe(topic="setpoint",qos=0)
        client.subscribe(topic="blowerspeedreq",qos=0)
        client.subscribe(topic="led",qos=0)
    except:
        print('?????? MQTT connection failed')

def CallbackMQTT(topic, msg):
    global HvacOnOff
    global SetPoint
    global BlowerSpeedReq
    global pin16

    print('>> MQTT Message received topic= ',topic,'value= ',msg)
    #print(topic,type(topic))
    topic1=str(topic)
    # to clarify the formating of the topic variables
    # it contains '' at the beginning and the end
    if 'OnOff' in topic1:
        HvacOnOff = min( int(msg), 1)
        print('>> MQTT: OnOff= ',            HvacOnOff)
    if 'setpoint'  in topic1:
        SetPoint = int(msg)
        print(">> MQTT: Setpoint= ",         SetPoint)
    if 'blowerspeedreq' in topic1:
        BlowerSpeedReq = min(int(msg),10)
        print(">> MQTT: blowerspeedreq= ",   BlowerSpeedReq)
    if 'led' in topic1:
        pin16 = min(int(msg)*1,1)
        print(">> MQTT: led= ",              pin16)
    LEDblink('blue')

def PublishMQTT(data):
    # Data = [CabTemp,EvapTemp,OutsideTemp, BlowerSpeedSts, watervalvests,error]
    global client
    global ipaddress
    try:
        print(">> Publishing data at "+TimeFormat( time.time() ))
        client.publish(topic="log",         msg="Sent by HVAC at "+ TimeFormat( time.time() )+" "+ipaddress)
        client.publish(topic="CabTemp",     msg=str(data[0]))
        client.publish(topic="EvapTemp",    msg=str(data[1]))
        client.publish(topic="AmbTemp",     msg=str(data[2]))
        client.publish(topic="blowerspeed", msg=str(data[3]))
        client.publish(topic="watervalve",  msg=str(data[4]))
        client.publish(topic="error",       msg=    data[5] )  # already a string
        client.publish(topic="clutch",      msg=str(data[6]))
    except:
        print('!! Cannot publish on MQTT')

def DemoCAN():
    print("#########  demo CAN   ##########")
    from machine import CAN
    can = CAN(mode=CAN.NORMAL, baudrate=250000, pins=('P20', 'P19'))
    #                                           pins=('RX', 'TX')
    print(can)
    #can.init(mode=CAN.NORMAL, baudrate=250000, frame_format=CAN.FORMAT_STD, rx_queue_len=128, pins=('P22', 'P23'))
    # CAN.NORMAL or CAN.SILENT
    # CAN.FORMAT_STD or CAN.FORMAT_EXT or CAN.FORMAT_BOTH

    while True:
        print('start')
        a=can.send(id=12, data=bytes([1, 2, 3, 4, 5, 6, 7, 8]))
        print(a)
        #can.deinit()
        #can.init(mode=CAN.NORMAL, baudrate=250000,frame_format=CAN.FORMAT_STD, rx_queue_len=128, pins=('P20', 'P19'))
        time.sleep(1)
        #mess_in=can.recv()
        #print(mess_in)
        print(TimeFormat( time.time()) )
        #LEDblink(0)

def CANframe( On_Off=1,  Temp_Control=0, Temp_Setting_C=20, Blower_Setting=0, AC=1, Configuration=1):
    # 0 = OFF / 1 = ON
    Byte0 = int(On_Off)
    # Bit 0-1: 0=Manual / 1= acquisition
    # Bit 2-7: [0-30] temperature setting index with 0=60F..30=90F
    idx = min(max(int((Temp_Setting_C*9/5+32)-60),0),30) # limi the range to 0..30
    print('Farenheit ',idx )
    Byte1 = int( Temp_Control + idx*4 )
    # Byte2
    Byte2 = int( Blower_Setting * 16)
    Byte3 = int( AC )
    Byte4 = 0
    Byte5 = int( Configuration )
    Byte6 = 0
    Byte7 = 0
    Data = [Byte0, Byte1, Byte2, Byte3, Byte4, Byte5, Byte6, Byte7]
    print (Data[1]/4)
    return Data

def ConnectSerial():
    from machine import UART
    global uart
    try:
        uart = UART(1, 1200,pins=('P10','P11'),parity=None, stop=1)   # init with given baudrate
        #                          TXD and RXD (``P20`` and ``P21``)
        #uart.init(9600, bits=8, parity=None, stop=1) # init with given parameters
    except:
        print('?????? Cannot connect to UART')

def SendSerial(Frame):
    # Frame is a table
    i=0
    #print(Frame)
    #print(i,'_',str(chr(Frame[i])))
    #uart.write((chr(Frame[i])))   # write characters
    uart.write(bytes(Frame))
    # chr transforms a decimal code into a string based on ascii table

def CommandFrame(OnOff=0, sp=0, BlowerSpeed=0,io=0):
    #Frame format compatible with the AGCO control head see ES11333

    Byte0 = 0xEE # Frame ID 0xEE = 238 dec
    Byte1 = 0x00 # SW version number int( Temp_Control + Temp_Setting*4 )
    Byte2 = io # to control the output of the condenser fan, will control a LED
    Byte3 = min(OnOff,1) # OnOff signal should toggle and bit1=1 to activate AC
    Byte4 = min(BlowerSpeedReq*3,30) # Blower speed knob position index
    Byte5 = min(convertSP(sp),30)
    Byte6 = 0x00
    Byte7 = int(0xFF&(Byte0+Byte1+Byte2+Byte3+Byte4+Byte5+Byte6))  # Check sum

    #Data = [0x81,0x18,0x24,0x42,0x81,0x99,0xA5,0xFF]
    #Data = [0x55,0x77,0x88,0xEE,0x05,0x06,0x07,0x08]
    Data = [Byte0, Byte1, Byte2, Byte3, Byte4, Byte5, Byte6, Byte7]
    print('>> cmd= ', Data)
    return Data

def ReceiveSerial():
    global uart
    buffer = ''
    try:
        buffersize = uart.any() # print if any character to read
        if buffersize > 0:
            buffer = uart.readall()
            #print('>>>> reading UART buffer',buffer)
            LEDblink('yellow')
    except:
        print('!! No UART available')
    return buffer

def DecodeError(code=0):
    err="NO Error"
    ErrorTable = {
    0:"NO error",
    1:"High Pressure",
    2:"Low Pressure",
    8:"Evaporator Sensor",
    9:"Outlet Sensor",
    10:"Ambient Sensor"
    }
    if code in ErrorTable:
        err = ErrorTable[code]
    else:
        err = 'Unknown Error'
    return err

def DecodeD0(frame):
    # Decode Frame as a table
    # will update directly global variable
    global CabinTemp
    global EvapTemp
    global OutsideTemp
    global BlowerSpeedSts
    global Error
    global Clutch
    # Define error table as a dictionary

    if len(frame)>0:
        if frame[0] == 0xD0:
            OutsideTemp = (int(frame[5])-32)*5/9
            Error       = int(frame[6])
            Clutch      = int(frame[2]) & 0x01

def DecodeDF(frame):
    # Decode Frame as a table
    # will update directly global variable
    global CabinTemp
    global EvapTemp
    global BlowerSpeedSts
    global WaterVSts
    if len(frame)>0:
        if frame[0] == 0xDF:
            CabinTemp       = (int(frame[1])-32)*5/9
            EvapTemp        = (int(frame[2])-32)*5/9
            # Outlet Temp   = frame[3]
            BlowerSpeedSts  = 100* (int(frame[4])) /255
            WaterVSts       = 100* (int(frame[5])) /255

print('\n')
print('###############################################\n')
print('system version:',sys.version)
print('micropython version:',sys.implementation)
print('module firmware version:\n',uos.uname())
print('working directory: ',os.getcwd())
print('directory content\n',os.listdir())

# MAIN APPLICATION

# Blink led to show startup
LEDblink('red')
# INITIALIZTION
ConnectWifi()
#Connection to MQTT server
client = None
ConnectMQTT()
#manage local time
rtc=None
ManageTime()  # get time from server
#connect CAN/serial
uart=None
ConnectSerial()
#create frame object for reception
frameD0 = FrameObj(0xD0)
frameDF = FrameObj(0xDF)
# Start ftp server for remote management
server = None
ftpServer()


loopcount=0
# MAIN LOOP
while True:
    loopcount+=1
    print('>> LOOP #', loopcount)
    #receive CAN/Serial Message
    b = ReceiveSerial()
    # Decode received frame
    fd0 = frameD0.filter(b)
    DecodeD0(fd0)
    print('>> Received frame',fd0)

    fdf=frameDF.filter(b)
    DecodeDF(frameDF.filter(b))
    print('>> Received frame',fdf)

    #Publish data to the MQTT server
    Data = [CabinTemp, EvapTemp , OutsideTemp, BlowerSpeedSts, WaterVSts,DecodeError(Error),Clutch]
    print('>> Data=', Data)
    PublishMQTT(Data)
    #save data on memory card

    #receive MQTT command
    client.check_msg()

    #send CAN/serial frame
    if pin16 == 1:  # will toggle led signal
        pin16 =0
    else:
        pin16 = 1
    SendSerial(CommandFrame(HvacOnOff,SetPoint,BlowerSpeedReq,pin16))

    if loopcount%10 == 0 :LEDblink('green')  #blink every 10 loops
    time.sleep(1.5)
