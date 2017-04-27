#!/usr/bin/env python
# -*- coding:utf-8 -*-
import hashlib
import time
import random
import collections

def random_code():
    code = ''
    for i in range(4):
        current = random.randrange(0,4)
        if current != i:
            temp = chr(random.randint(65,90))
        else:
            temp = random.randint(0,9)
        code += str(temp)
    return code


def generate_md5(value):
    r = str(time.time())
    obj = hashlib.md5(r.encode('utf-8'))
    obj.update(value.encode('utf-8'))
    return obj.hexdigest()



def tree_search(d_dic, comment_obj): #d_dic {(1, '111', None):{},}不过是有序字典类型   #comment_obj (9, '999', 5) 第三个值不是none的
    # 在comment_dic中一个一个的寻找其回复的评论
    # 检查当前评论的 reply_id 和 comment_dic中已有评论的nid是否相同，
    #   如果相同，表示就是回复的此信息
    #   如果不同，则需要去 comment_dic 的所有子元素中寻找，一直找，如果一系列中未找，则继续向下找
    for k, v_dic in d_dic.items():
        # 找回复的评论，将自己添加到其对应的字典中，例如： {评论一： {回复一：{},回复二：{}}}
        if k[0] == comment_obj[2]:
            d_dic[k][comment_obj] = collections.OrderedDict()
            print(d_dic)
            return
        else:
            # 在当前元素下中递归的去寻找该条评论的父亲
            tree_search(d_dic[k], comment_obj)

comment_list = [
            (1, '111',None),
            (2, '222',None),
            (3, '33',None),
            (9, '999',5),
            (4, '444',2),
            (5, '555',1),
            (6, '666',4),
            (7, '777',2),
            (8, '888',4),
        ]



def build_tree(comment_list):

    comment_dic = collections.OrderedDict() # 定义了一个有序空字典

    print(comment_dic) #OrderedDict()
    # 字典的键必须是不可变的，如字符串，数字或元组。
    for comment_obj in comment_list:
        # print(comment_obj)
        if comment_obj[2] is None:
            print(comment_obj) # (1, '111', None)
            # 如果是根评论，添加到comment_dic[评论对象] ＝ {}
            comment_dic[comment_obj] = collections.OrderedDict() # comment_dic = {(1, '111', None):{},}
        else:
            # 如果是回复的评论，则需要在 comment_dic 中找到其回复的评论
            tree_search(comment_dic, comment_obj)
    return comment_dic

# build_tree(comment_list)
