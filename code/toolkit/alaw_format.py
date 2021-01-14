import numpy as np

A = 87.6
def initialize(a):
    A = a

def linear2alaw(wav, integer=True):
    if not isinstance(wav, np.ndarray):
        if isinstance(wav[0], int):
            wav = np.array(wav, dtype=np.int16)
        else:
            wav = np.array(wav, dtype=np.float16)
    if wav.dtype == np.int16:
        wav = wav.astype(np.float16) / (2**15-1)
    indices = np.abs(wav) < 1 / A
    wav[indices] = np.sign(wav[indices]) * (A * np.abs(wav[indices])) / (1 + np.log(A))


    indices = 1 / A <= np.abs(wav)
    wav[indices] = np.sign(wav[indices]) * (1 + np.log(A * np.abs(wav[indices]))) / (1 + np.log(A))

    if integer:
        wav = (wav * (2**7-1)).astype(np.int8)

    return wav

def alaw2linear(wav, integer=True):
    if not isinstance(wav, np.ndarray):
        if isinstance(wav[0], int):
            wav = np.array(wav, dtype=np.int8)
        else:
            wav = np.array(wav, dtype=np.float16)
    if wav.dtype == np.int8:
        wav = wav.astype(np.float16) / (2**7-1)
    indices = np.abs(wav) < 1 / (1 + np.log(A))
    wav[indices] = np.sign(wav[indices]) * (np.abs(wav[indices]) * (1 + np.log(A))) / A


    indices = 1 / (1 + np.log(A)) <= np.abs(wav)
    wav[indices] = np.sign(wav[indices]) * (np.exp(np.abs(wav[indices]) * (1 + np.log(A)) - 1)) / A

    if integer:
        wav = (wav * (2**15-1)).astype(np.int16)

    return wav
