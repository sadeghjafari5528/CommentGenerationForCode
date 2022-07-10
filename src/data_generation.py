from gen.JavaParserLabeled import JavaParserLabeled
from gen.JavaParserLabeledListener import JavaParserLabeledListener
from antlr4 import *
from gen.JavaLexer import JavaLexer

import os
import json
from nltk.tokenize import sent_tokenize, word_tokenize

from config import BASE_DATA_DIR, ORIGINAL_DATA_PATHS, DATASET_PATH


class MethodDetectorListener(JavaParserLabeledListener):
    def __init__(self):
        self.methods_info = []

    def get_tokens(self, ctx):
        if ctx.getChildCount() == 0:
            return [ctx.getText()]
        tokens = []
        for child in ctx.getChildren():
            tokens += self.get_tokens(child)
        return tokens

    def get_original_text(self, ctx):
        token_source = ctx.start.getTokenSource()
        input_stream = token_source.inputStream
        start, stop = ctx.start.start, ctx.stop.stop
        return input_stream.getText(start, stop)

    def enterMethodDeclaration(self, ctx:JavaParserLabeled.MethodDeclarationContext):
        method_info = {
            "text": self.get_original_text(ctx),
            "tokens": self.get_tokens(ctx),
            "start_line": ctx.start.line
        }

        self.methods_info.append(method_info)



class DataGenerator:
    def __init__(self):
        pass

    def get_no_new_line(self, text):
        count = 0
        for char in text:
            if char == '\n':
                count += 1
        return count

    def get_cumulative_comments(self, file_address):
        file_stream = FileStream(r"" + file_address, encoding='utf8', errors='ignore')
        lexer = JavaLexer(file_stream)
        token = lexer.nextToken()

        comments_info = []
        previous_comment = None
        current_comment = None
        cumulative_comment = None
        while token.type != Token.EOF:
            if token.type == lexer.COMMENT:
                current_comment = {
                    'text': token.text[2:-2],
                    'start_line': token.line,
                    'stop_line': token.line + self.get_no_new_line(token.text)
                }

            elif token.type == lexer.LINE_COMMENT:
                current_comment = {
                    'text': token.text[2:],
                    'start_line': token.line,
                    'stop_line': token.line
                }

            if token.type == lexer.COMMENT or token.type == lexer.LINE_COMMENT:
                if previous_comment is None:
                    cumulative_comment = current_comment
                else:
                    if previous_comment['stop_line'] + 1 == current_comment['start_line']:
                        cumulative_comment['text'] += '\n' + current_comment['text']
                        cumulative_comment['stop_line'] = current_comment['stop_line']
                        #print('cumulative:', cumulative_comment)
                    else:
                        comments_info.append(cumulative_comment)
                        #print('cumulative:', cumulative_comment)
                        cumulative_comment = current_comment
                # print("-"*30)
                # print(previous_comment)
                # print(current_comment)
                previous_comment = current_comment.copy()

            token = lexer.nextToken()
        if comments_info == []:
            if cumulative_comment is not None:
                comments_info.append(cumulative_comment)
                #print('cumulative:', cumulative_comment)

        else:
            if comments_info[-1] != cumulative_comment:
                comments_info.append(cumulative_comment)
                #print('cumulative:', cumulative_comment)

        return comments_info

    def tokenize_comment(self, comment):
        tokens = []
        for s in sent_tokenize(comment):
            tokens += word_tokenize(s)
        return tokens


    def merge(self, comments, methods):
        data = []
        if len(comments) == 0 or len(methods) == 0:
            return []

        c = 0
        m = 0
        while (len(comments)>c and len(methods)>m):
            #print(len(comments), c, len(methods), m)
            if comments[c]['stop_line'] + 1 < methods[m]['start_line']:
                c += 1
            elif comments[c]['stop_line'] + 1 > methods[m]['start_line']:
                m += 1
            elif comments[c]['stop_line'] + 1 == methods[m]['start_line']:
                row = {
                    'method_text': methods[m]['text'],
                    'method_tokens': methods[m]['tokens'],
                    'comment_text': comments[c]['text'],
                    'comment_tokens': self.tokenize_comment(comments[c]['text'])
                }
                data.append(row)
                #print('row:', row)
                c += 1
                m += 1
        return data

    def find_all_file(self, address, type_):
        all_files = []
        for root, dirs, files in os.walk(address):
            for file in files:
                if file.endswith('.' + type_):
                    all_files.append(os.path.join(root, file).replace("\\", "/"))
        return all_files

    def generate(self, java_project_addresses, dataset_path):
        data = []
        for path in java_project_addresses:
            java_project_address = BASE_DATA_DIR + path
            files = self.find_all_file(java_project_address, 'java')
            for f in files:
                print('\t' + f)
                try:
                    stream = FileStream(f, encoding='utf8', errors='ignore')
                except:
                    print('\t' + f, 'can not read')
                    continue
                lexer = JavaLexer(stream)
                tokens = CommonTokenStream(lexer)
                parser = JavaParserLabeled(tokens)
                tree = parser.compilationUnit()
                listener = MethodDetectorListener()
                walker = ParseTreeWalker()

                walker.walk(
                    listener=listener,
                    t=tree
                )

                methods = listener.methods_info
                comments = self.get_cumulative_comments(f)

                data += self.merge(comments, methods)
            # for method_info in listener.methods_info:
            #     comment_text = self.get_comment(f, method_info['start_line'])

        with open(dataset_path, mode="w", encoding='utf-8', errors='ignore') as write_file:
            json.dump(data, write_file, indent=4)

if __name__ == "__main__":
    DG = DataGenerator()
    DG.generate(ORIGINAL_DATA_PATHS, DATASET_PATH)
