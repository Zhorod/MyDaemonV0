
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

#from mydaemon_tts import mydaemon_tts_speak
from aiy.board import Board, Led
from aiy.cloudspeech import CloudSpeechClient
from aiy.voice import tts

def get_hints(language_code):
    if language_code.startswith('en_'):
        return ('turn on the light',
                'turn off the light',
                'blink the light',
                'goodbye')
    return None


def locale_language():
    language, _ = locale.getdefaultlocale()
    return language

class MyDaemonSTT:
    def __init__(self):
        # client variable for each instance of MyDaemonSTT
        self.client = CloudSpeechClient()
        # set the langauge code to the local language code
        self.language_code = locale_language()
        # create a set of hint phrases to bias the recognition
        self.hints = get_hints("en-GB")
        self.text = ""

    def capture_utterance(self):
        # recognize from the mic and store results in self.text
        self.text = self.client.recognize(self.language_code, self.hints)
        return self.text

MyDaemonSTT_ = MyDaemonSTT()

def mydaemon_stt_capture():
    return(MyDaemonSTT_.capture_utterance())

def main():
    print(mydaemon_stt_capture())

if __name__ == '__main__':
    main()
