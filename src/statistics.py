from nltk.tokenize import sent_tokenize
import numpy as np
import matplotlib.pyplot as plt

class Statistics:
    def __init__(self, data):
        self.data = data

    def get_no_data(self):
        return len(self.data)

    def get_no_sentence(self):
        no_sentence = 0
        for d in self.data:
            no_sentence += len(sent_tokenize(d['comment_text']))
        return no_sentence

    def get_no_words(self):
        no_comment_words = 0
        no_code_words = 0
        for d in self.data:
            no_comment_words += len(d['comment_tokens'])
            no_code_words += len(d['method_tokens'])
        return {'code':no_code_words, 'comment':no_comment_words}

    def get_no_types(self):
        type_set_code = set()
        type_set_comment = set()
        for d in self.data:
            for token in d['comment_tokens']:
                type_set_comment.add(token)
            for token in d['method_tokens']:
                type_set_code.add(token)
        return {'code':len(type_set_code), 'comment':len(type_set_comment)}

    def get_histogram(self,no_columns, code=False):
        if code:
            lang = 'method_tokens'
        else:
            lang = 'comment_tokens'
        type_dic = dict()
        for d in self.data:
            for token in d[lang]:
                if token in type_dic:
                    type_dic[token] += 1
                else:
                    type_dic[token] = 0

        labels, values = zip(*type_dic.items())
        # sort your values in descending order
        indSort = np.argsort(values)[::-1]

        # rearrange your data
        labels = np.array(labels)[indSort]
        values = np.array(values)[indSort]
        labels = labels[:no_columns]
        values = values[:no_columns]

        indexes = np.arange(len(labels))

        bar_width = 0.35

        plt.bar(indexes, values)

        # add labels
        plt.xticks(indexes + bar_width, labels)
        plt.show()