# This program capture I2C writes towards the display 
# and send them to the telegram bot
# 

### Config your stuff here
from PLAT_CONFIG import TelegramToken, WDT_ENABLED, WL_SSID, WL_PW

Msg_prefix = "ATAG Q15S 01 "
Token = TelegramToken

firmware_url = "https://github.com/mmaz73/ota_upython_atag_q_display/"

###

import network
import uasyncio as asyncio
from telegram import TelegramBot
from ota import OTAUpdater

import sys
import time
from machine import Pin, PWM
import rp2
from rp2 import PIO

from machine import WDT
if WDT_ENABLED:
  print("Watchdog enabled in PLAT_CONFIG!")
  wdt = WDT(timeout=8000)  # enable it with a timeout of 8s

#from boot import WL

SDA_PIN = Pin(16, Pin.IN)
SCL_PIN = Pin(17, Pin.IN)
EV0_PIN = Pin(18, Pin.OUT)
EV1_PIN = Pin(19, Pin.OUT)
SAA1064 = 0x70

DisplayCurrent = "P 19"
DisplayOld = DisplayCurrent
LiveDisplayOn = False
LiveTempOn = False
Chat_id = None
TemperatureCurrent = "NA"
TemperatureOld = TemperatureCurrent
LastPressure = "0.0"
WlanIp = "0.0.0.0"

SevenSegDig = {
  0x00: " ",
  0x3F: "0",
  0x06: "1",
  0x07: "1",
  0x5B: "2",
  0x4F: "3",
  0x66: "4",
  0x6D: "5",
  0x7D: "6",
  0x27: "7",
  0x7F: "8",
  0x6F: "9",
  0x77: "A",
  0x7C: "b",
  0x39: "C",
  0x5E: "d",
  0x79: "E",
  0x71: "F",
  0x3D: "G",
  0x76: "H",
  0x30: "I",
  0x38: "L",
  0x37: "N",
  0x54: "n",
  0x5c: "o",
  0x73: "P",
  0x50: "r",
  0x31: "R",
  0x78: "t",
  0x3E: "U",
  0x6E: "Y"
}

def mycallback(bot,msg_type,chat_name,sender_name,chat_id,text,entry):
    global Msg_prefix, TemperatureCurrent, LastPressure, DisplayCurrent, LiveDisplayOn, LiveTempOn, Chat_id
    print(msg_type,chat_name,sender_name,chat_id,text)
    Chat_id = chat_id

    if text == "/temp":
        reply = Msg_prefix + "Temperature: " + TemperatureCurrent + "°C"
    elif text == "/pressure":
        reply = Msg_prefix + "Pressure: " + LastPressure + " Bar"
    elif text == "/ip":
        reply = Msg_prefix + "Local IP: " + str(WlanIp)
    elif text == "/display":
        reply = Msg_prefix + "Display: " + DisplayCurrent
    elif text == "/livedisplayon":
        LiveDisplayOn = True
        reply = Msg_prefix + "LiveDisplayOn"
    elif text == "/livedisplayoff":
        LiveDisplayOn = False
        reply = Msg_prefix + "LiveDisplayOff"
    elif text == "/livetempon":
        LiveTempOn = True
        reply = Msg_prefix + "LiveTempOn"
    elif text == "/livetempoff":
        LiveTempOn = False
        reply = Msg_prefix + "LiveTempOff"
    elif text == "/reset":
        reply = "Module reset!"
#        sys.exit()
    elif text == "/otaupdate":
        reply = "Checking for update!"
        ota_updater = OTAUpdater(firmware_url, "main.py")
        
        ota_updater.download_and_install_update_if_available()
    else:
        reply = Msg_prefix + "Display: " + DisplayCurrent
    
    bot.send(chat_id,reply)

@rp2.asm_pio(set_init=(rp2.PIO.OUT_HIGH,rp2.PIO.OUT_HIGH))

def i2c_start():
    wrap_target()
    wait(0, gpio, 16)                     # 0
    jmp(pin, "3")                         # 1
    jmp("5")                              # 2
    label("3")
    set(pins, 1)                          # 3
    irq(block, 7)                          # 4
    label("5")
    wait(1, gpio, 16)                     # 5
    wrap()

# -------- #
# i2c_data #
# -------- #

@rp2.asm_pio(set_init=(rp2.PIO.OUT_HIGH,rp2.PIO.OUT_HIGH))

