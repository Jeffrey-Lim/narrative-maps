from nltk.tokenize import word_tokenize
import pandas as pd
import numpy as np
import shap
import os
import shutil
import subprocess

#from sts_models.psbert_model import PSBertModel
#from sts_models.sbert_model import SBertModel
#from sts_models.bertscore_model import BertScoreModel
from packages.minilm_model import MiniLMModel

class STSWrapper():
    def __init__(self, sts_model, tokenizer='nltk', MAX_LENGTH=30):
        self.sts_model = sts_model
        self.tokenizer_model = tokenizer
        self.MAX_LENGTH = MAX_LENGTH

    def tokenizer(self, sent):
        if self.tokenizer_model == 'nltk': tokenizer = word_tokenize
        elif self.tokenizer_model == 'split': tokenizer = self._split_tokenizer

        tokens = tokenizer(sent)
        if len(tokens) > self.MAX_LENGTH:
            tokens = tokens[:self.MAX_LENGTH]
        return tokens


    def _split_tokenizer(self, sent):
        return sent.split()

    def __call__(self, sent_pair_list):
        batch = []
        for pair in sent_pair_list:
            s1,s2 = pair[0].split('[SEP]')
            batch.append( (s1,s2) )

        scores = self.sts_model(batch)
        return scores

    def _tokenize_sent(self, sentence):
        if isinstance(sentence,str):
            #token_ids = self.sts_model.tokenizer.encode(sentence)
            #tokens = self.sts_model.tokenizer.convert_ids_to_tokens(token_ids)[1:-1]
            tokens = self.tokenizer(sentence)
        elif isinstance(sentence, list):
            tokens = sentence

        return tokens

    def build_feature(self, sent1, sent2):
        tokens1 = self._tokenize_sent(sent1)
        tokens2 = self._tokenize_sent(sent2)
        self.s1len = len(tokens1)
        self.s2len = len(tokens2)

        tdict = {}
        for i in range(len(tokens1)):
            tdict['s1_{}'.format(i)] = tokens1[i]
        for i in range(len(tokens2)):
            tdict['s2_{}'.format(i)] = tokens2[i]

        return pd.DataFrame(tdict, index=[0])

    def mask_model(self, mask, x):
        tokens = []
        for mm, tt in zip(mask, x):
            if mm: tokens.append(tt)
            else: tokens.append('[MASK]')
        s1 = ' '.join(tokens[:self.s1len])
        s2 = ' '.join(tokens[self.s1len:])
        sentence_pair = pd.DataFrame([s1+'[SEP]'+s2])
        return sentence_pair



class ExplainableSTS():
    def __init__(self, wanted_sts_model, MAX_LENGTH=30):
        if wanted_sts_model == 'sbert':
            sts_model = SBertModel()
        elif wanted_sts_model == 'pair-bert':
            sts_model = PSBertModel()
        elif wanted_sts_model == 'bert-score':
            sts_model = BertScoreModel()
        elif wanted_sts_model == 'minilm':
            sts_model = MiniLMModel()

        self.wrapper = STSWrapper(sts_model, MAX_LENGTH=MAX_LENGTH)

    def __call__(self, sent1, sent2, MAX_LENGTH=30):
        t_s1 = self.wrapper.tokenizer(sent1)
        t_s2 = self.wrapper.tokenizer(sent2)
        s1 = ' '.join(t_s1)
        s2 = ' '.join(t_s2)
        return self.wrapper.sts_model([(s1, s2)])[0]

    def explain(self, sent1, sent2):
        explainer = shap.Explainer(self.wrapper, self.wrapper.mask_model, new_base_value=0.5, algorithm="permutation", seed=42, max_evals=500)
        features = self.wrapper.build_feature(sent1, sent2)
        value = explainer(features)
        return value, features









