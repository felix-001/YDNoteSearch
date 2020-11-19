#!/usr/bin/python

import requests
import sys
import time
import hashlib
import os
import http.cookiejar as cj
from requests.cookies import create_cookie
import json
from workflow import Workflow

reload(sys)  
sys.setdefaultencoding('utf8')

def timestamp():
    return str(int(time.time() * 1000))

class YoudaoNoteSession(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8'
        }
        self.cookies = cj.LWPCookieJar('cookies.txt')
	try:
            self.cookies.load(ignore_discard=True)
            cookies_dict = requests.utils.dict_from_cookiejar(self.cookies)
            self.cstk = cookies_dict['YNOTE_CSTK']
	except IOError:
            self.cstk = '0'
            print('no cookies')

    def login(self, username, password):
        self.get('https://note.youdao.com/web/')
        self.headers['Referer'] = 'https://note.youdao.com/web/'
        resp = self.get('https://note.youdao.com/signIn/index.html?&callback=https%3A%2F%2Fnote.youdao.com%2Fweb%2F&from=web')
        print('signIn status: ' + str(resp.status_code))
        self.headers['Referer'] = 'https://note.youdao.com/signIn/index.html?&callback=https%3A%2F%2Fnote.youdao.com%2Fweb%2F&from=web'
        resp = self.get('https://note.youdao.com/login/acc/pe/getsess?product=YNOTE&_=' + timestamp())
        print('getsess status: ' + str(resp.status_code))
        resp = self.get('https://note.youdao.com/auth/cq.json?app=web&_=' + timestamp())
        print('cq.json status : ' + str(resp.status_code))
        resp = self.get('https://note.youdao.com/auth/urs/login.json?app=web&_=' + timestamp())
        print('login.json status: ' + str(resp.status_code))
        data = {
            "username": username,
            "password": hashlib.md5(password).hexdigest()
        }
        resp = self.post('https://note.youdao.com/login/acc/urs/verify/check?app=web&product=YNOTE&tp=urstoken&cf=6&fr=1&systemName=&deviceType=&ru=https%3A%2F%2Fnote.youdao.com%2FsignIn%2F%2FloginCallback.html&er=https%3A%2F%2Fnote.youdao.com%2FsignIn%2F%2FloginCallback.html&vcode=&systemName=&deviceType=&timestamp=' + timestamp(), data=data, allow_redirects=True)
        print('login resp: ' + str(resp.status_code))
        resp = self.get('https://note.youdao.com/yws/mapi/user?method=get&multilevelEnable=true&_=' + timestamp())
        print('multilevelEnable: ' + str(resp.status_code))
        cookies_dict = requests.utils.dict_from_cookiejar(self.cookies)
        self.cstk = cookies_dict['YNOTE_CSTK']
        print('cstk: ' + self.cstk)
        self.cookies.save('cookies.txt', ignore_discard=True, ignore_expires=True)

    def search(self, keyword):
        url = "https://note.youdao.com/yws/api/personal/search?method=webSearch&kw="+keyword+"&parentId=&b=0&l=15&keyfrom=web&cstk="+self.cstk
        data = { 'cstk' : self.cstk }
        resp = self.post( url, data=data, allow_redirects=True)
        jsons = json.loads(resp.content)
        if resp.status_code != 200:
            #print("url: " + url)
            print("webSearch status " + str(resp.status_code))
            return None
        else:
            return jsons['entries']

    def getNoteDocx(self, id, saveDir):
        url = 'https://note.youdao.com/ydoc/api/personal/doc?method=download-docx&fileId=%s&cstk=%s&keyfrom=web' % (id, self.cstk)
        #print(url)
        response = self.get(url)
        with open('%s/%s.docx' % (saveDir, id), 'w') as fp:
            fp.write(response.content)

def main(wf):
    username = os.getenv("YDNOTE_USER")
    password = os.getenv("YDNOTE_PASSWD")
    sess = YoudaoNoteSession()
    notes = sess.search(sys.argv[1])
    if notes == None:
        sess.login(username, password)
        notes = sess.search(sys.argv[1])
    i = 0
    while i < len(notes):
        print(notes[i]['fileEntry']['name'])
        wf.add_item(title=notes[i]['fileEntry']['name'])
        i = i + 1
    wf.send_feedback()

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('args: <keyword>' )
        sys.exit(1)
    wf = Workflow() 
    sys.exit(wf.run(main))