def i2c_data():
    wrap_target()
    wait(1, gpio, 17)                     # 0
    set(pins, 0)                          # 1
    irq(block, 7)                          # 2
    wait(0, gpio, 17)                     # 3
    wrap()

# -------- #
# i2c_main #
# -------- #

@rp2.asm_pio(autopush=True,push_thresh=9, in_shiftdir=rp2.PIO.SHIFT_LEFT, fifo_join=PIO.JOIN_RX,)
def i2c_main():
    wrap_target()
    label("0")
    wait(1, irq, 7)                       # 0
    jmp(pin, "4")                         # 1
    in_(pins, 1)                          # 2
    jmp("0")                              # 3
    label("4")                            # Start or Stop
    mov(isr, pins)                        # 4
    wrap()

# Instantiate StateMachine(0) with wait_sda_low program on Pin(16).

sm0 = rp2.StateMachine(0, i2c_start, in_base=SDA_PIN, set_base=EV0_PIN, jmp_pin=SCL_PIN,)

sm2 = rp2.StateMachine(2, i2c_data, in_base=SDA_PIN, set_base=EV0_PIN, jmp_pin=SCL_PIN,)

sm3 = rp2.StateMachine(3, i2c_main, in_base=SDA_PIN, jmp_pin=EV0_PIN,)

# Start the StateMachine's running.
sm0.active(1)
sm2.active(1)
sm3.active(1)

############################
    
async def ReadFifoSM():
  global Repeat, State, TemperatureCurrent, LastPressure, DisplayCurrent

  while True:
     if sm3.rx_fifo()>0:
        val = sm3.get()
        ev_code = (val >> 11) & 0x03
        data = ((val >> 1) & 0xFF)
        if State == "Idle":
            if (ev_code == 1) and (data == SAA1064):
               State = "Instr"
            else :
               State = "Idle"
        elif  State == "Instr":
               State = "Control"
        elif  State == "Control":
               State = "D1"
        elif  State == "D1":
               State = "D2"
               Digit0 = data & 0x7F
        elif  State == "D2":
               State = "D3"
               Digit1 = data & 0x7F
        elif  State == "D3":
               State = "D4"
               Digit2 = data & 0x7F
        elif  State == "D4":
               State = "Idle"
               Digit3 = data & 0x7F
               #Discard noisy readings
               RawDisplay = SevenSegDig.get(Digit0,"X") + SevenSegDig.get(Digit1,"X") + SevenSegDig.get(Digit2,"X") + SevenSegDig.get(Digit3,"X")
               if not any(elem in "XU" for elem in RawDisplay):
                 DisplayCurrent = RawDisplay
                 await asyncio.sleep(0.02)
                 if DisplayCurrent[0] == "P":
                    LastPressure = DisplayCurrent[2] + "." + DisplayCurrent[3]
                 else:
                    TemperatureCurrent = DisplayCurrent[2] + DisplayCurrent[3]
               else:
                 await asyncio.sleep(0.1)
     else:
       await asyncio.sleep(0.01)
       # Feed watchdog to avoid deadlocks
       if WDT_ENABLED:
         if WL.isconnected():
           wdt.feed()

async def LiveDisplay():
  global DisplayCurrent, DisplayOld, TemperatureCurrent, TemperatureOld, LiveDisplayOn, LiveTempOn, Chat_id, Msg_prefix

  while True:
     if DisplayOld != DisplayCurrent:
        DisplayOld = DisplayCurrent
        if (LiveDisplayOn == True) and (Chat_id != None):
           reply = Msg_prefix + "Display: " + DisplayOld
           bot.send(Chat_id,reply)
        if TemperatureOld != TemperatureCurrent:
           TemperatureOld = TemperatureCurrent
           if (LiveTempOn == True) and (Chat_id != None):
              reply = Msg_prefix + "Temperature: " + TemperatureCurrent + "°C"
              bot.send(Chat_id,reply)

     await asyncio.sleep(0.2)

############################
# Main program
############################

print("Starting Telegram sniff I2C")

# Set initial State
State = "Idle"

# Connect wifi

WL = network.WLAN(network.STA_IF)

if not WL.isconnected():
    print('connecting to network...')
    WL.active(True)
    WL.connect(WL_SSID, WL_PW)
    while not WL.isconnected():
        pass

print('network config:', WL.ifconfig())

bot = TelegramBot(Token,mycallback)

asyncio.create_task(bot.run())
asyncio.create_task(ReadFifoSM())
asyncio.create_task(LiveDisplay())

loop = asyncio.get_event_loop()
loop.run_forever()


