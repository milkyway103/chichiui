import torch
import torch.nn as nn
import torch.nn.functional as F
from torchtext.data import Field, BucketIterator, TabularDataset
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import sys
from konlpy.tag import Komoran
import re
import dill

tagger = Komoran()
tagger = tagger.morphs

REVIEW = Field(use_vocab=True, lower=True,  # init_token="<s>", eos_token="</s>",
               include_lengths=True, batch_first=True)

with open("data/REVIEW.Field", "rb")as f:
    REVIEW = dill.load(f)

V = len(REVIEW.vocab)
D = 50
H = 128
H_f = 20 * 7
num_of_classes = 7
da = 100  # 50차원으로 줄임.
r = 5  # 5개의 attention 부분을 찾는다.
num_layers = 1
num_directions = 2
bidirec = True
batch_size = 32
LR = 0.005
STEP = 20

model_path = 'model_attn/Comb_bytitle_cut_Komoran_class7_DropOut.model'

USE_CUDA = torch.cuda.is_available()
DEVICE = 0 if USE_CUDA else -1
batch_size = 32
sys.maxsize = 922337203


class bidirec_LSTM(nn.Module):
    def __init__(self, V, dim, H, H_f, num_of_classes,
                 da, r, num_layers=3, bidirec=False, use_cuda=False):
        """
        V: input_size = vocab_size
        dim: embedding_size
        H: hidden_size of LSTM
        H_f: hidden_size of FC
        num_of_classes (fully-connected)
        da: attenion_dimension (hyperparameter)
        r: keywords (different parts to be extracted from the sentence)
        """
        super().__init__()

        self.Tag = ["치과교정과", "치과보철과", "치과보존과", "치주과", "구강악안면외과",
                    "구강내과", "소아치과", "구강병리과", "예방치과", "예방치의학과", "장애인치과"]
        self.r = r
        self.da = da
        self.hidden_size = H
        self.num_layers = num_layers
        self.USE_CUDA = use_cuda

        if bidirec:
            self.num_directions = 2
        else:
            self.num_directions = 1

        # V개의 vocab을 dim차원으로 표현
        self.emb = nn.Embedding(V, dim)

        # dim차원을 입력으로 받음. / batch_first - input: (batch, n, dim)
        # bidirec : Bi-LSTM 여부
        self.lstm = nn.LSTM(dim, H, num_layers,
                            batch_first=True, bidirectional=bidirec)

        # Attention Weights1 / input : (batch, n, 2H )
        self.attn_W1 = nn.Linear(self.num_directions * H, self.da, bias=False)
        self.tanh = nn.Tanh()

        # Attention Weights2 / input : (batch, n, da)
        self.attn_W2 = nn.Linear(self.da, self.r, bias=False)

        # input : (batch, n, r) 따라서 r에 softmax 적용.
        self.sftmax = nn.Softmax(dim=2)

        # M = AH : r x 2H

        self.fc = nn.Sequential(
            nn.Linear(r * H * self.num_directions, H_f),
            nn.ReLU(),
            # nn.BatchNorm1d(H_f),
            nn.Dropout(0.5),
            nn.Linear(H_f, num_of_classes),
        )

    def init_LSTM(self, batch_size):

        # (num_layers * num_directions, batch_size, hidden_size)
        hidden = torch.zeros(self.num_layers * self.num_directions,
                             batch_size, self.hidden_size,
                             requires_grad=True)
        cell = torch.zeros(self.num_layers * self.num_directions,
                           batch_size, self.hidden_size,
                           requires_grad=True)
        if self.USE_CUDA:
            hidden = hidden.cuda()
            cell = cell.cuda()
        return hidden, cell

    def penalization_term(self, A):
        # AxA_T : (batch_size, r, n) x (batch_size, n , r)
        # eye : batch size x r x r (AA_T size)로 확장
        eye = torch.eye(self.r, requires_grad=True).expand(A.size(0),
                                                           self.r, self.r)  # B, r, r
        if self.USE_CUDA:
            eye = eye.cuda()

        # (batch_size, r, r)
        P = torch.bmm(A, A.transpose(1, 2)) - eye
        loss_P = ((P ** 2).sum(1).sum(1) + 1e-10) ** 0.5
        loss_P = torch.sum(loss_P) / A.size(0)
        return loss_P

    def forward(self, inputs, inputs_lengths):
        """
        inputs: batch_size, n(max_len), V
         - batch_size: batch_size
         - n: max_len
         - V: vocab_size
        inputs_lengths: length of each sentences
        """
        # (batch_size, n, V) -> (batch_size, n, dim)
        embed = self.emb(inputs)
        # initial hidden state : (num_directions, batch_size, hidden_size)
        hidden, cell = self.init_LSTM(inputs.size(0))

        # 패딩된 문장을 패킹(패딩은 연산 안들어가도록)
        packed = pack_padded_sequence(embed, inputs_lengths.tolist(), batch_first=True)

        # packed (batch_size, n, dim) -> (batch , n , 2H) < n : seq_len >
        # hidden, cell: num_directions, batch_size, hidden_size
        output, (hidden, cell) = self.lstm(packed, (hidden, cell))

        # 패킹된 문장을 다시 unpack
        # output: (batch , n , 2H) < n : Max >
        output, output_lengths = pad_packed_sequence(output, batch_first=True)

        # By Attention (batch , n , 2H) -> (batch , n , da)
        tanh_v1 = self.tanh(self.attn_W1(output))

        # (batch , n , da) -> (batch, n, r)
        score = self.attn_W2(tanh_v1)
        self.A = self.sftmax(score.transpose(1, 2))  # (batch, r, n)

        # (batch, r, n) x (batch, n, 2H)-> (batch, r, 2H)
        self.M = self.A.bmm(output)

        # Penalization Term
        loss_P = self.penalization_term(self.A)

        # view : ( batch_size , r x 2H ) -> ( batch_size , num_of_classes )

        output = self.fc(self.M.view(self.M.size(0), -1))

        return output, loss_P

    def predict(self, inputs, inputs_lengths):
        preds, _ = self.forward(inputs, inputs_lengths)
        return F.softmax(preds, dim=1).argmax(dim=1)

    def showProb(self, inputText):
        self.eval()
        pattern = re.compile(r"[^ \n0-9A-Za-z가-힣]")
        inputText = pattern.sub("", inputText)
        # inputBag = torch.tensor([[REVIEW.vocab.stoi[key]
        #                          for key in
        #                          mecab.parse(inputText).split()[::2][:-1]]])
        inputBag = torch.tensor([[REVIEW.vocab.stoi[key]
                                  for key in
                                  tagger(inputText)]])
        lengths = torch.tensor([len(inputBag[0])])
        probs = F.softmax(self.forward(inputBag, lengths)[0], dim=1)
        # label = probs.argmax(dim = 1)

        dic = {}
        for tag, prob in zip(self.Tag, probs.tolist()[0]):
            dic[tag] = prob
        return dic


# Load model
model = bidirec_LSTM(V, D, H, H_f, num_of_classes, da, r, num_layers=num_layers, bidirec=bidirec, use_cuda=USE_CUDA)
if USE_CUDA:
    model = model.cuda()
    model.load_state_dict(torch.load(model_path))
else:
    model.load_state_dict(torch.load(model_path, map_location='cpu'))

def predicttorch(inputText):
    inputText = inputText
    model.cpu()
    model.eval()
    return model.showProb(inputText)