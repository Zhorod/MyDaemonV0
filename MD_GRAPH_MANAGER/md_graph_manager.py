# Paul Zanelli
# 13th April 2020
# Class that seeks to extract knoweldge from a user utterance to build a graph

import pandas as pd
import re
import spacy

import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client
import json

from spacy.matcher import Matcher
from spacy.tokens import Span
import networkx as nx
import matplotlib.pyplot as plt
from md_gm_db import md_gm_db_get_response

def getSentences(text):
    nlp = English()
    nlp.add_pipe(nlp.create_pipe('sentencizer'))
    document = nlp(text)
    return [sent.string.strip() for sent in document.sents]

def printToken(token):
    print(token.text, "->", token.dep_)

def appendChunk(original, chunk):
    return original + ' ' + chunk

def isRelationCandidate(token):
    deps = ["ROOT", "adj", "attr", "agent", "amod"]
    return any(subs in token.dep_ for subs in deps)

def isConstructionCandidate(token):
    deps = ["compound", "prep", "conj", "mod"]
    return any(subs in token.dep_ for subs in deps)

def processSubjectObjectPairs(tokens):
    subject = ''
    object = ''
    relation = ''
    subjectConstruction = ''
    objectConstruction = ''
    for token in tokens:
        printToken(token)
        if "punct" in token.dep_:
            continue
        if isRelationCandidate(token):
            relation = appendChunk(relation, token.lemma_)
        if isConstructionCandidate(token):
            if subjectConstruction:
                subjectConstruction = appendChunk(subjectConstruction, token.text)
            if objectConstruction:
                objectConstruction = appendChunk(objectConstruction, token.text)
        if "subj" in token.dep_:
            subject = appendChunk(subject, token.text)
            subject = appendChunk(subjectConstruction, subject)
            subjectConstruction = ''
        if "obj" in token.dep_:
            object = appendChunk(object, token.text)
            object = appendChunk(objectConstruction, object)
            objectConstruction = ''

    print (subject.strip(), ",", relation.strip(), ",", object.strip())
    return (subject.strip().lower(), relation.strip().lower(), object.strip().lower())

def printGraph(triples):
    G = nx.Graph()
    for triple in triples:
        G.add_node(triple[0])
        G.add_node(triple[1])
        G.add_node(triple[2])
        G.add_edge(triple[0], triple[1])
        G.add_edge(triple[1], triple[2])

    pos = nx.spring_layout(G)
    plt.figure()
    nx.draw(G, pos, edge_color='black', width=1, linewidths=1,
            node_size=500, node_color='seagreen', alpha=0.9,
            labels={node: node for node in G.nodes()})
    plt.axis('off')
    plt.show()

class MyDaemonGraph:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm') # can use the large model though takes a while to load
        self.user_name = "" # this is the name of the user
        self.user_age = 0  # this is the age of the user
        self.triples = []

    def set_user_name(self, text):
        self.user_name = text
        print("User name set to: ", self.user_name)

    def extract_user_name(self, text):
        doc = self.nlp(text)
        name = ""
        for token in doc:
            if token.pos_ == "PROPN":
                if name == "":
                    name = token.text
                else:
                    print("WARNING: text includes multiple proper nouns")
        return(name)

    def set_user_age(self, age):
        self.user_age = age
        print("User age set to: ", self.user_age)

    def extract_user_age(self, text):
        doc = self.nlp(text)
        age = 0
        for token in doc:
           if token.pos_ == "NUM":
               if age == 0:
                   age = token.text
               else:
                   print("WARNING: text includes multiple numbers")
        return (age)

    def process_text(self, user_text, mydaemon_text):
        # Compare the user input to the database to match a topic
        # This is not currently used
        #topic = md_gm_db_get_response(user_text)
        #print("The topic is: ",topic)

        print("Notice: processing text")
        # check to see if the question was asking for the user's name
        # if it was, extract and set the user's name
        if "what is your name" in mydaemon_text.lower():
            name = MyDaemonGraph_.extract_user_name(user_text)
            if name != "":
                MyDaemonGraph_.set_user_name(name)
                if( self.user_age != 0):
                    # add "name" "is" "age" to the graph
                    self.triples.append(this.user_name,"is",this.user_age)
                    printGraph(self.triples)
            else:
                print("ERROR: could not detect the user's name")
        # check to see if the question was asking for the user's age
        # if it was, extract and set the user's age
        elif "how old are you" in mydaemon_text.lower():
            age = MyDaemonGraph_.extract_user_age(user_text)
            if age != 0:
                MyDaemonGraph_.set_user_age(age)
                if (self.user_name != ""):
                    # add "name" "is" "age" to the graph
                    self.triples.append([self.user_name, "is", self.user_age])
                    printGraph(self.triples)
            else:
                print("ERROR: failed to detect the user's age")
        else:
            triple = self.processSentence(user_text)

            # Check that all of the triple has data
            print("Triple is: ", triple)
            if triple[0] != "" and triple[1] != "" and triple[2] != "":
                # Check to see if the subject is the user
                if triple[0] == "I" or triple[0] == "i" or triple[0] == "my" or triple[0] == "My":
                    new_triple = [self.user_name, triple[1], triple[2]]
                    self.triples.append(new_triple)
                else:
                    self.triples.append(triple)
                printGraph(self.triples)
            else:
                print("Notice: the tripple was not complete")

    def processSentence(self, sentence):
        tokens = self.nlp(sentence)
        return processSubjectObjectPairs(tokens)


MyDaemonGraph_ = MyDaemonGraph()


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
        MyDaemonGraph_.process_text(message_json["user"],message_json["mydaemon"])

def main():
    local_mqtt_client = mqtt_client.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect("test.mosquitto.org", 1883, 60)
    local_mqtt_client.loop_forever()

    local_json = {"user": "Paul", "mydaemon": "What is your name?"}
    MyDaemonGraph_.process_text(local_json["user"],local_json["mydaemon"])
    local_json = {"user": "I am 49 years old", "mydaemon": "How old are you?"}
    MyDaemonGraph_.process_text(local_json["user"],local_json["mydaemon"])
    local_json = {"user": "I live in Bath", "mydaemon": "Where do you live?"}
    MyDaemonGraph_.process_text(local_json["user"], local_json["mydaemon"])
    local_json = {"user": "I live in England", "mydaemon": "What country do you live in?"}
    MyDaemonGraph_.process_text(local_json["user"], local_json["mydaemon"])
    local_json = {"user": "I have two daughters", "mydaemon": "Tell me something about yoursefl?"}
    MyDaemonGraph_.process_text(local_json["user"], local_json["mydaemon"])
    local_json = {"user": "I have a wife called Hazel", "mydaemon": "Tell me something about yourself?"}
    MyDaemonGraph_.process_text(local_json["user"], local_json["mydaemon"])


if __name__ == '__main__':
    main()