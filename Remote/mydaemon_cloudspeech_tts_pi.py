#!/usr/bin/env python

import os
import subprocess
import sys


from time import sleep
from google.cloud import texttospeech

# set an environment variable so google cloud speach can find credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "./voice-assistant-246008-863f5e39dc2c.json"


class MyDaemonTTS:
    def __init__(self):
        # client variable for each instance
        self.client = texttospeech.TextToSpeechClient()

        # Create a female GB wavenet voice
        self.voice = texttospeech.types.VoiceSelectionParams(
            language_code='en-GB',
            name='en-GB-Wavenet-C',
            ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE)

        # Select the type of audio file you want returned
        self.audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3,
            volume_gain_db=-3,
            speaking_rate=1.0)

    def speak_text(self, input_text):
        synthesis_input = texttospeech.types.SynthesisInput(text=input_text)
        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = self.client.synthesize_speech(synthesis_input, self.voice, self.audio_config)

        # The response's audio_content is binary.
        with open('./output.mp3', 'wb') as out:
            # Write the response to the output file.
            out.write(response.audio_content)
            # print('Audio content written to file "output.mp3"')

        # play the file
        command_run = subprocess.call(
            ["play",
             "./output.mp3"])
        if command_run != 0:
            print("ERROR: mydaemon_tts - mydaemon_tts_speak - error calling omxplayer")

        # delete the file
        # command_run = subprocess.call(
        #    ["rm",
        #     "/home/pi/MyDaemon/python/output.mp3"])

        # if command_run != 0:
        # print("ERROR: mydaemon_tts - mydaemon_tts_speak - error calling omxplayer")


MyDaemonTTS_ = MyDaemonTTS()


def mydaemon_tts_speak(input_text):
    MyDaemonTTS_.speak_text(input_text)


if __name__ == '__main__':
    mydaemon_tts_speak(
        "Hello Paul. How are you today. I am MyDaemon and I am so happy that my voice now sounds less robotic and annoying.")