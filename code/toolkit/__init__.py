import re
from .biandiao_toolkit import start_biandiao
get_syllable = lambda text: start_biandiao(text)[1].split()
from .textnormal import text_normalization
text_normalize = lambda text: re.sub('\s', '', text_normalization(text))
from .monitor import split_synth
from .monitor import initialize as split_init
from .alaw_format import initialize as alaw_init
from .alaw_format import linear2alaw, alaw2linear
