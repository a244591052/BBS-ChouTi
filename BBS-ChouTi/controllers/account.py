#!/usr/bin/env python
# -*- coding:utf-8 -*-
import io
import datetime
import json
from backend.utils import check_code, message
from backend.core.request_handler import BaseRequestHandler
from forms import account
from backend.utils.response import BaseResponse
from backend import commons
from models import chouti_orm as ORM
from sqlalchemy import and_, or_


class CheckCodeHandler(BaseRequestHandler):
    def get(self, *args, **kwargs):
        # 创建一个内存级别的容器
        stream = io.BytesIO()
        # 创建图片并写入验证码
        img, code = check_code.create_validate_code()
        # 写入容器
        img.save(stream, "png")
        # 把验证码存入session, 为每个用户保存验证码
        self.session["CheckCode"] = code
        # 将图片内容而不是路径 返回给客户端
        self.write(stream.getvalue())


# 验证用户输入合法性和正确性,通过则设置[is_login]=True和[user_info]=
class LoginHandler(BaseRequestHandler):
    def post(self, *args, **kwargs):
        rep = BaseResponse()
        form = account.LoginForm()
        if form.valid(self):
            if form._value_dict['code'].lower() != self.session["CheckCode"].lower():
                rep.message = {'code': '验证码错误'}
                self.write(json.dumps(rep.__dict__))
                return
            conn = ORM.session()
            obj = conn.query(ORM.UserInfo).filter(
                or_(
                    and_(ORM.UserInfo.email == form._value_dict['user'],
                         ORM.UserInfo.password == form._value_dict['pwd']),
                    and_(ORM.UserInfo.username == form._value_dict['user'],
                         ORM.UserInfo.password == form._value_dict['pwd'])
                )).first()
            conn.close()
            if not obj:
                rep.message = {'user': '用户名邮箱或密码错误'}
                self.write(json.dumps(rep.__dict__))
                return

            self.session['is_login'] = True
            self.session['user_info'] = obj.__dict__
            rep.status = True
        else:
            rep.message = form._error_dict
        self.write(json.dumps(rep.__dict__))

# 这里需要注意的是如何拿到插入数据的自增id
class RegisterHandler(BaseRequestHandler):
    def post(self, *args, **kwargs):
        rep = BaseResponse()
        form = account.RegisterForm()
        if form.valid(self):
            current_date = datetime.datetime.now()
            limit_day = current_date - datetime.timedelta(minutes=1)
            conn = ORM.session()
            is_valid_code = conn.query(ORM.SendMsg).filter(ORM.SendMsg.email == form._value_dict['email'],
                                                           ORM.SendMsg.code == form._value_dict['email_code'],
                                                           ORM.SendMsg.ctime > limit_day).count()
            if not is_valid_code:
                rep.message['email_code'] = '邮箱验证码不正确或过期'
                self.write(json.dumps(rep.__dict__))
                return
            has_exists_email = conn.query(ORM.UserInfo).filter(ORM.UserInfo.email == form._value_dict['email']).count()
            if has_exists_email:
                rep.message['email'] = '邮箱已经存在'
                self.write(json.dumps(rep.__dict__))
                return
            has_exists_username = conn.query(ORM.UserInfo).filter(
                ORM.UserInfo.username == form._value_dict['username']).count()
            if has_exists_username:
                rep.message['email'] = '用户名已经存在'
                self.write(json.dumps(rep.__dict__))
                return
            form._value_dict['ctime'] = current_date
            form._value_dict.pop('email_code')
            obj = ORM.UserInfo(**form._value_dict)

            conn.add(obj)
            # 后两句的作用是为了拿到刚插入数据的自增id，obj.nid
            conn.flush()
            conn.refresh(obj)
            # 把nid取出来后再commit，否则提交后则拿不到nid
            user_info_dict = {'nid': obj.nid, 'email': obj.email, 'username': obj.username}

            conn.query(ORM.SendMsg).filter_by(email=form._value_dict['email']).delete()
            conn.commit()
            conn.close()

            self.session['is_login'] = True
            self.session['user_info'] = user_info_dict
            rep.status = True

        else:
            rep.message = form._error_dict

        self.write(json.dumps(rep.__dict__))


