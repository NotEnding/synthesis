import os, logging, re
import librosa
# import scipy.io.wavfile as wf
import numpy as np
from hparams import hparams

def _pre_key(char):
    char = '/' if char == '斜线' else char
    char = '\\' if char == '反斜线' else char
    char = '?' if char == '问号' else char
    char = '.' if char == '点' else char
    char = ':' if char == '冒号' else char
    return char

wavs = dict()

def initialize(unit_dir):
    for file in os.listdir(unit_dir):
        if not file.endswith('.wav'):
            continue
        char = file.replace('.wav', '')
        char = _pre_key(char)
        # _, wav = wf.read(os.path.join(unit_dir, file))
        wav, _ = librosa.load(os.path.join(unit_dir, file), sr=hparams.sample_rate)
        wav = (wav * (2**15-1)).astype(np.int16)
        wavs[char] = wav

def char_synth(idx, text):
    max_len = 5
    for l in range(max_len, 0, -1):
        key = text[idx: idx+l].lower()
        if key in wavs:
            return idx+l, wavs[key]

    return idx, None

def mandarin_check(char):
    return '\u4e00' <= char <= '\u9fa5'

def license_check(idx, text):
    provinces = [k for k in wavs.keys() if mandarin_check(k)]
    if text[idx] not in provinces:
        return False
    elif len(text) < idx+2:
        return False
    elif re.match('[a-zA-Z]', text[idx+1]):
        return True
    return False

def split_synth(text, logger):
    logger = logging.getLogger(logger) if isinstance(logger, str) else logger

    mtexts, nwavs = list(), list()
    mstidx, medidx, idx = 0, 0, 0
    twav = list()
    while idx < len(text):
        if mandarin_check(text[idx]) and not license_check(idx, text):
            if len(twav) != 0:
                nwavs.append(np.concatenate(twav))
                twav.clear()
                mstidx, medidx = idx, idx
            elif idx == 0:
                nwavs.append([])
            medidx += 1
            idx += 1
        else:
            if mstidx != medidx:
                mtexts.append(text[mstidx: medidx])
                mstidx, medidx = idx, idx
            idx, wav = char_synth(idx, text)
            if wav is None:
                logger.warning('Split_synth: There exists unrecord charactor "{}" in "{}"'.format(text[idx], text))
                idx += 1
                twav.append([])
            else:
                twav.append(wav)
    if mstidx != medidx:
        mtexts.append(text[mstidx: medidx+1])
    if len(twav) != 0:
        nwavs.append(np.concatenate(twav))
    return mtexts, nwavs
