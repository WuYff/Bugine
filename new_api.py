from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from operator import itemgetter
from api import descript, query_issue, _filter_search_keys
from model import zip_handler, xml_parser, work_path, match_name, util, nlp_util, search_rank
from model import issuedb
import logging
import csv
from model import table2tsv
import time
import os
import sqlite3
import re
from nltk import ngrams
import json


ui_keywords_json_path = "ui_keywords/"

csv_path = "rank_result/"
stopWords = set(stopwords.words('english'))
stemmer = SnowballStemmer("english")

star_score = {"1": 3, "2": 2, "3": 1}  # ?


# tokenize, stopwords removal and stemming
def nlp_process(content: str) -> list:
    words_filtered = []
    tokenizer = RegexpTokenizer(r'\w+')
    result = tokenizer.tokenize(content)
    for w in result:
        w = w.lower()
        if w not in stopWords:
            if re.fullmatch("([A-Za-z0-9-'])\\w+", w) is not None:
                words_filtered.append(w)

    result = []
    for w in words_filtered:
        result.append(stemmer.stem(w))
    return result


def get_keywords() -> (dict, dict):
    hot_keywords = {}
    two_keywords = {}
    # get key words key = score
    with open('./model/conf/new_keywords.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            hot_keywords[row[0]] = float(row[1])
    f.close()
    with open('./model/conf/key_2_gram.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if float(row[1]) < 0.35:
                break
            two_keywords[row[0]] = float(row[1])
    # with open(work_path.in_project("./model/conf/hotkey.dat"), 'r', encoding='utf8') as f:
    #     for row in f.readlines():
    #         tmp = row.strip()
    #         if tmp != "":
    #             tmp = stemmer.stem(tmp)
    #             if tmp in m:
    #                 print(tmp)

    # z = open("./model/conf/new_keywords.csv", 'w', encoding='utf-8', newline='')
    # # # # 2. 基于文件对象构建 csv写入对象
    # csv_writer = csv.writer(z)
    # # # # 3. 构建列表头
    # # csv_writer.writerow(["word", "weight"])
    # hot_keywords = sorted(hot_keywords, key=itemgetter(1), reverse=True)
    # for h in hot_keywords:
    #     csv_writer.writerow(h)
    # z.close()
    return hot_keywords, two_keywords


def keywords_in_content(hot_keywords: dict, content_words: list, weight=False) -> int:
    # get key words key = score
    count_dict = {}
    for k in content_words:
        if k in hot_keywords:
            if k not in count_dict:
                if weight:
                    count_dict[k] = hot_keywords[k]  # 要不要给keywords加上分数呢？
                else:
                    count_dict[k] = 1
            elif weight:
                count_dict[k] += 1 * hot_keywords[k]  # 要不要给keywords加上分数呢？
            else:
                count_dict[k] += 1
    score = 0
    for k in count_dict:
        score += count_dict[k]
    return score


def ui_key_word(ui_keywords: set, content_words: list) -> tuple:
    count_dict = {}
    for k in ui_keywords:
        if k in content_words:
            if k not in count_dict:
                count_dict[k] = 10
            else:
                count_dict[k] = count_dict[k] + 10
    score = 0
    for k in count_dict:
        score += count_dict[k]
    return (score,count_dict)

def keys_turn_set(_keys_sea):
        ess_keys = set()
        for r in _keys_sea:
            for a_list in r:
                ess_keys = ess_keys.union(a_list)
        ess_keys = " ".join(list(ess_keys))
        ess_keys = nlp_util.stem_sentence(ess_keys)
        return set(ess_keys)

def rank_review(app_score_list: list, max_depth=4) -> list:

    #  app_score_list is a list of (file_path, score, score_distribution_list)
    #   score_distribution_list = [] # should be a list of tuple [(_w1, _w2,  ngram_score)]  _w1 is for the app under test
    hot_keywords, two_keywords = get_keywords()
    rdb = issuedb.ISSuedb()  
    all_review = []
    # number = [5000, 10000, 15000, 20000]
    # number = [1000, 2000, 3000, 4000]
    target_app_keys={}
    ui_keywords_review={}
    target_app_all_keys={}
    for m in range(min(len(app_score_list), max_depth)):
        score_list = app_score_list[m][2]
        app_weight = app_score_list[m][1]

        keys_sea,keys_sea_app_under_test = _filter_search_keys(score_list, threshold=0.7)
        # print("$$$$$$$$$$$$$$$$$")
        # print(keys_sea)
        # ess_keys = set()
        # for r in keys_sea:
        #     for a_list in r:
        #         ess_keys = ess_keys.union(a_list)
        # ess_keys = " ".join(list(ess_keys))
        # ess_keys = nlp_util.stem_sentence(ess_keys)
        # ess_keys = set(ess_keys)

        ess_keys =  keys_turn_set(keys_sea)
        ess_keys_app_under_test =  keys_turn_set(keys_sea)
        # print("@@@@@@@@@@@")
        # print(ess_keys)
        app = app_score_list[m][0]
        app_name = os.path.basename(app)[:-4]
        score = {
            'star_num': 0,
            'hot_key_words': 0,
            'helpful_num': 0,
            'ui_key': 0,
            'similar_app': 0,  # app相似度
            'two_gram_keywords': 0,
        }
        #sql = """select review_id,content,star_num,helpful_num from {} order by length(content) desc"""
        sql = """select id, content,star_num,helpful_num from reviews where app_id=\'{}\' order by length(content) desc"""
        # tab_name = table2tsv.file2table(app)  # csv -> 数据库名字
        # print("@app_name{}".format(app_name))
        output = rdb.db_retrieve(sql.format(app_name))  # sql查询结果
        # head = ["review_id", "content", "bold", "star_num", "helpful_num", "reply_content"]
        head = ["review_id", "content", "star_num", "helpful_num"]
        f_output = issuedb.retrieve_formatter(head, output)
        # f_output[0].review_id
        target_app_keys[app_name] = []
        for i in f_output:
            if len(i.content) < 100:
                break
            processed_content = nlp_process(i.content)  # 没有移除数字
            print("@  {} : {}".format(app_name,processed_content))
            score_sum = 0
            score['star_num'] = star_score[str(i.star_num)]
            score['hot_key_words'] = keywords_in_content(hot_keywords, processed_content, False) * app_weight  # 关键词计分
            score['ui_key_words'] , ui_key_word_dict = ui_key_word(ess_keys, processed_content) 
            score['ui_key_words']=score['ui_key_words'] * app_weight
            matched_keywords_in_other_app_dict = list(ui_key_word_dict.keys())
            for zz in matched_keywords_in_other_app_dict:
                if zz not in target_app_keys[app_name]:
                    target_app_keys[app_name].append(zz) 
            target_app_all_keys[app_name]= list(ess_keys)
            ui_keywords_review[app_name]= ui_key_word_dict
            # score['two_gram_keywords'] = two_gram_key_word(two_keywords, processed_content)
            # score['helpful_num'] = int(i.helpful_num) * 0.25  # bug TypeError: can't multiply sequence by non-int of type 'float'
            # print(score['ui_key_words'])
            # if score['helpful_num'] > 25:
            #       score['helpful_num'] = 25
            for k in score:
                score_sum += score[k]
            if score_sum > 3:  # 3 2 1
                all_review.append([app_name, score_sum, i])
            # if len(all_review) > number[m]:
            #     break
    # 然后对all_review进行排序
    result = sorted(all_review, key=itemgetter(1), reverse=True)
    return (result[:400], target_app_keys,target_app_all_keys,ui_keywords_review)

def two_gram_key_word(two_keywords: dict, content_words: list, weight=False):
    ngrams2_li = [' '.join(w) for w in ngrams( content_words, 2)]
    count_dict = {}
    for k in ngrams2_li:
        if k in two_keywords:
            if k not in count_dict:
                count_dict[k] = 3
            else:
                count_dict[k] += 3
    score = 0
    for k in count_dict:
        score += count_dict[k]
    return score

if __name__ == '__main__':
    app_under_test = "Omni-Notes"
    s = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(time.time()))
    test = util.read_csv("model/data/description/"+app_under_test+".csv")
    print("begin search similar apps")
    scan_output = descript(test, source_category="Productivity",
                           except_files=app_under_test,extend=False, pool_size=32)  # get similar app
    #  scan_output is a list of (file_path, score, score_distribution_list)
    # print(util.get_col(scan_output, [0, 1]))
    print("begin rank reviews")
    rank_result,target_app_keys,target_app_all_keys,ui_keywords_review = rank_review(scan_output)
    now = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime(time.time()))
    # 1. 创建文件对象
    z = open(csv_path +app_under_test+ now + ".csv", 'w', encoding='utf-8', newline='')
    # # 2. 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(z)
    # # 3. 构建列表头
    review_id = 0
    csv_writer.writerow(["review_id","app_id", "score", "star_num", "helpful_num", "review_content"])
    for i in rank_result:
        review_id = review_id +1
        # # 写入文件
        csv_writer.writerow([review_id,i[0], i[1], i[2].star_num, i[2].helpful_num, i[2].content])
    # 5. 关闭文件
    z.close()

    with open(ui_keywords_json_path+app_under_test+'_UI_keywords_target_apps.json', 'w') as fp:
        json.dump(target_app_keys, fp)
    with open(ui_keywords_json_path+app_under_test+'_UI_keywords_target_apps_all.json', 'w') as fp:
        json.dump(target_app_all_keys, fp)
    with open(ui_keywords_json_path+app_under_test+'_UI_keywords_review.json', 'w') as fp:
        json.dump(ui_keywords_review, fp)

    print("end.")
    print(s)
    print(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(time.time())))
