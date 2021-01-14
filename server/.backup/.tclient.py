import argparse
from ws4py.client.threadedclient import WebSocketClient
import ws4py.messaging
import time, json, _thread
order = 1
class MiniClient(WebSocketClient):
    def __init__(self, url, protocols=None, extensions=None, heartbeat_freq=None):
        super(MiniClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.time = time.time()
        global order
        self.id = order
        self.wid = 0
        order += 1
        self.wtime = 0
        self.first = False

    def send_data(self, data):
        self.send(data)

    def opened(self):
        self.time = time.time()

    def received_message(self, msg):
        # print(type(msg))
        if isinstance(msg, ws4py.messaging.TextMessage):
            msg = json.loads(msg.data.decode('utf-8'))
            if type(msg) != list:
                return
            self.wid += 1
            print('<client {}>: {}'.format(self.id, self.wid))
            self.wtime += len(msg)/16000
            print('\tlen of data: {}s'.format(round(self.wtime, 3)))
            if not self.first:
                self.first = True
                print('\ttime wait: {}s'.format(round(time.time()-self.time, 3)))
                self.time = time.time()
            else:
                print('\ttime cost: {}s'.format(round(time.time()-self.time, 3)))
            # self.time = time.time()

def mainloop(args):
    ws = MiniClient(args.url)
    ws.connect()
    for _ in range(args.times):
        ws.send_data('向香港特别行政区同胞澳门和台湾同胞海外侨胞')
        ws.send_data('致以诚挚的问候和良好的祝愿')
        ws.send_data('是中国发展历史上非常重要的很不平凡的一年')
        ws.send_data('向香港特别行政区同胞澳门和台湾同胞海外侨胞')
        ws.send_data('致以诚挚的问候和良好的祝愿')
        ws.send_data('是中国发展历史上非常重要的很不平凡的一年')
        ws.send_data('向香港特别行政区同胞澳门和台湾同胞海外侨胞')
        ws.send_data('致以诚挚的问候和良好的祝愿')
        ws.send_data('是中国发展历史上非常重要的很不平凡的一年')
        ws.send_data('<eos>')
        ws.send_data('致以诚挚的问候和良好的祝愿')

def main():
    parser = argparse.ArgumentParser(description='Command line client for merlin')
    parser.add_argument('-u', '--url', default='ws://localhost:8080/tclient', dest='url', help='server websocket URL')

    parser.add_argument('-f', '--fork', default=1, dest='fork', type=int)
    parser.add_argument('-t', '--times', default=1, dest='times', type=int)

    args = parser.parse_args()
    for _ in range(args.fork):
        _thread.start_new_thread(mainloop, (args,))
    while True:
        time.sleep(3)

if __name__ == '__main__':
    main()
