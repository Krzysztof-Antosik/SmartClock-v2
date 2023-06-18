
from machine import RTC, Pin, SPI, I2C, Timer, ADC, reset, freq
from time import time, sleep
from ntptime import settime
from re import search
from pages import *
from ahtx0 import AHT10
import network, random, _thread, micropydatabase, max7219

try:
    import usocket as socket
except:
    import socket
  
freq(240000000)

#Initialize timer
timer0 = Timer(0)

#initialize I2C
i2c = I2C(1, scl = Pin(22), sda = Pin(21), freq = 400000)

#initialize sensor
sensor_aht10 = AHT10(i2c)

#initialize SPI
spi = SPI(1, baudrate=10000000, polarity=0, phase=0)

#initialize matrix led 
display = max7219.Matrix8x8(spi, Pin(23), 8)

def print_d(str, x = 0):
    global display
    display.fill(0)
    display.text(str , x, 0, 1)
    display.show()

def scrollText(str):
    global display
    scrolling_message = str
    length = len(scrolling_message)
    column = (length * 8) - 32
    for x in range(32, -column, -1):
        print_d(scrolling_message, x)
        sleep(0.01)

scrollText("SmartClock V2")

#Init ADC
photoresistor = ADC(Pin(36))
photoresistor.atten(ADC.ATTN_11DB) #Full range: 3.3v
  
#Init Database
database = micropydatabase.Database.open("database")

t_settings = database.open_table("settings")
t_strings = database.open_table("strings")
t_time = database.open_table("time")

settings = t_settings.find({"all": 1})

#Init access point
ap = network.WLAN(network.AP_IF)
ap.active(True)

ap_ssid = settings["ap_ssid"]
ap_pw = settings["ap_pw"]
ap_hostname = "settings"
ap.config(essid=ap_ssid, dhcp_hostname = ap_hostname)

if len(ap_pw) > 0:
    ap.config(password=ap_pw, authmode=network.AUTH_WPA_WPA2_PSK) 
else:
    ap.config(authmode=network.AUTH_OPEN)
    
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80)) 
s.listen(5)

print("Access point ready")
print("Access point IP is: ", ap.ifconfig()[2])

#Init wifi
sta = network.WLAN(network.STA_IF)
sta.active(True)
    
def disconnect():
    global sta
    sta.disconnect()
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
def connect():
    global sta, t_settings
    settings = t_settings.find({"all": 1})
    sta_ssid = settings["sta_ssid"]
    sta_pw = settings["sta_pw"]
    
    try:
        if not sta.isconnected():
            
            #scrollText("Connecting to network: {}".format(sta_ssid))
            sta.active(True)
            sta.connect(sta_ssid, sta_pw)

            for i in reversed(range(1,11)):
                
                #print_d("Conn: {}".format(i))
                
                if sta.isconnected():
                    break
                sleep(1)
                
            if sta.isconnected():
                #print_d("Success")
                sleep(0.5)
                print("Network IP is: ", sta.ifconfig()[2])
                
                syncTime()
                return True
            
            else:
                print_d, ("Failed")
                sleep(0.5)
                print("Coneccting failed")
                disconnect()
                return False
        else:
            print("Device is arledy connected")
        
    except OSError as e:
        print("Error C: ", e)
        disconnect()

_thread.start_new_thread(connect, ())

#Init RTC
timezone = 0
rtc = RTC()

#read last time from database

def readLastDateTime():
    global rtc, t_time
    time = t_time.find({"all": 1})
    rtc.datetime((
        time["year"],
        time["mount"],
        time["day"],
        time["wday"],
        time["hour"],
        time["minute"],
        time["second"],
        time["milisecond"]
    ))

readLastDateTime()

#save actual time to database
def updateLastDateTime():
    global rtc, t_time
    time = t_time.find({"all": 1})
    t_time.update(time,
                  {"year": rtc.datetime()[0],
                   "mount": rtc.datetime()[1],
                   "day": rtc.datetime()[2],
                   "wday": rtc.datetime()[3],
                   "hour": rtc.datetime()[4],
                   "minute": rtc.datetime()[5],
                   "second": rtc.datetime()[6],
                   "milisecond": rtc.datetime()[7],
                   "all": 1})
    print("Time saved to database")

