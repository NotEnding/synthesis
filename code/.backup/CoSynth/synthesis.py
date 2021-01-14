import os, time
import sys, logging
import itertools
import pandas as pd
from pypinyin import pinyin, Style
import numpy as np
from scipy import signal
import tensorflow as tf
from tacotron.models import create_model
from tacotron.utils.text import text_to_sequence
from hparams import hparams
cleaner_names = [x.strip() for x in hparams.cleaners.split(',')]
from infolog import log
from toolkit import get_syllable, split_synth, split_init
from librosa import util
import torch
from apex import amp

## some configuration for hparams
def hparams_deal():
    hparams.win_size = hparams.n_fft if hparams.win_size is None else hparams.win_size
    hparams.hop_size = int(hparams.win_size / 4) if hparams.hop_size is None else hparams.hop_size
hparams_deal()

## prosody net embedding word2id
def get_word2id(words_ids_file):
    df_words_ids = pd.read_csv(filepath_or_buffer=words_ids_file,
                               encoding='utf-8')
    id2word = pd.Series(index=df_words_ids['id'].values,
                          data=df_words_ids['words'].values)
    word2id = pd.Series(index=df_words_ids['words'].values,
                          data=df_words_ids['id'].values)
    return word2id, id2word

## get the real prosody according to the prosody net prediction
def prosody_result(res_pw, res_pph, res_iph, len_x=None):
    assert len(res_pw) == len(res_pph) == len(res_iph)
    comp = np.array([res_iph, res_pph, res_pw])
    args = np.argmax(comp, axis=0)
    result = list()
    len_x = len(res_pw) if len_x is None else len_x
    for idx in range(len_x):
        if comp[args[idx], idx] == 2:
            result.append(hparams.PROSODY_MARKER[3 - args[idx]])
        else:
            result.append(hparams.PROSODY_MARKER[0])
    return result

## get the tacotron input(index of symbols)
def get_taco_input(txt, prosodies, pflag=True):
    syllables = get_syllable(txt)
    if not pflag:
        ## nr
        text = ' '.join(syllables)
    else:
        ## normal
        text = ''.join(itertools.chain.from_iterable(zip(syllables, prosodies)))# + '&'
    return np.asarray(text_to_sequence(text, cleaner_names))

## for tacotron padding
def taco_pad(x, length):
    return np.pad(x, (0, length - x.shape[0]), mode='constant', constant_values = hparams.TACO_PAD)

