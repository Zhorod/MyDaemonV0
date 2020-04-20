# This programme checks to see if there is an utterance on the utterance server
# If there is it uses nltk to decompse and tag the utterance
# Note that I am dealing with an utterance but considering it to be a sentence
# Paul Zanelli
# Creation date: 4th April 2020

# poll ofr utterances from "user" and create responses from "mydaemon"

import nltk
import requests
import time
import sys
import getopt

import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client
import json

from mydaemon_qa import mydaemon_qa_get_response

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("user")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    message_text = msg.payload.decode('utf-8')
    try:
        message_json = json.loads(message_text)
    except Exception as e:
        print("Couldn't parse raw data: %s" % message_text, e)
    else:
        print("JSON received : ", message_json)

    if msg.topic == "user":
            # The msg has content from user
            if message_json["user"] != "":
                if message_json["user"].lower() == "shutdown" or message_json["user"].lower() == "shut down":
                    sys.exit()

                #qa_dataset = cb.load_database()
                answer = mydaemon_qa_get_response(message_json["user"])
                message_json["mydaemon"] = answer
                message_text = json.dumps(message_json)
                mqtt_publish.single("mydaemon", message_text, hostname="test.mosquitto.org")
                print("JSON published: ", message_json)
            else:
                message_json["mydaemon"] = ""
                message_text = json.dumps(message_json)
                mqtt_publish.single("mydaemon", message_text, hostname="test.mosquitto.org")
                print("JSON published: ", message_json)

def main(argv):

        local_mqtt_client = mqtt_client.Client()
        local_mqtt_client.on_connect = on_connect
        local_mqtt_client.on_message = on_message
        local_mqtt_client.connect("test.mosquitto.org", 1883, 60)

        while True:
                local_mqtt_client.loop_forever()

if __name__ == '__main__':
    main(sys.argv[1:])