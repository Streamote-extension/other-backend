import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import tensorflow as tf
from flask import stream_with_context, request, Response, Flask
from flask_socketio import SocketIO, send, emit
from keras.models import load_model
from realtime_VideoStreamer import VideoStreamer
from keras import backend as K
from threading import Timer
import time
import datetime

from realtime_RecognitionEngine_textOutput_v2 import RecognitionEngine
import multiprocessing.dummy as mp

emotion_model_path = './Engine/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5'
emotion_classifier = load_model(emotion_model_path, compile=False)
emotion_classifier._make_predict_function()
# graph = tf.get_default_graph()

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading", ping_timeout=10000)

streamer_list = []
analyseAll = False

currentlyPlayingEmote = False

# r_engine = RecognitionEngine(streamer_list,  emotion_classifier, graph, queueSize=128)



@socketio.on('connect')
def handle_connect():
    print("connected")
    emit('test', 'test0')

@socketio.on('message')
def handle_message(arg1):
    print(arg1)
    emit('test', 'test1')

@socketio.on('disconnect')
def handle_disconnect():
    #K.clear_session()
    print('disconnected')

@socketio.on('analyseAll')
def handle_analyse(arg1):
    print("changed analyse satus to " + arg1)
    analyseAll = arg1

@socketio.on('ev')
def abc(json):
    print(json)

@socketio.on('sendStreamer')
def handle_streamer(arg1):

    global currentlyPlayingEmote

    print("")
    print('RECEIVED: ' + str(arg1))
    print("")

    emit('sessionStatus', '0') # deleted network

    tf.reset_default_graph()
    graph = tf.get_default_graph()

    emit('sessionStatus', '1')  # created Network

    streamer = arg1['streamer']
    # game = arg1['game']

    resolution = '360p'


    print("")
    print("STARTING TO ANALYSE " + str(streamer) + " stream")
    print("")

    stream = VideoStreamer("https://www.twitch.tv/"+streamer, queueSize=128, resolution=resolution, n_frame=15)

    r_engine = RecognitionEngine(VStreamer=stream, emotion_classifier=emotion_classifier, graph=graph, queueSize=128)

    emit('sessionStatus', '2')  # initialised FFMPEG

    while True:

        if r_engine.more():

            element = r_engine.read()
            text = "[" + str(element[0]) + ", " +str(element[1]) + "]"
            print(text)

            # with open('emotion_logging.txt', 'a') as f:
            #     f.write("{};{};{};{};\n".format(str(element[0]), str(element[1]), str(game), datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
            #     f.close()

            # if element[0] == "angry":
            confidenceScore = element[1]
            emotion = element[0]
            if (confidenceScore > 0.4 and not currentlyPlayingEmote and emotion != 'neutral'):
                currentlyPlayingEmote = True
                emit('rageIncoming', {'emotion': str(emotion), 'confidence': str(confidenceScore), 'emote': 'Hypers'}, broadcast=True)
                
                def flipPlaying():
                    global currentlyPlayingEmote
                    currentlyPlayingEmote = False
                
                t = Timer(15.0, flipPlaying)
                t.start()

        else:
            continue

if __name__ == '__main__':
    socketio.run(app, port=5000)
