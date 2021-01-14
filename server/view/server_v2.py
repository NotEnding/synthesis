# -*- coding:utf-8 _*-
""" 
@file: server_v2.py 
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

import tornado.websocket
import logging, json, time
import uuid
from config import Status, BUFFER_SIZE, Color, DELAY_TIMEOUT, CODE_PATH, nclient_per_gpu, TOP_N, SplitList, options
import queue
import sys, os, re

sys.path.append(CODE_PATH)
from toolkit import text_normalize, alaw_init, linear2alaw

alaw_init(options['alaw_A'])
from hparams import hparams
import numpy as np
from librosa.core import resample


# deal with gpu client(now only to support Tacotorn-2)
class TClientSocketHandler2(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        self.id = str(uuid.uuid4())
        self.Status = Status.CREATED
        self.num_doing = 0
        self.num_waits = 0
        self.num_done = 0
        self.num_total = 0
        self.priority = time.time()
        self.wav_buffer = dict()
        self.task_queue = dict()
        super(TClientSocketHandler2, self).__init__(application, request, **kwargs)

    def check_origin(self, origin):
        return True

    def initialize(self, logname='TClientSocketHandler'):
        self.logger = logging.getLogger(logname)

    def open(self):
        self.status = Status.CONNECTED
        self.application.tclients.append(self)
        self.logger.info('{}<tclient <{}>>{}: Request opening'.format(Color['info'], self.id, Color['end']))
        if sum(list(self.application.tgpus.values())) < 1:
            self.logger.error(
                '{}<tclient <{}>>{}: There is no TGPU worker active'.format(Color['error'], self.id, Color['end']))
            self.status = Status.CANCELLING
            self.close()

        elif sum(list(self.application.tgpus.values())) * nclient_per_gpu < len(self.application.tclients):
            event = dict(code=400, status=str(Status.NOT_AVAILABLE),
                         message='The gpu worker is busy now(each gpu worker supports {} clients). we now have {} gpus, however we have {} clients to be served, all gpus are busy now. please try again later'.format(
                             nclient_per_gpu, sum(list(self.application.tgpus.values())),
                             len(self.application.tclients)))
            try:
                self.write_message(json.dumps(event))
            except Exception as e:
                self.logger.warning(
                    '{}<client <{}>>{}: Can\'t write back message to client(no worker)'.format(Color['warning'],
                                                                                               self.id, Color['end']))
            self.close()
        else:
            self.logger.info('{}<tclient <{}>>{}: Request opened'.format(Color['info'], self.id, Color['end']))
            self.logger.info(
                '{}<tclient <{}>>{}: There exists {} clients and {} gpus'.format(Color['info'], self.id, Color['end'],
                                                                                 len(self.application.tclients), sum(
                        list(self.application.tgpus.values()))))
            self.application.num_running_tasks += 1
            self.application.send_status_update()

    def on_message(self, msg):
        if self.status in [Status.CONNECTED, Status.PROCESSING]:
            self.logger.info(
                '{}<tclient <{}>>{}: Receiving message ({}) of length {} from client.'.format(Color['info'], self.id,
                                                                                              Color['end'], type(msg),
                                                                                              len(msg)))

            if msg == '<eos>':
                self.status = Status.EOS_RECEIVED
                self.logger.info(
                    '{}<tclient <{}>>{}: Received the EOS flag from client, waiting for the previous task to be finished.'.format(
                        Color['info'], self.id, Color['end']))
                if self.num_doing + self.num_waits == 0:
                    self.close()
                return

            try:
                assert sum(list(self.application.tgpus.values())) > 0
            except AssertionError as e:
                self.logger.error(
                    '{}<tclient <{}>>{}: There is no TGPU worker active'.format(Color['error'], self.id, Color['end']))

            # TODO: segmentation
            msg = json.loads(msg)
            required_fields = set(['spkid', 'text', 'pageNum'])
            if len(required_fields - set(msg.keys())) != 0:
                self.logger.warning(
                    '{}<tclient <{}>>{}: Skip this msg because there are some properties missed: {}'.format(
                        Color['warning'], self.id, Color['end'], required_fields - set(msg.keys())))
                return
            self.logger.debug(
                '{}<tclient <{}>>{}: message information: <"spkid": "{}", "text": "{}","pageNum":"{}">'.format(
                    Color['debug'], self.id, Color['end'], msg['spkid'], msg['text'], msg['pageNum']))
            spkid, text, pageNum = msg['spkid'], msg['text'], msg['pageNum']
            if spkid not in self.application.tgpus:
                self.logger.warning(
                    '{}<tclient <{}>>{}: Client close because there is not correspond speaker({})'.format(
                        Color['warning'], self.id, Color['end'], spkid))
                event = dict(code=404, status=str(Status.NOT_AVAILABLE),
                             message='This is no gpu worker for speaker {}; available speakers are listed as following: {}'.format(
                                 spkid, self.application.tgpus))
                try:
                    self.write_message(json.dumps(event))
                except Exception as e:
                    self.logger.warning(
                        '{}<client <{}>>{}: Can\'t write back message to client(no worker)'.format(Color['warning'],
                                                                                                   self.id,
                                                                                                   Color['end']))
                self.close()
                return

            if spkid not in self.task_queue:
                self.task_queue[spkid] = queue.Queue(maxsize=BUFFER_SIZE)

            txts = re.split(SplitList, text.strip())
            for txt in txts:
                if len(txt) == 0:
                    continue
                for text in text_normalize(txt).split(','):
                    self.num_total += 1
                    self.task_queue[spkid].put((text, self.num_total))
                    self.num_waits += 1
                self.status = Status.PROCESSING
            self.status = Status.PROCESSING

            if self.task_queue[spkid].empty():
                return

            # TODO: if or while??
            remain_tgpus = [tgpu_handler for tgpu_handler in self.application.free_tgpus if tgpu_handler.spkid == spkid]
            if len(remain_tgpus) != 0:
                tgpu_handler = remain_tgpus.pop()
                self.application.free_tgpus.discard(tgpu_handler)

                clients, txts = self.application.get_tasks(spkid=tgpu_handler.spkid, top_n=TOP_N)
                logmsg = ''.join(
                    ['<tclient <{}>> <idx{}> : {}\n'.format(client[0].id, client[1], txt) for client, txt in
                     zip(clients, txts)])
                self.application.logger.debug(
                    'Select a serial of tasks for speaker({}) to deal with:\n{}'.format(tgpu_handler.spkid, logmsg))
                try:
                    # server to tgpu
                    news = {"pageNum": pageNum, "txts": txts}
                    tgpu_handler.write_message(json.dumps(news))
                    tgpu_handler.await_clients = clients
                    tgpu_handler.status = Status.PROCESSING
                except Exception as e:
                    self.logger.error(
                        '{}<tgpu <{}>>{}: TGPU worker is not active'.format(color['error'], tgpu_handler.id,
                                                                            color['end']))

        elif self.status == Status.EOS_RECEIVED:
            self.logger.warning(
                '{}<tclient <{}>>{}: Has received the EOS flag, new message will be ignored.'.format(Color['warning'],
                                                                                                     self.id,
                                                                                                     Color['end']))
        elif self.status != Status.CANCELLING:
            self.logger.error(
                '{}<tclient <{}>>{}: status doesn\'t match <{}>'.format(Color['error'], self.id, Color['end'],
                                                                        self.status))
            raise Exception('status doesn\'t match')

    def on_close(self):
        try:
            self.application.tclients.remove(self)
            self.application.num_requests_processed += 1
            self.application.num_running_tasks -= 1
            self.application.send_status_update()
        except:
            # TODO:
            print('**********something wrong with the application.tclients************')
            pass
        self.logger.info('{}<tclient <{}>>{}: client leaving'.format(Color['info'], self.id, Color['end']))


# deal with gpu backward msg(now only to support Tacotron-2)
class TGPUSocketHandler2(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        self.id = None
        self.status = Status.CREATED
        self.await_clients = None
        super(TGPUSocketHandler2, self).__init__(application, request, **kwargs)

    def check_origin(self, origin):
        return True

    def initialize(self, logname='TGPUSocketHandler'):
        self.logger = logging.getLogger(logname)

    def open(self):
        self.status = Status.CONNECTED
        self.application.free_tgpus.add(self)

    def on_message(self, msg):
        if self.status == Status.CONNECTED and self.id is None:
            msg = json.loads(msg)
            self.id = msg['id']
            self.spkid = msg['spkid']
            if self.spkid not in self.application.tgpus:
                self.application.tgpus[self.spkid] = 1
            else:
                self.application.tgpus[self.spkid] += 1

            self.logger.info(
                'New TGPU worker available {}<tgpu <{}>>{} of {}'.format(Color['info'], self.id, Color['end'],
                                                                         self.spkid))
            self.logger.info(self.application.server_status())
            self.status = Status.INITIALIZED
        elif self.status in [Status.INITIALIZED, Status.PROCESSING]:
            self.logger.info(
                '{}<tgpu <{}>>{}: Receiving message ({}) of length {} from TGPU worker.'.format(Color['info'], self.id,
                                                                                                Color['end'], type(msg),
                                                                                                len(msg)))
            # self.logger.debug('{}<tgpu <{}>>{}: message information: {}'.format(Color['debug'], self.id, Color['end'], msg))
            assert self.await_clients is not None
            data = json.loads(msg)
            for (client, idx), wav in zip(self.await_clients, data['wav']):
                assert idx not in client.wav_buffer
                client.wav_buffer[idx] = wav

                while client.num_done + 1 in client.wav_buffer:
                    try:
                        # server to tclient
                        client.num_doing -= 1
                        client.num_done += 1
                        wav = client.wav_buffer.pop(client.num_done)
                        wav = np.array(wav, np.int16)

                        # sample rate adjusting
                        if options['sample_rate'] != hparams.sample_rate:
                            wav = resample(wav.astype(np.float32), hparams.sample_rate, options['sample_rate'],
                                           res_type='kaiser_best').astype(np.int16)

                        # wavformat adjusting
                        if options['wavform'] == 'alaw':
                            wav = np.array(linear2alaw(wav), dtype=np.int8)

                        # add page info & finished flag to client
                        if client.num_doing:  # 单次请求还没全部完成的时候
                            event = dict(code=200, status=str(Status.PROCESSING),
                                         message='text synthesis wave data processing', wav_data=wav.tolist(),
                                         pageNum=data['pageNum'])
                        else:  # 单次请求全部完成
                            event = dict(code=200, status=str(Status.FINISHED),
                                         message='text synthesis wave data finished', wav_data=wav.tolist(),
                                         pageNum=data['pageNum'])
                        client.write_message(event)
                        self.logger.info(
                            '{}<tclient <{}>>{}: Writing back wave data to client, {} samples in total.'.format(
                                Color['info'], client.id, Color['end'], len(wav)))
                        client.priority += len(wav) / options['sample_rate']
                        # TODO: whether EOS check?? num_done == num_total
                        if client.num_doing + client.num_waits == 0 and client.status == Status.EOS_RECEIVED:
                            self.logger.info(f"正在工作中的:{client.num_doing},正在等待中的:{client.num_waits},已经处理完的:{client.num_done},客户端请求状态：{client.status}")
                            client.close()
                    except Exception as e:
                        print(e)
                        self.logger.warning(
                            '{}<tclient <{}>>{}: Can\'t write back message to client, maybe it has closed'.format(
                                Color['warning'], client.id, Color['end']))

            self.application.free_tgpus.add(self)
            free_tgpus = tuple(self.application.free_tgpus)
            for tgpu_handler in free_tgpus:
                clients, txts = self.application.get_tasks(tgpu_handler.spkid, top_n=TOP_N)
                # server log message
                logmsg = ''.join(
                    ['<tclient <{}>> <idx{}> : {}\n'.format(client[0].id, client[1], txt) for client, txt in
                     zip(clients, txts)])
                self.application.logger.debug(
                    'Select a serial of tasks for speaker({}) to deal with:\n{}'.format(tgpu_handler.spkid, logmsg))
                if len(clients) != 0:
                    self.application.free_tgpus.discard(tgpu_handler)
                    try:
                        # server to tgpu
                        tgpu_handler.write_message(json.dumps(txts))
                        tgpu_handler.await_clients = clients
                        tgpu_handler.status = Status.PROCESSING
                    except Exception as e:
                        self.logger.error(
                            '{}<tgpu <{}>>{}: Can\'t forward message to the TGPU worker, maybe it has closed'.format(
                                color['error'], tgpu_handler.id, color['end']))

        else:
            self.logger.error(
                '{}<tgpu <{}>>{}: status doesn\'t match <{}>'.format(Color['error'], self.id, Color['end'],
                                                                     self.status))
            raise Exception('status doesn\'t match')

    def on_close(self):
        self.application.free_tgpus.discard(self)
        if self.spkid in self.application.tgpus:
            self.application.tgpus[self.spkid] -= 1
            if self.application.tgpus[self.spkid] == 0:
                self.application.tgpus.pop(self.spkid)
        self.await_clients = None
        self.logger.info(
            '{}<tgpu <{}>>{}: TGPU worker leaving, speaker({})'.format(Color['info'], self.id, Color['end'],
                                                                       self.spkid))
        self.logger.info(self.application.server_status())
