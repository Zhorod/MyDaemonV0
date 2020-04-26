# MyDaemon python script that manages a conversation with a second script
# Communication is through MQTT
# Paul Zanelli
# 13th April 2020

import argparse
import locale
import logging
import requests
import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client
import json
import time
import sys

from google.cloud.speech import enums
from google.cloud.speech import types

from md_tts_pc import md_tts_speak
from md_stt_pc import md_stt_capture

def on_connect(mqtt_client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    mqtt_client.subscribe("mydaemon")


# The callback for when a PUBLISH message is received from the server.
def on_message(mqtt_client, userdata, msg):
    # check to see if the message has valid content
    message_text = msg.payload.decode('utf-8')
    try:
        message_json = json.loads(message_text)
    except Exception as e:
        print("Couldn't parse raw data: %s" % message_text, e)
    else:
        print("JSON received : ", message_json)

    # if the message topic is mydaemon
    if msg.topic == "mydaemon":
        md_tts_speak(message_json["mydaemon"])

    # get the next input from the user
    while True:
        utterance = md_stt_capture()
        if utterance != None:
            # The utterance has data in it
            # Create a string which has a question and and space for an answer
            message_json["user"] = utterance
            message_string = json.dumps(message_json)

            # publish the JSON
            mqtt_publish.single("user", message_string, hostname="test.mosquitto.org")

            # print the JSON
            print("JSON published: ", message_json)

            # If the user has said shutdown or shut down then exit
            if utterance.lower() == "shutdown" or utterance.lower() == "shut down":
                sys.exit()

            # stop listening and wait for an answer
            break

def main():
   # Create an MQTT client and attach our routines to it.
    local_mqtt_client = mqtt_client.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect("test.mosquitto.org", 1883, 60)

    while True:
        # Loop the MQTT client
        local_mqtt_client.loop_forever()

if __name__ == '__main__':
    main()
