__author__ = 'Jiff'

import os
SERVER_PATH = os.path.dirname(__file__)
UPFILE_PATH = os.path.join(SERVER_PATH, 'upfile')
TOP_PATH = os.path.dirname(SERVER_PATH)
CODE_PATH = os.path.join(TOP_PATH, 'code')
MODEL_DATA_PATH = os.path.join(TOP_PATH, 'model_data')

global words_ids_file, graph_file, prosody_model_file, tacotron_model_file, unit_dir, waveglow_model_file

def init_spkid(spkid):
    global words_ids_file, graph_file, prosody_model_file, tacotron_model_file, unit_dir, waveglow_model_file
    words_ids_file = os.path.join(MODEL_DATA_PATH, spkid, 'words_ids.csv')
    graph_file = os.path.join(MODEL_DATA_PATH, spkid, 'frozen_graph.pb')
    prosody_model_file = os.path.join(MODEL_DATA_PATH, spkid, 'prosody_models', 'model')
    tacotron_model_file = os.path.join(MODEL_DATA_PATH, spkid, 'tacotron_models', 'tacotron_model.ckpt')
    waveglow_model_file = os.path.join(MODEL_DATA_PATH, spkid, 'waveglow')
    unit_dir = os.path.join(MODEL_DATA_PATH, spkid, 'units')

nclient_per_gpu, TOP_N = 3, 6
SplitList = '[,?!:;\'"，。？！：；‘’“”、]'

options = {
    'port' : 8080,
        'sample_rate' : 16000, # 采样率
        'wavform' : 'linear', # 目前支持两种格式，一种linear，一种alaw
        'alaw_A' : 87.6, # alaw参数A，默认为87.6
}

settings = {
    'static_path' : os.path.join(SERVER_PATH, 'static'),
    'template_path' : os.path.join(SERVER_PATH, 'templates'),
    'debug' : True, # 运行在调试模式下，开发True, 应用False
    'autoreload' : True, # 自动重启，开发True, 应用False
    'compiled_template_cache' : False, # 使用缓存编译的模板，开发False，应用True
    'static_hash_cache' : False, # 静态文件hash值缓存，开发False，应用True
    'serve_traceback' : True, # 提供追踪信息

    # 'autoescape' : None, # 关闭模板自动转义
}

from enum import Enum
Status = Enum('Status', ('CREATED',
                        'CONNECTED',
                        'INITIALIZED',
                        'PROCESSING',
                        'EOS_RECEIVED',
                        'CANCELLING',
                        'FINISHED',
                        'NOT_AVAILABLE',
                        ))
DELAY_TIMEOUT = 30
BUFFER_SIZE = 0

# color
Color = dict(debug = '\033[0;34m',
            info = '\033[0;32m',
            warning = '\033[0;33m',
            error = '\033[0;31m',
            end = '\033[0m',
            )
for key in Color:
    Color[key] = ''
