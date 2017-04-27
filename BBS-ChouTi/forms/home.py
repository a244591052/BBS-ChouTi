#!/usr/bin/env python
# -*- coding:utf-8 -*-

from backend.form.forms import BaseForm
from backend.form.fields import StringField
from backend.form.fields import IntegerField
from backend.form.fields import EmailField


class IndexForm(BaseForm):

    def __init__(self):
        self.title = StringField()
        self.content = StringField(required=False) #代表为空也可以
        self.url = StringField(required=False) # 添加文字一栏的时候不知道url，只有加入数据库后才能知道自增ID
        self.news_type_id = IntegerField()

        super(IndexForm, self).__init__()


class CommentForm(BaseForm):

    def __init__(self):
        self.content = StringField()
        self.news_id = IntegerField()
        self.reply_id = IntegerField(required=False)

        super(CommentForm, self).__init__()