#sync time from internet
def syncTime():
    try:
        settime() #init sync
        print("Time is now actual")
    except OSError as e:
        print(e)
 
_thread.start_new_thread(syncTime, ())

specialChars = ['ą', 'ć', 'ł', 'ó', 'ś', "ś", 'ę', 'ń', 'ż', 'ź', 'Ą', 'Ć', 'Ł', 'Ó', 'Ś', 'Ę', 'Ń', 'Ż', 'Ź', '\n']
normalChars = ['a', 'c', 'l', 'o', 's', "s", 'e', 'n', 'z', 'z', 'A', 'C', 'L', 'O', 'S', 'E', 'N', 'Z', 'Z', '']

def removeAccets(str):
    for i in range(len(specialChars)):
        str = str.replace(specialChars[i], normalChars[i])
    return str

#init timer and show time
def showTime():
    global rtc, photoresistor, t_strings, timezone, settings
    
    settings = t_settings.find({"all": 1})
    
    
    
    if settings["display"] == 'on':
        
        #set display brightness
        lightLevel = photoresistor.read()
        brightness = ((lightLevel - 0) / (4095 - 0)) * (7 - 0) + 0  
        display.brightness(round(brightness))
        
        #show time
        timezone = settings["timezone"]
        print(timezone)
        hour = rtc.datetime()[4]
        minute = rtc.datetime()[5]
        second = rtc.datetime()[6]
        
        currentTime = "%02d:%02d:%02d" % (hour + timezone, minute, second)
        
        print_d(currentTime)
        
        try:
            if second == 0:
                _thread.start_new_thread(syncTime, ())
                     
                if minute % 20 == 0:
                    strings = t_strings.query({"all": 1})
                    lenStrings = len(strings)
                    randomInt = random.randint(0, lenStrings - 1)
                    randomString = strings[randomInt]["string"]
                    scrollText(removeAccets(randomString))
                    
                elif minute % 2 == 0:
                    scrollText("Temp: {} `C Hum: {}%".format(round(sensor_aht10.temperature, 2), round(sensor_aht10.relative_humidity, 2)))
                    
            elif second % 20 == 0:
                _thread.start_new_thread(connect, ())
                
            elif second % 10 == 0:
                _thread.start_new_thread(updateLastDateTime, ())
             
        except OSError as e:
            print("Error T: ", e)
    else:
        display.fill(0)
        display.show()


def startTime():
    global timer0
    timer0.init(period=1000, mode=Timer.PERIODIC, callback=lambda t:showTime())
    
startTime()  
      
def stopTime():
    global timer0
    timer0.deinit()
    
def trySend(data):
    try:
        conn.send(data)
    except OSError as e:
        print("Error R: ", e)
    
