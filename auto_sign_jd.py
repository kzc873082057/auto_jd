#coding=utf-8
import requests
import random
from bs4 import BeautifulSoup
import json
import os
import time
from selenium import webdriver
import re

class auto_sign_jd(object):

    def __init__(self,username,password):
        #username password
        self.username = username
        self.password = password
        # cookie info
        self.track_id = ''
        self.uuid = ''
        self.eid = ''
        self.fp = ''
        self.interval = 0
        #init_url
        self.home = 'https://passport.jd.com/new/login.aspx'
        self.login = 'https://passport.jd.com/uc/loginService'
        self.imag = 'https://authcode.jd.com/verify/image'
        self.auth = 'https://passport.jd.com/uc/showAuthCode'
        self.vip = 'https://vip.jd.com/'
        self.user_info ='https://vip.jd.com/member/getUserInfo.html'
        self.signin = 'https://vip.jd.com/common/signin.html'
        #session_link
        self.session_link = requests.Session()
        #request_header
        self.requests_header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'ContentType': 'application/x-www-form-urlencoded; charset=utf-8',
            'Connection': 'keep-alive',
        }
        try:
            self.browser = webdriver.PhantomJS()
        except Exception,e:
            print 'Phantomjs initialize failed :',e
            exit(1)

    @staticmethod
    def response_status(response):
        #Check whether the connection is successful
        if response.status_code != requests.codes.OK:
            print 'Status: %u, Url: %s' % (response.status_code, response.url)
            return False
        return True

    def need_auth_code(self,username):
        # check if need auth code
        auth_data = {
            'loginName':username
         }
        parameter = {
            'r':random.random(),
            'version':'2015'
        }
        response = self.session_link.post(self.auth,data=auth_data,params=parameter)
        if self.response_status(response):
            js = json.loads(response.text[1:-1])
            return js['verifycode']
        print u'获取是否需要验证码失败'
        return False
    def get_auth_code(self,uuid):
        #image save path
        image_file = os.path.join(os.getcwd(),'authcode.jpg')
        parameter = {
            'a':1,
            'acid':uuid,
            'uid':uuid,
            'yys':str(int(time.time() * 1000)),
        }
        # get auth code
        response = self.session_link.get(self.imag,params = parameter)
        if not self.response_status(response):
            print u'获取验证码失败'
            return False
        with open(image_file,'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        os.system('start'+ image_file)
        return str(raw_input('Auth Code'))

    def login_once(self, login_data):
        # url parameter
        payload = {
            'r': random.random(),
            'uuid': login_data['uuid'],
            'version': 2015,
        }

        resp = self.session_link.post(self.login, data=login_data, params=payload)
        if self.response_status(resp):
            js = json.loads(resp.text[1:-1])
            if not js.get('success'):
                print  js.get('emptyAuthcode')
                return False
            else:
                return True
        return False

    def login_try(self):
        # get login page
        # resp = self.session_link.get(self.home)
        print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        print u'{0} > 登陆'.format(time.ctime())

        try:
            # 2016/09/17 PhantomJS can't login anymore
            self.browser.get(self.home)
            soup = BeautifulSoup(self.browser.page_source, "html.parser")

            # set cookies from PhantomJS
            for cookie in self.browser.get_cookies():
                self.session_link.cookies[cookie['name']] = str(cookie['value'])

            # for (k, v) in self.session_link.cookies.items():
            # 	print '%s: %s' % (k, v)

            # response data hidden input == 9 ??. Changed
            inputs = soup.select('form#formlogin input[type=hidden]')
            rand_name = inputs[-1]['name']
            rand_data = inputs[-1]['value']
            token = ''
            for idx in range(len(inputs) - 1):
                id = inputs[idx]['id']
                va = inputs[idx]['value']
                if id == 'token':
                    token = va
                elif id == 'uuid':
                    self.uuid = va
                elif id == 'eid':
                    self.eid = va
                elif id == 'sessionId':
                    self.fp = va

            auth_code = ''
            if self.need_auth_code(self.username):
                auth_code = self.get_auth_code(self.uuid)
            else:
                print u'无验证码登陆'
            login_data = {
                '_t': token,
                'authcode': auth_code,
                'chkRememberMe': 'on',
                'loginType': 'f',
                'uuid': self.uuid,
                'eid': self.eid,
                'fp': self.fp,
                'nloginpwd': self.password,
                'loginname': self.username,
                'loginpwd': self.password,
                rand_name: rand_data,
            }

            login_succeed = self.login_once(login_data)
            if login_succeed:
                self.track_id = self.session_link.cookies['TrackID']
                print u'登陆成功 %s' % self.username
            else:
                print u'登陆失败 %s' % self.username
            self.signi()
            return login_succeed
        except Exception, e:
            print 'Exception:', e.message
            print e
        return False
    def signi(self):
        vip_source = self.session_link.get(self.vip).content
        compile_re = re.compile(r'.*pageConfig.token="(.*)";')
        token = compile_re.search(vip_source).groups()[0]
        print token
        params = {
            'token':token
        }
        user_json_data = self.session_link.get(self.user_info,params=params).content
        user_js = json.loads(user_json_data)

        if user_js['success']:
            user_info = user_js['result']['userInfo']
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'用户名:' + user_info['nicknameShow']
            print u'当前京豆:'+ str(user_info['userJingBeanNum'])
        else:
            print u'获取当前用户信息失败'

        jd_json_data = self.session_link.get(self.signin,params=params).content
        jd_js = json.loads(jd_json_data)
        if jd_js['success']:
            jd = jd_js['result']
            print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++'
            print u'连续签到:'+str(jd['brightSize'])+u'天'
            print u'获得京豆:'+str(jd['jdnum'])+u'个'
            print u'签到成功'
        else:
            print u'签到失败'



if __name__ == '__main__':
    username = raw_input('Please enter account')
    password = raw_input('Please input a password')
    jd = auto_sign_jd(username,password)
    jd.login_try()
    jd.browser.close()



