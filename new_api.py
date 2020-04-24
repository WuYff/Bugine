from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from operator import itemgetter
from api import descript, query_issue
from model import zip_handler, xml_parser, work_path, match_name, util, nlp_util, search_rank
from model import issuedb
import logging
from model import table2tsv

stopWords = set(stopwords.words('english'))
stemmer = SnowballStemmer("english")

star_score = {"1": 3, "2": 2, "3": 1}
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
            'similar_app': 0
        }
        sql = """select review_id,content,star_num,helpful_num from {} order by length(content) desc"""
        tab_name = table2tsv.file2table(app)
        output = rdb.db_retrieve(sql.format(tab_name))
        # head = ["review_id", "content", "bold", "star_num", "helpful_num", "reply_content"]
        head = ["review_id", "content", "star_num", "helpful_num"]
        f_output = issuedb.retrieve_formatter(head, output)
        for i in f_output:
            score_sum = 0
            score['star_num'] = star_score[i.star_num]
            score['hot_key_words'] = keywords_in_content(nlp_process(i.content)) * 0.3
            score['helpful_num'] = i.helpful_num * 0.25 # bug TypeError: can't multiply sequence by non-int of type 'float'
            for k in score:
                score_sum += score[k]
            if score_sum > 1:
                all_review.append([score_sum, i])
    # 然后对all_review进行排序
    return sorted(all_review, key=itemgetter(0))


if __name__ == '__main__':
    test = util.read_csv("model/data/description/com.duckduckgo.mobile.android.csv")
    scan_output = descript(test, except_files="com.duckduckgo.mobile.android", pool_size=12)  # get similar app
    rank_result = rank_review(scan_output)
