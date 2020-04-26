# This programme checks to see if there is an utterance on the utterance server
# If there is it uses nltk to decompse and tag the utterance
# Note that I am dealing with an utterance but considering it to be a sentence
# Paul Zanelli
# Creation date: 4th April 2020

import nltk
import requests
import time
import sys
import getopt

import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client
import json

# from md_db_lookup import md_db_get_response

class MyDaemonQuestionGenerator:
    def __init__(self):
        print("Initialising the question generator class")
        self.next_question_number = 0
        self.number_of_questions = 5
        self.questions = ["Hello, my name is MyDaemon, what is your name?",
                          "What country do you live in?",
                          "What city do you live in",
                          "How old are you?",
                          "What is your favourite colour?"]
    def more_questions(self):
        if self.next_question_number < self.number_of_questions:
            return(True)
        else:
            return(False)

    def get_next_question(self):
        if self.next_question_number < self.number_of_questions:
            question = self.questions[self.next_question_number]
            self.next_question_number = self.next_question_number + 1
            return(question)
        else:
            print("No more questions in the start up question list")
            return("")

MyDaemonQuestionGenerator_ = MyDaemonQuestionGenerator()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("user")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):

    # Check that the message is in the right format
    message_text = msg.payload.decode('utf-8')
    try:
        message_json = json.loads(message_text)
    except Exception as e:
        print("Couldn't parse raw data: %s" % message_text, e)
    else:
        print("JSON received : ", message_json)

    # Check that the topic is "user" which indicates a message from the user
    if msg.topic == "user":
            # The msg has content from user
            if message_json["user"] != "":
                if message_json["user"].lower() == "shutdown" or message_json["user"].lower() == "shut down":
                    sys.exit()

                # Check to see if there are more questions
                if MyDaemonQuestionGenerator_.more_questions():
                    # There are more questions
                    question = MyDaemonQuestionGenerator_.get_next_question()
                    qa_json = {"user": "", "mydaemon": question}
                    qa_string = json.dumps(qa_json)
                    mqtt_publish.single("mydaemon", qa_string, hostname="test.mosquitto.org")
                    print("JSON published: ", qa_string)
                else:
                    question = "Tell me something about yourself"
                    qa_json = {"user": "", "mydaemon": question}
                    qa_string = json.dumps(qa_json)
                    mqtt_publish.single("mydaemon", qa_string, hostname="test.mosquitto.org")
                    print("JSON published: ", qa_string)

                    # If we are passed the start up phase we need to ask a question driven by the knowledge graph
                    # This section can be used to generate a response from a database
                    #qa_dataset = cb.load_database()
                    # answer = md_db_get_response(message_json["user"])
                    # message_json["mydaemon"] = answer
                    # message_text = json.dumps(message_json)
                    # mqtt_publish.single("mydaemon", message_text, hostname="test.mosquitto.org")
                    # print("JSON published: ", message_json)
            else:
                # Publish an empty message to keep the conversation going
                # This will force anybody listening to the "mydaemon" topic to run their callback
                message_json["mydaemon"] = ""
                message_text = json.dumps(message_json)
                mqtt_publish.single("mydaemon", message_text, hostname="test.mosquitto.org")
                print("JSON published: ", message_json)

def main(argv):

        local_mqtt_client = mqtt_client.Client()
        local_mqtt_client.on_connect = on_connect
        local_mqtt_client.on_message = on_message
        local_mqtt_client.connect("test.mosquitto.org", 1883, 60)

        # We have jsut started up so we need to start the conversation
        # At this point we have assumed that this is the first time MyDaemon has been switched on
        # The first question is therefore "what is your name"

        question = MyDaemonQuestionGenerator_.get_next_question()
        qa_json = {"user": "", "mydaemon": question}
        qa_string = json.dumps(qa_json)
        mqtt_publish.single("mydaemon", qa_string, hostname="test.mosquitto.org")
        print("JSON published: ", qa_string)

        while True:
                local_mqtt_client.loop_forever()

if __name__ == '__main__':
    main(sys.argv[1:])