# 这里需要注意的是邮件验证码的有效期判断和用户注册的频率
class SendMsgHandler(BaseRequestHandler):
    def post(self, *args, **kwargs):
        rep = BaseResponse()
        form = account.SendMsgForm()
        # 判断输入是否合法
        if form.valid(self):
            email = form._value_dict['email']
            conn = ORM.session()

            # 判断该邮箱是否已注册
            has_exists_email = conn.query(ORM.UserInfo).filter(ORM.UserInfo.email == email).count()
            if has_exists_email:
                rep.summary = '该邮箱已被注册'
                self.write(json.dumps(rep.__dict__))
                return
            current_datetime = datetime.datetime.now()
            code = commons.random_code()

            # 判断该邮箱之前是否发送过验证码
            has_send_count = conn.query(ORM.SendMsg).filter(ORM.SendMsg.email == email).count
            if not has_send_count:
                message.email([email, ], code)
                insert_obj = ORM.SendMsg(email = email, code = code, ctime = current_datetime)
                conn.add(insert_obj)
                conn.commit()
                rep.status = True
            else:
                # 发送过则判断是否过于频繁
                limit_hour = current_datetime - datetime.timedelta(hours=1)
                times = conn.query(ORM.SendMsg).filter(ORM.SendMsg.email == email,
                                                       ORM.SendMsg.ctime > limit_hour,
                                                       ORM.SendMsg.times >= 10,).count()
                if times:
                    rep.summary = "已经超过今日最大次数（1小时后重试）"
                else:
                    # 判断是否超过间隔时间，是则清零
                    unforzen = conn.query(ORM.SendMsg).filter(ORM.SendMsg.email == email,
                                                              ORM.SendMsg.ctime < limit_hour).count()
                    if unforzen:
                        # filter_by 里面是键值对； filter 里面是条件
                        conn.query(ORM.SendMsg).filter_by(email = email).update({"times": 0})
                    message.email([email,], code)
                    conn.query(ORM.SendMsg).filter_by(email = email).update({"times": ORM.SendMsg.times + 1,
                                                                             "code": code,
                                                                             "ctime": current_datetime})
                    conn.commit()
                    rep.status = True
            conn.close()
        else:
            rep.summary = form._error_dict['email']
        self.write(json.dumps(rep.__dict__))



        # ret = {'status':True, 'data':"", "error":""}
        # email = self.get_argument('em',None)
        # if email:
        #     code = commons.random_code()
        #     message.email([email,], code)
        #
        #     conn = ORM.session()
        #     current_time = datetime.datetime.now()
        #     obj = ORM.SendMsg(email=email, code = code, ctime = current_time)
        #     conn.add(obj)
        #     conn.commit()
        # else:
        #     ret['status'] = False
        #     ret['error'] = "邮箱格式错误"
        # self.write(json.dumps(ret))

        # rep = BaseResponse()
        # form = account.SendMsgForm()
        # if form.valid(self):
        #     email = form._value_dict['email']
        #     conn = ORM.session()
        #
        #     has_exists_email = conn.query(ORM.UserInfo).filter(ORM.UserInfo.email == form._value_dict['email']).count()
        #     if has_exists_email:
        #         rep.summary = "此邮箱已经被注册"
        #         self.write(json.dumps(rep.__dict__))
        #         return
        #     current_date = datetime.datetime.now()
        #     code = commons.random_code()
        #
        #     count = conn.query(ORM.SendMsg).filter_by(**form._value_dict).count()
        #     if not count:
        #         message.email([email, ], code)
        #         insert = ORM.SendMsg(code=code,
        #                              email=email,
        #                              ctime=current_date)
        #         conn.add(insert)
        #         conn.commit()
        #         rep.status = True
        #     else:
        #         limit_day = current_date - datetime.timedelta(hours=1)
        #         times = conn.query(ORM.SendMsg).filter(ORM.SendMsg.email == email,
        #                                                ORM.SendMsg.ctime > limit_day,
        #                                                ORM.SendMsg.times >= 10,
        #                                                ).count()
        #         if times:
        #             rep.summary = "'已经超过今日最大次数（1小时后重试）'"
        #         else:
        #             unfreeze = conn.query(ORM.SendMsg).filter(ORM.SendMsg.email == email,
        #                                                       ORM.SendMsg.ctime < limit_day).count()
        #             if unfreeze:
        #                 conn.query(ORM.SendMsg).filter_by(email=email).update({"times": 0})
        #             message.email([email, ], code)
        #             conn.query(ORM.SendMsg).filter_by(email=email).update({"times": ORM.SendMsg.times + 1,
        #                                                                    "code": code,
        #                                                                    "ctime": current_date},
        #                                                                   synchronize_session="evaluate")
        #             conn.commit()
        #             rep.status = True
        #     conn.close()
        # else:
        #     rep.summary = form._error_dict['email']
        #     # print (rep.__dict__)
        # self.write(json.dumps(rep.__dict__))

