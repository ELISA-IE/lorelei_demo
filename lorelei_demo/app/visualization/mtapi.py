#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import json
import urllib2

def trans(lang, query):
    try:
        url = 'http://holst.isi.edu/mt/syntax-translator/v2/language-pairs/' \
              '%s-eng/translation'\
              '?fields=alignment&tokenized=false&detokenize=true&truecase=true'
        req = urllib2.Request(url % lang, query)
        response = urllib2.urlopen(req)
        res = json.loads(response.read())
        return res
    except ValueError:
        return ''

if __name__ == '__main__':
    # print trans('hau', 'gawawwakin')
    print trans('hau', 'An samu dukkan gawawwakin wadanda suka mutu sakamakon balaʼin zabtarewar kasa a lardin Yunnan')
