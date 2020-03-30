# coding:utf8
import requests
import time
import json
import os
import sys
import re
from tqdm import tqdm
reload(sys)
sys.setdefaultencoding('utf8')

class GetKeyValue(object):
    def __init__(self, o, mode='j'):
        self.json_object = None
        if mode == 'j':
            self.json_object = o
        elif mode == 's':
            self.json_object = json.loads(o)
        else:
            raise Exception('Unexpected mode argument.Choose "j" or "s".')

        self.result_list = []

    def search_key(self, key):
        self.result_list = []
        self.__search(self.json_object, key)
        return self.result_list

    def __search(self, json_object, key):

        for k in json_object:
            if k == key:
                self.result_list.append(json_object[k])
            if isinstance(json_object[k], dict):
                self.__search(json_object[k], key)
            if isinstance(json_object[k], list):
                for item in json_object[k]:
                    if isinstance(item, dict):
                        self.__search(item, key)
        return


class UserImageGetter():
    def __init__(self):
        self.gkv = GetKeyValue
        self.rule = re.compile('(<.*?>)', re.S)

    def run(self, uid, containerid='', verbose=False):
        if not os.path.exists(uid):
            os.mkdir(uid)
            os.chdir(uid)
        url = 'https://m.weibo.cn/api/container/getIndex?uid={}&type=uid&value={}&containerid={}'.format(uid, uid, containerid)
        reqcontent = self.request(url)
        # print(reqcontent)
        loadjson = self.gkv(o=reqcontent, mode='s')
        while True:
            time.sleep(0.5)
            try:
                since_id = loadjson.search_key('since_id')[0]
            except:
                break
            if verbose:
                print('since_id:{}'.format(since_id))
            url2 = 'https://m.weibo.cn/api/container/getIndex?uid={}&type=uid&value={}&containerid={}&since_id={}'.format(
                uid, uid, containerid, since_id)
            if verbose:
                print('next_url:{}'.format(url2))
            reqcontent = unicode(self.request(url2))
            # print(reqcontent)
            loadjson = self.gkv(o=reqcontent, mode='s')
            cards = loadjson.search_key('cards')[0]
            ctime = None
            for card in cards:
                content, imageurl, ctime = self.parseblog(card)
                k = 0
                for image in tqdm(imageurl):
                    k += 1
                    imagecontent = self.request(image)
                    with open('{}/{},{},{}.jpg'.format(uid, content, ctime, k), 'wb') as f:
                        f.write(imagecontent)
                        f.close()
                    time.sleep(0.2)
            print('Done...Enter Next page. Current time:{}'.format(ctime))

    def parseblog(self, blogjson):
        content = blogjson['mblog']['text']
        content = self.rule.sub('', str(content))
        ctime = blogjson['mblog']['created_at']
        imageurl = []
        if 'pics' in blogjson['mblog']:
            for item in blogjson['mblog']['pics']:
                imageurl.append(self.getiurl(item))
        return content, imageurl, ctime
    @staticmethod
    def getiurl(picsjson):
        if 'large' in picsjson:
            return picsjson['large']['url']
        return ['url']


    @staticmethod
    def request(url):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'MWeibo-Pwa': '1',
            'Referer': 'https://m.weibo.cn/u/{}?uid={}'.format(uid, uid),
            'Sec-Fetch-Dest': 'empty',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            # 'X-XSRF-TOKEN': '56c23b'
        }
        return requests.get(url, headers=headers).content

if __name__ == '__main__':

    uig = UserImageGetter()
    while True:
        print('请输入带爬用户的id')
        uid = raw_input('>>>')
        uig.run(uid=uid)
        print('用户{}图片爬取完成。'.format(uid))


