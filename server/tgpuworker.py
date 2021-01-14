import logging, time, os
import argparse
from config import Color, options, init_spkid

parser = argparse.ArgumentParser(description='Worker for Tacotron')
parser.add_argument('-u', '--url', default='ws://localhost:{}/tgpu', dest='url', help='url to link the server')
parser.add_argument('-p', '--port', default=str(options['port']), dest='port', help='the port to be connnected, only activate when "{}" in url option')
# parser.add_argument('-f', '--fork', default=1, dest='fork', type=int, help='the number of workers')
parser.add_argument('-l', '--logfile', default='logdir/tgpuworker.log', dest='logfile', help='where to store the log information')
parser.add_argument('-c', '--cuda', default=None, dest='cuda', help='which gpu kernel to use')
parser.add_argument('-s', '--speaker', default='person_1', dest='speaker', help='which speaker to load')

args = parser.parse_args()
if args.cuda is None:
    if 'CUDA_VISIBLE_DEVICES' in os.environ:
        args.cuda = os.environ['CUDA_VISIBLE_DEVICES']
    else:
        args.cuda = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = str(args.cuda)
args.url = args.url.format(args.port) if '{}' in args.url else args.url
init_spkid(args.speaker)

from multiprocessing import Process
from view.tgpuworker import TGPUWebSocket
import _thread
import tornado.ioloop
from logplot import log_preparation
tlevel = 'info'
conf = {'main': ('main', tlevel),
        'tgpuworker': ('tgpuworker', tlevel),
        }

def main_loop(server_url):
    logger = logging.getLogger('main')
    while True:
        ws = TGPUWebSocket(server_url, args.speaker)
        try:
            logger.info('Opening websocket connection to master server: {}<tgpu <{}>>{}'.format(Color['info'], ws.id, Color['end']))
            ws.connect()
            ws.run_forever()
        except Exception as e:
            logger.error('Couldn\'t connect to server, waiting for {} seconds: {}<tgpu <{}>>{}'.format(5, Color['error'], ws.id, Color['end']))
            time.sleep(2)
        time.sleep(1)

def multiProcess(server_url):
    # _thread.start_new_thread(tornado.ioloop.IOLoop.instance().start, ())
    main_loop(server_url)

def main():
    os.makedirs(os.path.dirname(args.logfile), exist_ok=True)
    log_preparation(conf.values(), args.logfile)
    logger = logging.getLogger('main')
    logger.debug('Starting up worker')
    _thread.start_new_thread(tornado.ioloop.IOLoop.instance().start, ())

    '''
    for i in range(args.fork):
        Process(target=multiProcess, args=(args.url,)).start()
    '''
    multiProcess(args.url)

if __name__ == '__main__':
    main()
