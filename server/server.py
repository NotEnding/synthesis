from tornado import httpserver
from config import options
from tornado.ioloop import IOLoop
from app.server import ServerApp
import re, argparse, os
from logplot import log_preparation

def log_init(cfg, logfile):
    conf = dict()
    with open(cfg, 'r') as fid:
        # fid.readline()
        for line in fid:
            l = re.split('\s+', line.strip())
            assert len(l) >= 2
            name, logname = l[:2]
            level = l[2] if len(l) > 2 else 'INFO'
            conf[name] = (logname, level)
    log_preparation(conf.values(), logfile)
    return conf

def main():
    parser = argparse.ArgumentParser(description='parameter for server')
    parser.add_argument('--conf', '-c', default='logging.conf', help='configuration file for logging')
    parser.add_argument('--logfile', '-l', default='logdir/server.log', help='where to store the log information')
    parser.add_argument('--port', '-p', default=None, help='the port for server')

    args = parser.parse_args()
    os.makedirs(os.path.dirname(args.logfile), exist_ok=True)
    conf = log_init(args.conf, args.logfile)
    app = ServerApp(conf)
    server = httpserver.HTTPServer(app)
    port = args.port if args.port is not None else options['port']
    server.listen(port)

    IOLoop.current().start()

if __name__ == '__main__':
    main()
