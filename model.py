from tensorflow.python.keras.backend import set_session
from tensorflow.python.keras.preprocessing import sequence
import numpy as np
from string import punctuation
import re



cnnmodel = 0
okt = 0
graph = 0
word_index = 0
sess = 0


pattern1 = re.compile(r"[{0}]".format(re.escape(punctuation)))
pattern2 = re.compile(r"[^ \nA-Za-z가-힣]")
pattern3 = re.compile(r"\s{2,}")
#cnnmodel = keras.models.load_model('C:\\Users\\legen\\Desktop\\HwanEui\\BIGDATA\\PROJECT\\CODE\\Front_Backend\\test\\10000_all_CNN_NaverKin.h5','r')

#cnnmodel._make_predict_function()

pad_id = 0
oov_id = 1
index_offset = 1

def initmodel():
    predictmodel = modelinit()
    return predictmodel

class modelinit():
    def __init__(self):
        import tensorflow as tf
        from konlpy.tag import Okt
        from tensorflow import keras
        global sess
        global cnnmodel
        global graph
        global okt
        global word_index

        sess = tf.Session()
        set_session(sess)
        cnnmodel = keras.models.load_model('model/cnn.h5')
        graph = tf.get_default_graph()
        okt = Okt()
        word_dict = {}
        wordfile = open("model/word_counter2.txt", "r", encoding="UTF8")
        lines = wordfile.readline()
        word = lines.split(" ")[:-1]
        for _ in word:
            words = _.split(":")
            word_dict[words[0]] = int(words[1])

        temp = sorted(word_dict.items(), key=lambda t: t[1], reverse=True)

        vocab = {
            '<PAD>': pad_id,
            '<OOV>': oov_id
        }
        for i, (word, cnt) in enumerate(temp, start=index_offset + 1):
            vocab[(word)] = i

        word_index = vocab

    def text_to_index(self,text):
        text = pattern3.sub(" ", pattern2.sub(" ", pattern1.sub("", text))).strip()
        indexes = []
        for token in [kk[0] for kk in okt.pos(text, norm=True, stem=True)]:
            if token in word_index:
                indexes.append(word_index[token])
            else:
                indexes.append(oov_id)
        return indexes

    def labelingName(self, num):
        if num == 0:
            return "치과교정과"
        elif num == 1:
            return "치과보철과"
        elif num == 2:
            return "치과보존과"
        elif num == 3:
            return "치주과"
        elif num == 4:
            return "구강악안면외과"
        elif num == 5:
            return "구강내과"
        elif num == 6:
            return "소아치과"

    def predict(self, query_sentence):
        sentence_size = 1000
        query = query_sentence
        query_variable = [self.text_to_index(query_sentence)]
        query_padded = sequence.pad_sequences(query_variable,  ## sequence.pad~ 함수가 자동 nd.array로 변경
                                              maxlen=sentence_size,
                                              truncating='post',
                                              padding='post',
                                              value=pad_id)
        to_be_embedded_query = np.expand_dims(query_padded[0], axis=0)
        result_list = []
        with graph.as_default():
            set_session(sess)
            for label, prob in enumerate(cnnmodel.predict(to_be_embedded_query)[0]):
                result_list.append([label, prob])

        # result_list = sorted(result_list, key=lambda x: x[1], reverse=True)
        # return [(self.labelingName(_[0]),_[1]) for _ in result_list]
        dict_ = {}
        [dict_.update({self.labelingName(_[0]): _[1]}) for _ in result_list]
        return dict_

