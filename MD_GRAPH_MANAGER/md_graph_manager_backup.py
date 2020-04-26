# Paul Zanelli
# 13th April 2020
# Class that seeks to extract knoweldge from a user utterance to build a graph

import logging
import spacy
import re
import pandas as pd
import bs4
import requests
from spacy import displacy

import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client
import json

from spacy.matcher import Matcher
from spacy.tokens import Span

import networkx as nx

import matplotlib.pyplot as plt
from tqdm import tqdm

pd.set_option('display.max_colwidth', 200)

class MyDaemonGraph:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.entity_pairs = []
        self.relations = []

    def add_utterance(self, utterance):

        print("Adding utterance")
        self.entity_pairs.append(self.get_entities(utterance))
        self.relations.append(self.get_relation(utterance))
        #print(self.entity_pairs)
        #print(entity_pairs[0])
        #print(entity_pairs[1])
        #print(self.relations)

    def draw_graph(self):
        # extract subject
        source = [i[0] for i in self.entity_pairs]

        # extract object
        target = [i[1] for i in self.entity_pairs]

        kg_df = pd.DataFrame({'source': source, 'target': target, 'edge': self.relations})

        G = nx.from_pandas_edgelist(kg_df, "source", "target",
                                    edge_attr=True, create_using=nx.MultiDiGraph())

        plt.figure(figsize=(12, 12))

        pos = nx.spring_layout(G)
        nx.draw(G, with_labels=True, node_color='skyblue', edge_cmap=plt.cm.Blues, pos=pos)
        plt.show()

    def get_entities(self, utterance):
        ## chunk 1
        ent1 = ""
        ent2 = ""

        prv_tok_dep = ""  # dependency tag of previous token in the sentence
        prv_tok_text = ""  # previous token in the sentence

        prefix = ""
        modifier = ""

        #############################################################

        utterance = utterance.lower()

        for tok in self.nlp(utterance):
            print(tok.text, tok.dep_)


        for tok in self.nlp(utterance):
            ## chunk 2
            # if token is a punctuation mark then move on to the next token
            if tok.dep_ != "punct":
                # check: token is a compound word or not
                if tok.dep_ == "compound":
                    prefix = tok.text
                    # if the previous word was also a 'compound' then add the current word to it
                    if prv_tok_dep == "compound":
                        prefix = prv_tok_text + " " + tok.text

                # check: token is a modifier or not
                if tok.dep_.endswith("mod") == True:
                    modifier = tok.text
                    # if the previous word was also a 'compound' then add the current word to it
                    if prv_tok_dep == "compound":
                        modifier = prv_tok_text + " " + tok.text

                ## chunk 3
                if tok.dep_.find("subj") == True:
                    ent1 = modifier + " " + prefix + " " + tok.text
                    prefix = ""
                    modifier = ""
                    prv_tok_dep = ""
                    prv_tok_text = ""

                    ## chunk 4
                if tok.dep_.find("obj") == True:
                    ent2 = modifier + " " + prefix + " " + tok.text

                ## chunk 5
                # update variables
                prv_tok_dep = tok.dep_
                prv_tok_text = tok.text
        #############################################################

        return [ent1.strip(), ent2.strip()]

    def get_relation(self, utterance):

        doc = self.nlp(utterance)

        # Matcher class object
        matcher = Matcher(self.nlp.vocab)

        # define the pattern
        pattern = [{'DEP': 'ROOT'},
                   {'DEP': 'prep', 'OP': "?"},
                   {'DEP': 'agent', 'OP': "?"},
                   {'POS': 'ADJ', 'OP': "?"}]

        matcher.add("matching_1", None, pattern)

        matches = matcher(doc)
        k = len(matches) - 1

        span = doc[matches[k][1]:matches[k][2]]

        return (span.text)

MyDaemonGraph_ = MyDaemonGraph()

def mydaemon_graph_add_utterance(input_text):
    MyDaemonGraph_.add_utterance(input_text)
    MyDaemonGraph_.draw_graph()


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
        print("We are ready to do something")

def main():
    local_mqtt_client = mqtt_client.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect("test.mosquitto.org", 1883, 60)

    #graph = MyDaemonGraph()
    #graph.draw_graph()

    local_mqtt_client.loop_forever()

if __name__ == '__main__':
    main()