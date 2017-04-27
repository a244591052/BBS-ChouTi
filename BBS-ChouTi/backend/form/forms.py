#!/usr/bin/env python
# -*- coding:utf-8 -*-
from backend.form import fields


class BaseForm:

    def __init__(self):
        self._value_dict = {}
        self._error_dict = {}
        self._valid_status = True

    def valid(self, handler):
        # 下一行的self代表着是login、register等类型的对象，那么对应的self.__dict__.items()就代表那些需要验证的字段
        for field_name, field_obj in self.__dict__.items():
            # print(field_name, field_obj)
            # 如果是 _ 开头则代表是
            # self._value_dict = {}
            # self._error_dict = {}
            # self._valid_status = True
            # 这种字段，跳过不操作
            if field_name.startswith('_'):
                continue
            # 获取用户输入的值
            if type(field_obj) == fields.CheckBoxField:
                post_value = handler.get_arguments(field_name, None)
            elif type(field_obj) == fields.FileField:
                post_value = []
                file_list = handler.request.files.get(field_name, [])
                for file_item in file_list:
                    post_value.append(file_item['filename'])
            else:
                post_value = handler.get_argument(field_name, None)
            # 用正则验证用户输入值得合法性
            field_obj.match(field_name, post_value)
            # 合法则添加进value值
            if field_obj.is_valid:
                self._value_dict[field_name] = field_obj.value
            # 不合法则添加进error值，并将status设为false
            else:
                self._error_dict[field_name] = field_obj.error
                self._valid_status = False
        return self._valid_status