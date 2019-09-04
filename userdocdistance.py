import pandas as pd
from numpy import dot
from numpy.linalg import norm
import numpy as np
import pickle

def cos_sim(A, B):
       return dot(A, B)/(norm(A)*norm(B))

# 인자로 resultdoctor와 user의각전문분야별유사도를 받아서
# 각 doctor들과의 유사도를 구하여
# sorting한 뒤 dictionary{doctorid:유사도} 형식으로 return
def computedistance(userresult, userregion):
    # 각 의사들의 전문도를 불러오는 부분
    # wdoc = pd.read_csv('wdoc.csv', index_col='id')
    with open('wdoc.pickle', 'rb') as f:
        wdoc = pickle.load(f)

    # user의 지역에 해당하는 의사만 가져옴
    if int(userregion) != 0:
        wdoc = wdoc[wdoc['region'] == int(userregion)]

    wdoc['sim'] = [sum(np.array(weight[:7], dtype='float64')*np.array(userresult, dtype='float64'))
                        for weight in wdoc['weighted']]

    # 이걸 pandas에 붙이고 이 행을 기준으로 해서 특정 값 이하인 doctor들은 쳐내기
    resultdoctor = wdoc[wdoc['sim'] > 0.5]
    resultdoctor = resultdoctor

    # weighted를 기준으로 sorting
    resultdoctor.sort_values(by='sim', ascending=False, inplace=True)

    return resultdoctor


def getdoctor(doctoridlist):
    # 각 의사들의 전문도를 불러오는 부분
    # wdoc = pd.read_csv('wdoc.csv', index_col='id')
    with open('wdoc.pickle', 'rb') as f:
        wdoc = pickle.load(f)

    # user의 지역에 해당하는 의사만 가져옴

    wdoc = wdoc.loc[doctoridlist]

    wdoc['sim'] = [np.array(weight[:7], dtype='float64') for weight in wdoc['weighted']]

    # 이걸 pandas에 붙이고 이 행을 기준으로 해서 특정 값 이하인 doctor들은 쳐내기
    resultdoctor = wdoc

    return resultdoctor
