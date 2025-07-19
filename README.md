# ATAG Q Series Display hacking
In my central heating system I have a Gas Boiler (ATAG Q15S installed in 2007) which has no possibility to be controlled/monitored remotely.

<img width="500" height="600" alt="image" src="https://github.com/user-attachments/assets/398f28db-7c2b-4c17-ae9b-5ad613c743f5" />


I started to have some issues, which cause a block of the heater and requires a manual intervention to restart it:

<img width="300" height="500" alt="image" src="https://github.com/user-attachments/assets/0f6e1a62-06f1-4d3a-9098-7d889341328d" />


Before the cause of the issue has been found and fixed I had to check periodically the display of the boiler to verify the presence of the malfunction.

I started to look for a solution, ready to use, which gave the possibility to remotely monitor the boiler.

I didn't find it but I found some useful information (https://www.circuitsonline.net/forum/view/160463?query=display+ic&mode=or) which suggested to implement a system to visualize the content of the 7 segment display by means of a network service.

The digits of the display are driven by an NXP (formerly Philips) SAA1064 IC which interprets I2C messages to switch on/off 7 segments LEDs.

<img width="280" height="350" alt="image" src="https://github.com/user-attachments/assets/1da75aa7-565b-4000-9480-1839ff052b2f" /> <img width="200" height="300" alt="image" src="https://github.com/user-attachments/assets/eb6ff195-cb22-443a-9d65-b7c2586f5cb1" /> <img width="330" height="350" alt="image" src="https://github.com/user-attachments/assets/5b4b79ef-84e0-4651-b965-3d05ec1b59ea" />

<img width="550" height="500" alt="image" src="https://github.com/user-attachments/assets/61850d56-e98a-4907-96bb-09065601700f" />

I used a Raspberry Pi Pico 2 w which has Programmable IO (PIO) blocks (4 state machines for custom peripheral support) which permits I2C bus sniffing (in pure HW, without SW interrupt intervention, see:  https://github.com/jjsch-dev/pico_i2c_sniffer) and provides 5V tolerant pins.

It is not possible to use a standard and widely available I2C slave peripheral, because it would conflict with the SAA1064, causing unpredictable behavior.

I ported the RP2040 I2C sniffer implementation from C-SDK to MicroPython, in order to simplify and speedup the integration with web interface libs.

I added a library to interface with a Telegram Bot which offers, at zero cost, the possibility to send and receive messages from "Display sniffer" to a mobile phone.

Secondly I added the OTA library, wich permits to remotely update tha main script main.py (downloading the latest version from this Github repository).

Telegram chat bot provides a simple way to implement custom commands to easily communicate with MicroPython:

<img width="400" height="8000" alt="image" src="https://github.com/user-attachments/assets/f8148454-46a3-47dc-89da-fe38ad83c3b2" />