def smooth(wavs):
    window = signal.get_window('hamming', hparams.smooth_window_size, fftbins=False)
    for wav in wavs:
        if len(wav) < hparams.smooth_window_size:
            continue
        wav[:hparams.smooth_window_size//2] = (wav[:hparams.smooth_window_size//2].astype(np.float64) * window[:hparams.smooth_window_size//2]).astype(np.int16)
        wav[-hparams.smooth_window_size//2:] = (wav[-hparams.smooth_window_size//2:].astype(np.float64) * window[hparams.smooth_window_size//2:]).astype(np.int16)
    return wavs

def wav_normalize(wavs):
    res_wavs = []
    for wav in wavs:
        if len(wav) == 0:
            res_wavs.append(wav)
        else:
            # res_wavs.append((wav / np.max(wav) * (2**15-1)).astype(np.int16))
            res_wavs.append((util.normalize(wav, norm=np.inf, axis=None) * (2**15-1)).astype(np.int16))
    return res_wavs

## define a structure for the whole program
class Synth(object):
    def __init__(self, words_ids_file, prosody_model_file, tacotron_model_file, waveglow_model_file, unit_dir):
        self._words_ids_file = words_ids_file
        self._prosody_model_file = prosody_model_file
        self._tacotron_model_file = tacotron_model_file
        self._waveglow_model_file = waveglow_model_file
        self._unit_dir = unit_dir

        split_init(self._unit_dir)
        if os.path.exists(self._words_ids_file):
            self.word2id, self.id2word = get_word2id(self._words_ids_file)
            self._prosody_flag = True
        else:
            self._prosody_flag = False

        ## graph
        self.graph = tf.Graph()
        with self.graph.as_default():
            if self._prosody_flag:
                ## prosody model
                saver = tf.train.import_meta_graph(
                    meta_graph_or_file='{}.meta'.format(self._prosody_model_file),
                    clear_devices=True)

                self.X_p = self.graph.get_operation_by_name('Prosody_model/input_placeholder').outputs[0]
                self.seq_len_p = self.graph.get_operation_by_name('Prosody_model/seq_len').outputs[0]
                self.pred_pw = self.graph.get_operation_by_name('Prosody_model/pred_pw').outputs[0]
                self.pred_pph = self.graph.get_operation_by_name('Prosody_model/pred_pph').outputs[0]
                self.pred_iph = self.graph.get_operation_by_name('Prosody_model/pred_iph').outputs[0]

            ## tacotron_model
            with tf.variable_scope('Tacotron_model') as scope:
                self.inputs = tf.placeholder(tf.int32, (None, None),
                                        name='inputs')
                self.input_lengths = tf.placeholder(tf.int32, (None),
                                               name='input_lengths')
                taco_model = create_model('Tacotron', hparams=hparams)
                taco_model.initialize(self.inputs, self.input_lengths)

            self.mel_outputs = taco_model.mel_outputs
            self.stop_token_prediction = taco_model.stop_token_prediction

            init = tf.global_variables_initializer()
            variables = tf.global_variables()
            log('********** Graph Finished! **********')

        ## session
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.Session(graph=self.graph, config=config)
        self.sess.run(init)
        if self._prosody_flag:
            log('********** Restoring Prosody Model! **********')
            log('Prosody Model: {}'.format(self._prosody_model_file))
            prosody_variables = [var for var in variables if 'Prosody_model' in var.name]
            saver = tf.train.Saver(prosody_variables)
            saver.restore(self.sess, self._prosody_model_file)
        log('********** Restoring Tacotron Model! **********')
        log('Tacotron Model: {}'.format(self._tacotron_model_file))
        tacotron_variables = [var for var in variables if 'Tacotron_model' in var.name]
        saver = tf.train.Saver(tacotron_variables)
        saver.restore(self.sess, self._tacotron_model_file)

        # waveglow
        log('********** Restoring Waveglow Model! **********')
        log('Waveglow Model: {}'.format(self._waveglow_model_file))
        self.waveglow = torch.load(self._waveglow_model_file)
        self.waveglow = self.waveglow.remove_weightnorm(self.waveglow)
        self.waveglow.cuda().eval()
        self.waveglow, _ = amp.initialize(self.waveglow, [], opt_level="O3")
        log('********** Loaded Model Correctly! **********')

    def synth(self, txts, logger='Synth'):
        logger = logging.getLogger(logger) if isinstance(logger, str) else logger
        start = time.time()

        texts, pwavs = list(), list()
        parts = list()
        for txt in txts:
            mtexts, nwavs = split_synth(txt, logger)
            texts.extend(mtexts)
            pwavs.append(nwavs)
            parts.append(len(mtexts))

        X = list()
        mwavs = list()
        if self._prosody_flag:
            for txt in texts:
                try:
                    X.append(list(map(lambda x: self.word2id[x], txt.strip())))
                except KeyError as e:
                    logger.warning('Synthor: There must be some non-mandarin symbols in the input text "{}"'.format(txt))
                    X.append([])
        else:
            X = texts

        if len(X) > 0:
            if self._prosody_flag:
                len_X = list(map(len, X))
                [x.extend([hparams.TEXT_PAD] * (hparams.MAX_SENTENCE_SIZE - len_x)) for x, len_x in zip(X,len_X)]

                res_pw, res_pph, res_iph = self.sess.run(fetches=[self.pred_pw, self.pred_pph, self.pred_iph],
                                                    feed_dict={self.X_p: X, self.seq_len_p: len_X})
                prosody_res = prosody_result(res_pw, res_pph, res_iph)
                prosody_res = np.array(prosody_res).reshape([-1, hparams.MAX_SENTENCE_SIZE])
                # print(prosody_res)
            else:
                prosody_res = [[]] * len(X)
                len_X = list(map(len, X))

            taco_inputs = [get_taco_input(txt, prosodies[: len_x], self._prosody_flag)
                           for txt, prosodies, len_x in zip(texts, prosody_res, len_X)]
            taco_input_lengths = [len(x) for x in taco_inputs]
            max_len = max(taco_input_lengths)
            taco_inputs = [taco_pad(x, max_len) for x in taco_inputs]

            taco_inputs = np.stack(taco_inputs)

            feed_dict = {self.inputs: taco_inputs,
                         self.input_lengths: taco_input_lengths,
                         }
            logger.debug('Synthor: prepare time used: {}s'.format(time.time()-start))
            start = time.time()
            
            mels, stps = self.sess.run(
                                    fetches=[self.mel_outputs, self.stop_token_prediction],
                                    feed_dict=feed_dict)
            # TODO mwav
            mels = mels * 4 - 12
            mels = torch.from_numpy(mels.transpose((0, 2, 1))).cuda().half()
            with torch.no_grad():
                mwavs = self.waveglow.infer(mels, sigma=0.6).cpu().numpy()

            output_lengths = [row.index(1) for row in np.round(stps).tolist()]
            if hparams.preemphasize:
                mwavs = [signal.lfilter([1], [1, -hparams.preemphasis], wav[:length*hparams.hop_size]) for wav, length in zip(mwavs, output_lengths)]
            else:
                mwavs = [wav[:length*hparams.hop_size] for wav, length in zip(mwavs, output_lengths)]
            logger.debug('Synthor: synthesis time used: {}s'.format(time.time()-start))
            start = time.time()

            mwavs = wav_normalize(mwavs)

        wavs = list()
        twav = list()
        idx = 0
        for i, num_part in enumerate(parts):
            for j in range(num_part):
                twav.extend(pwavs[i][j])
                twav.extend(mwavs[idx])
                idx += 1
            if num_part < len(pwavs[i]):
                twav.extend(pwavs[i][-1])
            wavs.append(np.array(twav, dtype=np.int16))
            twav.clear()

        # smooth
        wavs = smooth(wavs)

        # silence
        wavs = [np.concatenate([wav, np.zeros(shape=(int(hparams.interval*hparams.sample_rate),), dtype=np.int16)], axis=-1) for wav in wavs]
        return wavs

    def __del__(self):
        if hasattr(self, 'sess'):
            self.sess.close()

if __name__ == '__main__':
    BASIC_DIR = '/home/server/synthesis/server/model_data'
    prosody_model_dir = os.path.join(BASIC_DIR, 'prosody_models/')
    prosody_model_name = 'model-10000'
    prosody_model_file = os.path.join(prosody_model_dir, prosody_model_name)
    tacotron_model_dir = os.path.join(BASIC_DIR, 'tacotron_models/')
    tacotron_model_name = 'tacotron_model.ckpt-200000'
    tacotron_model_file = os.path.join(tacotron_model_dir, tacotron_model_name)
    words_ids_file = os.path.join(BASIC_DIR, 'words_ids.csv')

    synth = Synth(words_ids_file, prosody_model_file, tacotron_model_file)
    txts = ['欢迎来到昆山杜克大学大数据研究中心',
           '昆山杜克大学是中美合办的优秀学校',
           '几年来励志树立世界一流名校的旗帜',
           '去年首次获准开启本科生项目',
           '取得了不小的成绩',
           '本科入学人数达两百多余人',
           '学子品学兼优',
           '教员敬职敬业',
           '在过去的半年里',
           '共同努力将杜克大学变成一个融洽和谐的校园']
    for idx in range(1, 6):
        wavs = synth.synth(txts)
        wav = None
        for w in wavs:
            wav = np.concatenate([wav, np.zeros(int(0.3 * hparams.sample_rate)), w]) \
                    if wav is not None else w
        import librosa
        librosa.output.write_wav('wavs/{}.wav'.format(idx), wav, hparams.sample_rate)
