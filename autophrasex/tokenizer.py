import abc
import logging
import os

import jieba
from LAC import LAC

from . import utils

try:
    import opencc
    converter = opencc.OpenCC('t2s.json')
except ImportError:
    converter = None


class AbstractTokenizer(abc.ABC):

    def tokenize(self, text, **kwargs):
        raise NotImplementedError()

    def _uniform_text(self, text, **kwargs):
        to_simplified = kwargs.get('to_simplified', True)
        to_lower = kwargs.get('to_lower', True)
        to_half = kwargs.get('to_half', True)
        if to_simplified:
            text = self._traditional_to_simplified(text)
        if to_half:
            text = self._full_width_to_half(text)
        if to_lower:
            text = self._to_lower(text)
        return text

    def _traditional_to_simplified(self, text):
        text = converter.convert(text)
        return text

    def _to_lower(self, text):
        text = text.lower()
        return text

    def _full_width_to_half(self, text):
        text = "".join(utils.Q2B(x) for x in text)
        return text


class BaiduLacTokenizer(AbstractTokenizer):

    def __init__(self, custom_vocab_path=None, model_path=None, mode='seg', use_cuda=False, **kwargs):
        """Initialize LAC.

        Args:
            custom_vocab_path: Path to customize vocabulary file for LAC
            model_path: Path of custom lac model. Optional.
            mode: Mode of LAC, one of ['seg', 'lac']
            use_cuda: Boolean, use GPU or not
        """
        self.lac = LAC(model_path=model_path, mode=mode, use_cuda=use_cuda)
        logging.info('LAC initialized successfully.')
        if custom_vocab_path:
            self.lac.load_customization(custom_vocab_path)
            logging.info('LAC load custom vocab successfully.')

    def tokenize(self, text, **kwargs):
        text = self._uniform_text(text, **kwargs)
        results = self.lac.run(text)
        results = [x.strip() for x in results if x.strip()]
        return results


class JiebaTokenizer(AbstractTokenizer):

    def __init__(self, custom_vocab_path=None):
        if custom_vocab_path:
            with open(custom_vocab_path, mode='rt', encoding='utf8') as fin:
                jieba.load_userdict(fin)
                logging.info('Load user dict: %s successfully.', custom_vocab_path)
        jieba.initialize()

    def tokenize(self, text, **kwargs):
        text = self._uniform_text(text)
        result = jieba.lcut(text, cut_all=kwargs.get('cut_all', False), HMM=kwargs.get('HMM', True))
        result = [x.strip() for x in result if x.strip()]
        return result


class DefaultTokenizer(AbstractTokenizer):
    def tokenize(self, text, **kwargs):
        return text.split()