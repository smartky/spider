# -*- coding: utf-8 -*-
import requests
import threading
import Queue
from bs4 import BeautifulSoup

import sys


class Url:
    def __init__(self):
        self.url_str = ''
        self.class_ = ''
        self.name = ''

class AllData:
    _instance_lock = threading.Lock()

    def __init__(self):
        self.data = {}

    def __new__(cls, *args, **kwargs):
        if not hasattr(AllData, "_instance"):
            with AllData._instance_lock:
                if not hasattr(AllData, "_instance"):
                    AllData._instance = object.__new__(cls)
        return AllData._instance

    def add_new_url(self,url):
        if url.class_ not in self.data:
            self.data[url.class_] = {}
        if url.name not in self.data[url.class_]:
            self.data[url.class_][url.name] = {}
        if 'old' not in self.data[url.class_][url.name]:
            self.data[url.class_][url.name]['old'] = set()
        if url.url_str not in self.data[url.class_][url.name]['old']:
            if 'new' not in self.data[url.class_][url.name]:
                self.data[url.class_][url.name]['new'] = Queue.Queue()
            self.data[url.class_][url.name]['new'].put(url.url_str)

    def add_old_url(self,url):
        if url.class_ not in self.data:
            return
        if url.name not in self.data[url.class_]:
            return
        if url.url_str not in self.data[url.class_][url.name]['new']:
            return
        else:
            self.data[url.class_][url.name]['old'].add(url.url_str)
            self.data[url.class_][url.name]['new'].remove(url.url_str)

    def get_new_url(self):
        for class_ in self.data:
            for name_ in self.data[class_]:
                if not self.data[class_][name_]['new'].empty():
                    url_ = self.data[class_][name_]['new'].get()
                    self.data[class_][name_]['old'].add(url_)
                    return [class_,name_,url_]
        return []

class UrlManager:
    def __init__(self):
        self.url_used=set()
        self.url_target=Queue.Queue()

    def getNewUrl(self):
        return self.url_target.get()

    def isEmpty(self):
        return self.url_target.empty()

    def addNewUrl(self,newUrl):
        if newUrl in self.url_used:
            pass
        else:
            self.url_target.put(newUrl)

    def addOldUrl(self,oldUrl):
        self.url_used.add(oldUrl)


def download_info(url_m):
    url_name = UrlManager()
    page_l = []
    url_o = url_m
    page_l.append(url_o)
    tag = url_m[url_m.rfind('/'):url_m.rfind('.')]

    rsp = download_page(url_o)
    bs_page=BeautifulSoup(rsp.text,"html.parser")
    p = bs_page.find_all('a',{'target':"_self"})
    url_end = url_m[:url_m.rfind('/')+1]
    for i in p:
        if '\xe6\x9c\xab\xe9\xa1\xb5' in str(i.prettify('utf-8')):
            url_end += i.get('href')[i.get('href').find('/',2)+1:]
    i = 2
    while True:
        url_add = 'http://www.meituba.com/tag'+tag+'/'+str(i)+'.html'
        page_l.append(url_add)
        if url_add != url_end:
            i += 1
        else:
            break

    for url_origin in page_l:
        rsp = download_page(url_origin)
        bs_page=BeautifulSoup(rsp.text,"html.parser")

        l = bs_page.find_all('a',{'target':"_blank"})
        for one_ in l:
            str_ = str(one_.prettify('utf-8'))
            if 'title' in str_ and 'img' in str_:
                url_ = one_.get('href')
                url_name.addNewUrl(url_)

    down_img = UrlManager()
    while True:
        if url_name.isEmpty():
            break
        url = url_name.getNewUrl()
        if url:
            #print url
            save_img_url(url,down_img)
            url_name.addOldUrl(url)
        else:
            break

    return down_img

'''
start = 'http://www.meituba.com/tag/jutun.html'
end = 'http://www.meituba.com/tag/mnshenghuozhao.html'
tag = 0
for i in ps :
    url_str = i.get('href')
    if start == url_str:
        tag =1
    if end == url_str:
        break
    if tag:
        str_ = str(i.prettify('utf-8'))
        end_ = str_.rfind('</a>')
        s_ = str_.find('k">')
        #print s_,str_[s_+4:end_]
        url[url_str] = str_[s_+4:end_]
'''



def save_img_url(url,down_img):
    page_ = download_page(url)
    bs_page=BeautifulSoup(page_.text,"html.parser")
    ps = bs_page.find_all(lambda tag:tag.has_attr('alt') and tag.has_attr('src'))
    url_s = ''
    url_e = ''
    for img_ in ps:
        j = str(img_.prettify('utf-8'))
        if 'logo' not in j:
            url_s = img_.get('src')

    pages = bs_page.find_all('div',{'class':'pages'})
    str_p = str(pages[0].prettify('utf-8'))
    num = str_p[str_p.find('\xe5\x85\xb1')+3:str_p.find('\xe9\xa1\xb5')]
    url_end = url[:-5]+'_'+num+'.html'
    page_ = download_page(url_end)
    bs_page=BeautifulSoup(page_.text,"html.parser")
    ps = bs_page.find_all(lambda tag:tag.has_attr('alt') and tag.has_attr('src'))
    url_e = ''
    for img_ in ps:
        j = str(img_.prettify('utf-8'))
        if 'logo' not in j:
            url_e = img_.get('src')

    main_url = url_s[:url_s.find('_')+1]
    try:
        start_ = int(url_s[url_s.find('_')+1:url_s.rfind('.')])
        end___ = int(url_e[url_e.find('_')+1:url_e.rfind('.')])
        for i in range(start_,end___):
            p = str(i)
            url_down = main_url+p+url_s[url_s.rfind('.'):]
            down_img.addNewUrl(url_down)
    except:
        pass

def save_img(url,file_):
    rsp2 = download_page(url)
    #print 'down :'+url
    with open(file_,'w') as w:
         w.write(rsp2.content)

def download_page(url):
    #url = ''
    rsp = requests.get(url)
    rsp.encoding = 'utf-8'
    return rsp

if __name__ == "__main__":



    url_m = "http://www.meituba.com/tag/qiaotun.html"
    down_img = download_info(url_m)
    #print 'get all url'
    #print down_img.url_target.qsize()
    path = 'img/'
    count = 1
    while True:
        if down_img.isEmpty():
            break
        url = down_img.getNewUrl()
        if url:
            save_img(url,path+str(count)+url[url.rfind('.'):])
        else:
            break
        count += 1