while True:
    conn, addr = s.accept()

    request = conn.recv(1024)
    request = str(request)
    
    request = (request
            .replace("\\xc4\\x99", "ę")
            .replace("\\xc3\\xb3", "ó")
            .replace("\\xc4\\x85", "ą")
            .replace("\\xc5\\x9b", "ś")
            .replace("\\xc5\\x82", "ł")
            .replace("\\xc5\\xbc", "ż")
            .replace("\\xc5\\xba", "ź")
            .replace("\\xc4\\x87", "ć")
            .replace("\\xc5\\x84", "ń")
            .replace("\\xc4\\x98", "Ę")
            .replace("\\xc3\\x93", "Ó")
            .replace("\\xc4\\x84", "Ą")
            .replace("\\xc5\\x9a", "Ś")
            .replace("\\xc5\\x81", "Ł")
            .replace("\\xc5\\xbb", "Ż")
            .replace("\\xc5\\xb9", "Ź")
            .replace("\\xc4\\x86", "Ć")
            .replace("\\xc5\\x83", "Ń"))
    
    trySend('HTTP/1.1 200 OK\n')
    trySend('Content-Type: text/html; charset=utf-8\n')
    trySend('Connection: close\n\n')
    
    stopTime()
    try:
        page = search('/([a-zA-Z]+)?', request).group(0) #check page
    except:
        page = "/"   

    if page == "/":
        trySend(headerPage())
        trySend(homePageStart())
        strings = t_strings.query({"all": 1})

        if not strings == None:
            for i in strings:
                try:
                    string = i["d"]["string"]
                    stringID = i["d"]["id"]
                except:
                    string = i["string"]
                    stringID = i["id"]
                
                part = '''<tr>
                            <td>{}</td>
                            <td>
                                <form action="/edit" method="post" accept-charset="utf-8" enctype="text/plain">
                                    <input type="hidden" value="{}" name="id"/>
                                    <button type="submit">edit</button>
                                </form>
                            </td>
                            <td>
                                <form action="/remove" method="post" accept-charset="utf-8" enctype="text/plain">
                                    <input type="hidden" value="{}" name="id"/>
                                    <button type="submit">remove</button>
                                </form>
                            </td>
                        </tr>'''.format(string, stringID, stringID)
                
                trySend(part)

        else:
            trySend('<tr><td colspan="3">database is empty</td></tr>')
        trySend(homePageEnd())
        trySend(footerPage())   
        
    elif page == "/add":
        trySend(headerPage())
        trySend(addPage())
        trySend(footerPage())
        
    elif page == "/added":
        newText = search('newText=([a-zA-ZęóąśłżźćńĘÓĄŚŁŻŹĆŃ0-9 !@#$%^&*()-=_+,.\?;\'\"\`]+)?', request).group(0).replace('newText=', '')
        trySend(headerPage())
        trySend(addedPage(newText))
        trySend(footerPage())
        
    elif page == "/edit":
        idText = search('id=([0-9]+)?', request).group(0).replace('id=', '')
        if idText:
            trySend(headerPage())
            trySend(editPage(idText))
            conn.send(footerPage())
        
    elif page == "/update":
        idText = search('id=([0-9]+)?', request).group(0).replace('id=', '')
        newText = search('newText=([a-zA-ZęóąśłżźćńĘÓĄŚŁŻŹĆŃ0-9 !@#$%^&*()-=_+,.\?;\'\"\`]+)?', request).group(0).replace('newText=', '')
        if idText and newText:
            trySend(headerPage())
            trySend(updatePage(idText, newText))
            trySend(footerPage())
            
    elif page == "/remove":
        idText = search('id=([0-9]+)?', request).group(0).replace('id=', '')
        if idText:
            trySend(headerPage())
            trySend(removePage(idText))
            trySend(footerPage())
            
    elif page == "/settings":
    
        trySend(headerPage())
        scan = sta.scan()
        trySend( '''<main>
                        <table style="width: 100%;text-align: center;"> 
                            <tbody>
                                <tr>
                                    <th>
                                        <h2>Change Settings</h2>   
                                    </th>
                                </tr>
                                <tr>
                                    <td>''')
        
        if settings['display'] == "on":
            trySend('''
                                        <a href="/displayoff">
                                            <button>Turn off</button>
                                        </a>''')
        else:
            trySend('''
                                        <a href="/displayon">
                                            <button>Turn on</button>
                                        </a>''')
        if settings['timezone'] == 1:
             trySend('''
                                        <a href="timezonetwo">
                                            <button>Switch daylight time to summer</button>
                                        </a>''')
        else:                            
            trySend('''                 <a href="timezoneone">
                                            <button>Switch daylight time to winter</button>
                                        </a>''')
        trySend('''
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <table>
                            <tbody>
                                <tr>
                                    <th>
                                        <h2>Change WiFi</h2>
                                    </th>
                                    <th>
                                        <a href="/settings">
                                            <button>refresh</button>
                                        </a>
                                    </th>
                                </tr>''')
        
        for i in scan:
            nameWiFi = i[0].decode("utf-8")
            secure = i[4]

            part = '''<tr>
                        <td>{}</td>
                        <td>
                            <form action="/password" method="post" accept-charset="utf-8" enctype="text/plain">
                                <input type="hidden" value="{}" name="ssid"/>
                                <input type="hidden" value="{}" name="secure"/>
                                <button type="submit">connect</button>
                            </form>
                        </td>
                    </tr>'''.format(nameWiFi, nameWiFi, secure)
            trySend(part)
            
        trySend('''</tbody>
            </table>
        </main>''')
        trySend(footerPage(page))
    
    elif page == "/password":
        ssid = search('ssid=([a-zA-ZęóąśłżźćńĘÓĄŚŁŻŹĆŃ0-9 !@#$%^&*()-=_+,.\?;\'\"\`]+)?', request).group(0).replace('ssid=', '')
        secure = search('secure=([0-9])?', request).group(0).replace('secure=', '')
        if ssid and secure:
            trySend(headerPage())
            trySend(passwordPage(ssid, secure))
            trySend(footerPage("/settings"))
            
    elif page == "/connect":
        ssid = search('ssid=([a-zA-ZęóąśłżźćńĘÓĄŚŁŻŹĆŃ0-9 !@#$%^&*()-=_+,.\?;\'\"\`]+)?', request).group(0).replace('ssid=', '')
        try:
            password = search('password=([a-zA-ZęóąśłżźćńĘÓĄŚŁŻŹĆŃ0-9 !@#$%^&*()-=_+,.\?;\'\"\`]+)?', request).group(0).replace('password=', '')
        except:
            password = ""
            
        settings = t_settings.find({"all": 1})

        t_settings.update(settings, {'display': settings['display'], 'sta_ssid': ssid, 'sta_pw': password, 'ap_pw': settings['ap_pw'], 'all': settings['all'], 'ap_ssid': settings['ap_ssid'], 'version': settings['version'], 'timezone': settings['timezone']})
        
        disconnect()
        status = connect()
        
        syncTime()
            
        trySend(headerPage())
        trySend(connectPage(status))
        trySend(footerPage("/settings"))
        
    elif page == "/about":
        trySend(headerPage())
        trySend(aboutPage())
        trySend(footerPage("/about"))
        
    elif page == "/displayoff":
        settings = t_settings.find({"all": 1})
        t_settings.update(settings, {'display': 'off', 'sta_ssid': settings['sta_ssid'], 'sta_pw': settings['sta_pw'], 'ap_pw': settings['ap_pw'], 'all': settings['all'], 'ap_ssid': settings['ap_ssid'], 'version': settings['version'], 'timezone': settings['timezone']})
        
        trySend(headerPage())
        trySend(displayOffPage())
        trySend(footerPage("/settings"))
        
    elif page == "/displayon":
        settings = t_settings.find({"all": 1})
        t_settings.update(settings, {'display': 'on', 'sta_ssid': settings['sta_ssid'], 'sta_pw': settings['sta_pw'], 'ap_pw': settings['ap_pw'], 'all': settings['all'], 'ap_ssid': settings['ap_ssid'], 'version': settings['version'], 'timezone': settings['timezone']})
        
        trySend(headerPage())
        trySend(displayOnPage())
        trySend(footerPage("/settings"))
        
    elif page == "/timezonetwo":
        settings = t_settings.find({"all": 1})
        t_settings.update(settings, {'display': settings['display'], 'sta_ssid': settings['sta_ssid'], 'sta_pw': settings['sta_pw'], 'ap_pw': settings['ap_pw'], 'all': settings['all'], 'ap_ssid': settings['ap_ssid'], 'version': settings['version'], 'timezone': 2})
        
        trySend(headerPage())
        trySend(timezoneSwitchPage())
        trySend(footerPage("/settings"))
        
    elif page == "/timezoneone":
        settings = t_settings.find({"all": 1})
        t_settings.update(settings, {'display': settings['display'], 'sta_ssid': settings['sta_ssid'], 'sta_pw': settings['sta_pw'], 'ap_pw': settings['ap_pw'], 'all': settings['all'], 'ap_ssid': settings['ap_ssid'], 'version': settings['version'], 'timezone': 1})
        
        trySend(headerPage())
        trySend(timezoneSwitchPage())
        trySend(footerPage("/settings"))

    startTime()
    conn.close()
        