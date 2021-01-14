# -*- coding:utf-8 _*-
""" 
@file: tgpuworker_v2.py 
@time: 2020/11/24
@site:  
@software: PyCharm 

# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛ 
"""

from ws4py.client.threadedclient import WebSocketClient
import ws4py.messaging
import logging, json, time, _thread, sys
import queue, uuid
from config import Status, Color, CODE_PATH, words_ids_file, prosody_model_file, tacotron_model_file, unit_dir, \
    waveglow_model_file
import numpy as np

sys.path.append(CODE_PATH)
from CoSynth.synthesis import Synth

synthor = Synth(words_ids_file, prosody_model_file, tacotron_model_file, waveglow_model_file, unit_dir)
synthor.synth(['你好'])


# v2
class TGPUWebSocket2(WebSocketClient):
    logger = logging.getLogger('tgpuworker')

    def __init__(self, url, spkid):
        self.status = Status.CREATED
        self.id = str(uuid.uuid4())
        self.spkid = spkid
        super(TGPUWebSocket2, self).__init__(url=url, heartbeat_freq=10)

    def opened(self):
        self.send(json.dumps(dict(id=self.id, spkid=self.spkid)))
        self.status = Status.CONNECTED
        self.logger.info(
            'Opened websocket connection to server: {}<tgpu <{}>>{}, speaker({})'.format(Color['info'], self.id,
                                                                                         Color['end'], self.spkid))

    def received_message(self, msg):
        self.logger.info(
            '{}<tgpu <{}>>{}: Got message from server of type {}'.format(Color['info'], self.id, Color['end'],
                                                                         str(type(msg))))
        if isinstance(msg, ws4py.messaging.TextMessage):
            news = json.loads(str(msg.data.decode('utf-8')))
            self.logger.info(
                '{}<tgpu <{}>>{}: message information: {}'.format(Color['debug'], self.id, Color['end'], news))
            # got txts
            wavs = synthor.synth(news['txts'], self.logger)

            try:
                # gpu to server
                data = {"pageNum": news['pageNum'], "wav": [wav.astype(np.int16).tolist() for wav in wavs]}
                self.send(json.dumps(data))
                self.logger.info(
                    '{}<tgpu <{}>>{}: Writing back wave data to server.'.format(Color['info'], self.id, Color['end']))
            except Exception as e:
                self.logger.warning(
                    '{}<tgpu <{}>>{}: Can\'t write message back to the server, check whether the server is closed if needed'.format(
                        Color['warning'], self.id, Color['end']))

    def closed(self, code, reason=None):
        self.logger.debug('{}<tgpu <{}>>{}: Websocket closed() called'.format(Color['debug'], self.id, Color['end']))
        self.logger.info('{}<tgpu <{}>>{}: Websocket has closed'.format(Color['info'], self.id, Color['end']))
