from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from operator import itemgetter
from api import descript, query_issue
from model import zip_handler, xml_parser, work_path, match_name, util, nlp_util, search_rank
from model import issuedb
import logging
import csv
from model import table2tsv
import datetime
import time

csv_path = "rank_result/"
stopWords = set(stopwords.words('english'))
stemmer = SnowballStemmer("english")

star_score = {"1": 3, "2": 2, "3": 1}  # ?
hot_keywords = {}


# tokenize, stopwords removal and stemming
def nlp_process(content: str) -> list:
    words_filtered = []
    tokenizer = RegexpTokenizer(r'\w+')
    result = tokenizer.tokenize(content)
    for w in result:
        w = w.lower()
        if w not in stopWords:
            words_filtered.append(w)

    result = []
    for w in words_filtered:
        result.append(stemmer.stem(w))
    return result


def keywords_in_content(content_words: list, weight=False) -> int:
    # get key words key = score
    count_dict = {}
    for k in hot_keywords:
        if k in content_words:
            if weight:
                count_dict[k] += 1 * hot_keywords[k]  # 要不要给keywords加上分数呢？
            else:
                count_dict[k] += 1
    score = 0
    for k in count_dict:
        score += count_dict[k]
    return score


def rank_review(app_score_list: list, max_depth=4) -> list:
    # 对于筛选出来的相似app
    # sql = """select review_id,content,bold,star_num,helpful_num,reply_content from {}
    #                 order by length(content) desc"""
    logger = logging.getLogger("StreamLogger")
    rdb = issuedb.ISSuedb()  # 'review2.db
    all_review = []
    for i in range(min(len(app_score_list), max_depth)):
        app = app = scan_output[i][0]
        score = {
            'star_num': 0,
            'hot_key_words': 0,
            'helpful_num': 0,
            'ui_key': 0,
            'similar_app': 0  # app相似度
        }
        sql = """select review_id,content,star_num,helpful_num from {} order by length(content) desc"""
        tab_name = table2tsv.file2table(app)  # csv -> 数据库名字
        output = rdb.db_retrieve(sql.format(tab_name))
        # head = ["review_id", "content", "bold", "star_num", "helpful_num", "reply_content"]
        head = ["review_id", "content", "star_num", "helpful_num"]
        f_output = issuedb.retrieve_formatter(head, output)
        # f_output[0].review_id
        for i in f_output:
            score_sum = 0
            score['star_num'] = star_score[i.star_num]
            score['hot_key_words'] = keywords_in_content(nlp_process(i.content)) * 0.3
            score['helpful_num'] = int(
                i.helpful_num) * 0.25  # bug TypeError: can't multiply sequence by non-int of type 'float'
            for k in score:
                score_sum += score[k]
            if score_sum > 1:  # 3 2 1
                all_review.append([score_sum, i])
    # 然后对all_review进行排序
    return sorted(all_review, key=itemgetter(0), reverse=True)


if __name__ == '__main__':
    test = util.read_csv("model/data/description/com.duckduckgo.mobile.android.csv")
    scan_output = descript(test, except_files="com.duckduckgo.mobile.android", pool_size=12)  # get similar app
    rank_result = rank_review(scan_output)
    now = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime(time.time()))
    # 1. 创建文件对象
    z = open(csv_path + now + ".csv", 'w', encoding='utf-8', newline='')
    # # 2. 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(z)
    # # 3. 构建列表头
    csv_writer.writerow(["score", "star_num", "help_num", "review_content"])
    for i in rank_result:
        # # 写入文件
        csv_writer.writerow([i[0], i[1].star_num, i[1].helpful_num, i[1].content])
    # 5. 关闭文件
    z.close()
    print(rank_result)
    print(len(rank_result))
