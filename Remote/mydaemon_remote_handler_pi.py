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

from mydaemon_cloudspeech_tts_pi import mydaemon_tts_speak
from mydaemon_cloudspeech_stt_pi import mydaemon_stt_capture

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
        mydaemon_tts_speak(message_json["mydaemon"])
    
    # get the next input from the user
    while True:
        utterance = mydaemon_stt_capture()
        #MyDaemonSTT_.recognise_speech()
        if utterance != None:

            # create a string which has a question and and space for an answer
            qa_json = {"user": "", "mydaemon": ""}
            qa_json["user"] = utterance
            qa_string = json.dumps(qa_json)

            # publish the JSON
            mqtt_publish.single("user", qa_string, hostname="test.mosquitto.org")
            # print the JSON
            print("JSON published: ", qa_json)
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
        # Publish an empty JSON to get the interacvtion started
        qa_json = {"user": "", "mydaemon": ""}
        qa_json["user"] = ""
        qa_string = json.dumps(qa_json)
        mqtt_publish.single("user", qa_string, hostname="test.mosquitto.org")
        local_mqtt_client.loop_forever()


if __name__ == '__main__':
    main()
