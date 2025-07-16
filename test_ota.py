from ota import OTAUpdater
# from WIFI_CONFIG import SSID, PASSWORD

firmware_url = "https://github.com/mmaz73/ota_upython_atag_q_display/main/"

ota_updater = OTAUpdater(firmware_url, "main.py")

ota_updater.download_and_install_update_if_available()
