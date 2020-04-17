import os
import random
from model import issuedb
from model  import match_name
from model  import util
from model  import nlp_util
from model import search_rank
from model import table2tsv
from model import url_repo
# import eval_test
import logging

pp = util.PrintWarp()

SRC_DIR = "tsv/"
TEST_DIR = "tsv_test/"


def select_item(a_list):
    print("-" * 50)
    length = len(a_list)
    for i in range(length):
        print("{}\t{}".format(i + 1, a_list[i]))
    while True:
        try:
            sele = int(input("Select number:"))
            print(sele)
            if sele not in range(1, length + 1):
                raise Exception("Not in range.")
            else:
                break
        except Exception as e:
            pass
    return sele - 1


def select_dir(path):
    filelist = os.listdir(path)
    filelist.sort(key=lambda x: x.lower())
    i = select_item(filelist)
    rt_path = os.path.join(path, filelist[i])
    return rt_path


def scan_match(sample_ui_list, path_list, comp_func, weight_list=None, threshold=0.6):
    """
    :param sample_ui_list: output after process_tsv()
    :param path_list: relative or absolute path list of tsv files
    :param comp_func: compare function
    :param weight_list: ui weight mask
    :param threshold: threshold，超过一定的阈值才会被计算成相同组件
    :return: best match path name
    """
    logger = logging.getLogger("StreamLogger")
    out_dict = dict()
    for path in path_list:
        logger.debug(path)
        tmp_out = util.read_tsv(path)
        tmp_out = nlp_util.process_tsv(tmp_out)
        out_dict[os.path.basename(path)] = tmp_out

    count = 0
    score_list = []
    for j in range(len(path_list)):
        count += 1
        j_file = os.path.basename(path_list[j])
        name = path_list[j]
        if len(out_dict[j_file]) == 0:
            logger.debug(f"EMPTY {name}")
            score_distribution_list = []
            continue
        else:
            score_distribution_list = match_name.weight_compare_list(sample_ui_list, out_dict[j_file], comp_func,
                                                                     weight_list)
        # score_distribution_list = util.get_col(score_distribution_list, 2)
        score = match_name.similar_index(score_distribution_list, threshold, col_index=2, rate=True)

        score_list.append((name, score, score_distribution_list))
        logger.debug(f"ADD {count} {name}")
    # return sorted path^score^score_distribution_list list
    return sorted(score_list, key=lambda k: k[1], reverse=True)


def restore_mask(name):
    """连接符分隔开，重新变成数组"""
    tmp = list(filter(lambda item: item != "#", name.split("=")))
    for i in range(len(tmp)):
        tmp[i] = tmp[i].split("^")
    return tmp


def filter_search_keys(weight_list, threshold=0.6, unique=True):
    """
    :param weight_list: output of weight_compare_list
    :param threshold: threshold
    :param unique: unique the keys
    :return: 3 dim list of target ui components
    """
    keys = []
    for res in weight_list:
        src, target, score = res
        if score < threshold:
            continue
        src, target = map(restore_mask, [src, target])
        keys.append(target)
    if unique:
        unique_keys = util.StringHash(keys)
        return unique_keys.get_in_list()
    else:
        return keys