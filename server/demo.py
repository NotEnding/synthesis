# -- encoding : utf-8 --
'''
## 需要安装的几个包
名字      作用
ws4py     socket通信
scipy     保存音频
numpy     数据转换
'''
from ws4py.client.threadedclient import WebSocketClient
import ws4py.messaging
import time, json
import numpy as np
import argparse
from config import options, CODE_PATH
import sys
sys.path.append(CODE_PATH)
if options['wavform'] == 'alaw':
    from toolkit import alaw_init, alaw2linear
    alaw_init(options['alaw_A'])

class MiniClient(WebSocketClient):
    def __init__(self, url, protocols=None, extensions=None, heartbeat_freq=None):
        super(MiniClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.data = []

    def received_message(self, msg):
        # 二进制数据流是音频数据点，将接收到的数据加上文件头保存下来即可。
        if isinstance(msg, ws4py.messaging.BinaryMessage):
            ## 这里我将数据保存下来，
            ## 此处可以自行加相应的操作将音频播放出来，
            ## 音频数据是int16，单声道，8kHz采样率。
            if options['wavform'] == 'alaw':
                wav = np.fromstring(msg.data, dtype=np.int8)
            elif options['wavform'] == 'linear':
                wav = np.fromstring(msg.data, dtype=np.int16)
            self.data.extend(wav.tolist())
        # 服务器状态信息，比如工作端服务状态已满，无法再服务当前客户端等。
        # 解析后是一个dict。
        elif isinstance(msg, ws4py.messaging.TextMessage):
            msg = json.loads(msg.data.decode('utf-8'))

            if type(msg) == dict:
                print(msg)

if __name__ == '__main__':
    # 发送需要合成的文本数据，可以多句，但需要以中文逗号作为分割符
    # 单独发一个结束标记<eos>，意味着不再发送数据，建议在发送结束后发送
    # 如果合成结束仍没有接收到需要合成的文本，服务器会自动断开连接，
    # 建议在接受完整数据后自动断开与服务器的连接
    text = '发送需要合成的文本，需要以中文逗号作为分割符'
    # text = '空军五项飞行比赛，中国队以总分第一的成绩，将空军五项的首块金牌收入囊中，这是中国队在本届军运会上获得的第二金。在低空三角导航飞行比赛中，中国选手廖伟华以3500分的成绩摘得金牌获冠军。'

    ## 命令行参数配置
    parser = argparse.ArgumentParser(description='only for demo')
    # 访问链接
    parser.add_argument('-u', '--url', default='ws://localhost:{}/tclient', dest='url', help='url to link the server')
    parser.add_argument('-p', '--port', default=str(options['port']), dest='port', help='the port to be connnected, only activate when "{}" in url option')
    # 合成文本
    parser.add_argument('-t', '--text', default=text, dest='text', help='text to be synthesized')
    parser.add_argument('-s', '--speaker', default='person_1', dest='speaker', help='which speaker to use.')
    args = parser.parse_args()
    args.url = args.url.format(args.port) if '{}' in args.url else args.url

    try:
        # 尝试连接服务器
        ws = MiniClient(args.url)
        ws.connect()

        event = dict(spkid=args.speaker, text=args.text)
        ws.send(json.dumps(event))
        # ws.send(json.dumps(event))
        # ws.send(json.dumps(event))
        ws.send('<eos>')

        while not ws.client_terminated:
            time.sleep(0.5)

        # 相应的数据(采样率8kHz)
        print('音频的时长: {}s'.format(len(ws.data) / options['sample_rate']))

        ## 如果需要保存音频供试听，可以通过如下代码保存
        import scipy.io.wavfile as wf
        if options['wavform'] == 'linear':
            norm_data = np.array(ws.data, dtype=np.int16)
        elif options['wavform'] == 'alaw':
            norm_data = np.array(alaw2linear(ws.data), dtype=np.int8)
        wf.write('test.wav', rate=options['sample_rate'], data=norm_data)
    except Exception as e:
        print(e)

    finally:
        ws.close()
