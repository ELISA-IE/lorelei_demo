#-*- coding: utf-8 -*-
import sys
import io
import operator
import uuid
import os
import sys
import re
import uuid
import shutil


PWD = os.path.dirname(os.path.abspath(__file__))
KBNAMESPACE = 'https://en.wikipedia.org/wiki'
# KBNAMESPACE = 'https://www.freebase.com'


# ******** Classes Definition ******** #
class Mention(object):
    def __init__(self, mid, mstr, did, b, e, kb, etype, mtype, c):
        self.mention_id = mid
        self.mention_str = mstr
        self.docid = did
        self.beg = int(b)
        self.end = int(e)
        self.ref_kb = kb
        self.entity_type = etype
        self.mention_type = mtype
        self.conf = float(c)

    def tohtml(self, id_='', err=dict(), image=False):
        tag = self.entity_type
        t = '<span id="%stag" >%s</span>' % (tag.lower(), self.entity_type)
        m = '<span id="%s" >%s</span>' % (tag.lower(), self.mention_str)
        if err == dict():
            mention = '[%s %s]' % (t, m)
        else:
            mention = '[<mark>%s %s</mark>]' % (t, m)

        tooltip = '<span id=\'%s\' class=\'inline\' data-tipped-options' \
                  '="inline: \'%s-%s\'">%s</span> ' % (self.mention_id,
                                                       self.mention_id, id_,
                                                       mention)
        if 'spurious' in err:
            elements = 'Mention ID: <mark>%s</mark> -> Spurious Mention<br>' % \
                       self.mention_id
        else:
            elements = 'Mention ID: %s<br>' % self.mention_id
        if 'offset' in err:
            '%s <a onmouseover="SelectText(\'%s\');">%s</a> '
            elements += 'Mention Str: <mark>%s</mark> %s:%s -> <a onmouseover' \
                        '="SelectText(\'%s\');">%s %s:%s</a><br>' % \
                        (self.mention_str, self.beg, self.end,
                         err['offset'][1], err['offset'][0],
                         err['offset'][2], err['offset'][3])
        else:
            elements += 'Mention Str: %s %s:%s<br>' % (self.mention_str,
                                                       self.beg, self.end)
        if 'kb' in err:
            elements += 'Reference KB: <a href="%s/%s" target="_blank"> ' \
                        '<mark>%s</mark></a>' \
                        ' -> <a href="%s/%s" target="_blank">%s</a><br>' \
                        % (KBNAMESPACE, self.ref_kb, self.ref_kb,
                           KBNAMESPACE, err['kb'][0], err['kb'][0])
        else:
            elements += 'Reference KB: <a href="%s/%s" target="_blank">' \
                        '%s</a><br>' % (KBNAMESPACE, self.ref_kb, self.ref_kb)

        if 'etype' in err:
            elements += 'Entity Type: <mark>%s</mark> -> %s<br>' % \
                        (self.entity_type, err['etype'][0])
        else:
            elements += 'Entity Type: %s<br>' % self.entity_type
        if 'mtype' in err:
            elements += 'Mention Type: <mark>%s</mark> -> %s<br>' % \
                        (self.mention_type, err['mtype'][0])
        else:
            elements += 'Mention Type: %s<br>' % self.mention_type

        elements += 'Confidence Value: %s<br>' % self.conf

        # boliang: generate token translation
        if w4w_translation:
            tokens = self.mention_str.split(' ')
            translations = [w4w_translation[t.decode('utf-8')] if t.decode('utf-8') in w4w_translation else [] for t in tokens]
            translation_tip = []
            for i, t in enumerate(tokens):
                line = '&nbsp&nbsp' + t + '&nbsp->&nbsp' + ';&nbsp'.join(translations[i][:3])
                translation_tip.append(line)

            elements += 'Translation:<br>' + "<br>".join(translation_tip) + '<br>'

        if image:
            elements += 'Images: <br>'
            elements += get_image_div(self.mention_str)

        div = '<div id=\'%s-%s\' style=\'display:none\'>%s</div>' \
              % (self.mention_id, id_, elements)
        return tooltip + div


# ******** Support Functions ******** #
def parse_tab(path):
    ### Parse .tab output file
    tab = open('%s' % path)
    docs = dict()
    for line in tab:
        try:
            line = line.strip().split('\t')
            mid = line[1].replace('.', '-')  # HTML span id cannot support dot
            mstr = line[2]
            # docid_offset = re.match('(\S+)\:(\d+)\-(\d+)', line[3])
            # did = docid_offset.group(1)
            # b = docid_offset.group(2)
            # e = docid_offset.group(3)
            did = line[3].split(':')[0]
            try:
                b = line[3].split(':')[1].split('-')[0]
                e = line[3].split(':')[1].split('-')[1]
            except IndexError:
                print('tab line error: ', line)
            kb = line[4]
            etype = line[5]
            mtype = line[6]
            c = line[7]
            if KBNAMESPACE == 'https://www.freebase.com':
                kb = kb.replace('.', '/')
            try:
                mention_obj = Mention(mid, mstr, did, b, e, kb, etype, mtype, c)
            except ValueError:
                print(line)
            if did not in docs:
                docs[did] = dict()
            docs[did][mid] = mention_obj
        except AttributeError:
            continue
    return docs


def check_err(query, gold):
    err = dict()
    if all([m.ref_kb == 'NIL' for m in gold.values()]):
        check_linking_err = False
    else:
        check_linking_err = True

    for mid in gold:
        gm = gold[mid]
        if query.beg == gm.beg and query.end == gm.end:
            if query.entity_type == gm.entity_type and \
                            query.mention_type == gm.mention_type and \
                            query.ref_kb == gm.ref_kb:
                return dict()
            else:
                if query.entity_type != gm.entity_type:
                    err['etype'] = (gm.entity_type, gm.mention_id)
                if query.mention_type != gm.mention_type:
                    err['mtype'] = (gm.mention_type, gm.mention_id)

                # Do not have entity linking yet
                if check_linking_err and query.ref_kb != gm.ref_kb:
                    if query.ref_kb.startswith('NIL') and \
                            gm.ref_kb.startswith('NIL'):
                        pass
                    else:
                        err['kb'] = (gm.ref_kb, gm.mention_id)
            return err
        # If the offset is not correct, doesn't check other errors
        elif query.beg in range(gm.beg, gm.end+1) or \
                        query.end in range(gm.beg, gm.end+1):
            err['offset'] = (gm.mention_str, gm.mention_id, gm.beg, gm.end)
            return err
    err['spurious'] = 'Spurious'
    return err


def check_missing(system, gold):
    missing = dict()
    for mid_g in gold:
        mg = gold[mid_g]
        get = False
        for mid_s in system:
            ms = system[mid_s]
            if mg.beg in range(ms.beg, ms.end+1) or \
                            mg.end in range(ms.beg, ms.end+1):
                get = True
                break
        if get == False:

            if w4w_translation:
                # Boliang: generate token translation for missing mention
                mg.mention_str = get_token_translation(mg.mention_str)

            missing[mg.mention_id] = mg
    return missing


def counts(mentions):
    count = dict()
    count['total'] = 0
    count['per'] = 0
    count['org'] = 0
    count['gpe'] = 0
    count['loc'] = 0
    count['fac'] = 0
    count['ttl'] = 0
    count['nam'] = 0
    count['nom'] = 0
    for mid in mentions:
        m = mentions[mid]
        count['total'] += 1
        count[m.entity_type.lower()] += 1
        count[m.mention_type.lower()] += 1
    return count


def fix_unicode(data):
    if isinstance(data, int):
        return data.encode('utf-8')
    elif isinstance(data, dict):
        data = dict((fix_unicode(k), fix_unicode(data[k])) for k in data)
    elif isinstance(data, list):
        for i in range(0, len(data)):
            data[i] = fix_unicode(data[i])
    return data


def pretty(text, rtl=False):
    if rtl:
        text = ['<div lang="ar" dir="rtl">' + item + '</div>' for item in text.split('\n')]
        ptext = '<br>'.join(text)
    else:
        ptext = text.replace('\n', '<br>')
    return ptext


def get_image_div(mention_str):
    # check if mention string has cached images
    image_cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    '../static/per_images')

    names_with_cached_image = set(os.listdir(image_cache_path))

    if mention_str in names_with_cached_image:
        if not len(os.listdir(os.path.join(image_cache_path, mention_str))) > 10:
            return 'Not Found'
    else:
        return 'Not Found'

    images = ''
    pf = '/static/per_images/%s/%s.jpg'
    n = 1
    while n < 5:
        url = pf % (urllib.quote(mention_str), n)
        try:
            # u = urllib2.urlopen(url, timeout=10)
            # u.close()
            images += '<li><img src="%s" ' \
                      'style="width:250px;height:250px;"></li>' % url
        except urllib2.HTTPError as e:
            break
        except urllib2.URLError as e:
            break
        n += 1

    image_div_index = str(uuid.uuid4())  # generate unique id
    image_div = '<div id="slider%s" class="slider" index="%s">' \
                '<a href="#" class="control_next" id="ctrl_next_%s">>></a>' \
                '<a href="#" class="control_prev" id="ctrl_prev_%s"><</a>' \
                '<ul>' \
                '%s' \
                '</ul>' \
                '</div>' % (image_div_index,
                            image_div_index,
                            image_div_index,
                            image_div_index,
                            images)
    return image_div


def get_translation(text, lang):
    res = ''
    snt_count = 0
    for line in text.split('\n'):
        alig = dict()
        if line == '':
            res += '<br>'
            continue
        tres = mtapi.trans(lang, line)
        trg = tres['translation'][0]['nbest'][0]['text']
        toked_trg = tres['translation'][0]['nbest'][0]['alignment']['tokenized-target']
        toked_src = tres['translation'][0]['nbest'][0]['alignment']['tokenized-source']

        alig = dict()
        ti = 0
        for tt in toked_trg:
            src_toks_index = list()
            for st in tt['source']:
                try:
                    si = st['index']
                    src_toks_index.append(si)
                except:
                    pass
            for si in src_toks_index:
                if si not in alig:
                    alig[si] = list()
                alig[si].append(ti)
            ti += 1

        src_html = toked_src.split(' ')
        trg_html = trg.split(' ')
        n = 0
        for n in range(len(src_html)):
            if n in alig:
                spanid = 'snt%s-tok%s' % (snt_count, n)
                src_html[n] = '<a onmouseover="SelectText(\'%s\');"><i>%s</i></a>' % \
                              (spanid, src_html[n])
                tt = alig[n]
                trg_toks = trg_html[tt[0]:tt[-1]+1]
                trg_html[tt[0]] = '<span id="%s">%s</span>' % (spanid,
                                                               ' '.join(trg_toks))
                for i in tt[1:]:
                    trg_html[i] = ''

        src_html = ' '.join(src_html)
        trg_html = ' '.join(trg_html)
        res += '%s<br><font color=#DF7401>%s</font><br>' % (src_html, trg_html)
        snt_count += 1
    return res


# boliang
def get_translation_from_prl(text, docid):
    elisa_doc = None
    for doc in pdp.elisa_documents:
        if doc.id == docid:
            elisa_doc = doc

    if not elisa_doc:
        print("%s not found in parallel during generating translation" % docid)
        return False

    res = []
    for line in text.strip().split('\n'):
        trans = ''
        for p in elisa_doc.parallels:
            src_sent = p[0].orig_raw
            trg_sent = p[1].orig_raw
            if src_sent in line:
                trans += trg_sent

        res.append(trans)

    return res


# boliang
def get_token_translation(s):
    res = []
    s = s.split('\n')
    for line in s:
        line_res = []
        for t in line.split(' '):
            try:
                if t.strip().decode('utf-8') in w4w_translation:
                    translation = w4w_translation[t.strip().decode('utf-8')]
                elif t.strip()[:-1].decode('utf-8') in w4w_translation:
                    translation = w4w_translation[t.strip()[:-1].decode('utf-8')]
                elif t.strip()[1:].decode('utf-8') in w4w_translation:
                    translation = w4w_translation[t.strip()[1:].decode('utf-8')]
                else:
                    translation = []
            except ValueError:
                translation = []
            if len(t) > 0:
                div_id = uuid.uuid4()
                if translation:
                    translation_html = '<span style="border-bottom:1px dashed;" class=\'inline\' data-tipped-options="inline: \'%s\'">%s</span> <div id=\'%s\' style=\'display:none\'>%s -> %s</div>' % (div_id, t, div_id, t, '; '.join(translation[:3]))
                else:
                    translation_html = '<span>%s</span>' % t
            else:
                translation_html = t
            line_res.append(translation_html)
        res.append(' '.join(line_res))

    return '\n'.join(res)


# boliang
def add_token_translation(rlist):
    res = []
    current_raw_text = ''
    for i, item in enumerate(rlist):
        if len(item) < 4:
            current_raw_text += item
            if i == len(rlist) - 1:
                current_raw_text = get_token_translation(current_raw_text)
                res.append(current_raw_text)
        else:
            if current_raw_text:
                current_raw_text = get_token_translation(current_raw_text)
                res.append(current_raw_text)
                current_raw_text = ''
            # if item.startswith('<mark>') and '<span>' not in item:
            #     stem = item.replace('<mark>', '').replace('</mark>')
            #     stem_translation_html = get_token_translation(stem)
            #     res.append('<mar>%s</mark>' % stem_translation_html)

            res.append(item)

    return res


def get_div(rlist, divname, name, n=-1, lang='', docid='', raw_text='', rtl=False):
    button = '<button type="button" onclick="showhide(\'%s\');"><b>' \
             '%s</b></button>&nbsp;'
    button_div = '<div id="%s" style=\'display:none\'>%s</div>'

    # rlist = fix_unicode(rlist)

    # boliang
    if w4w_translation:
        rlist = add_token_translation(rlist)

    text = ''.join(rlist)

    # boliang ----------
    if lang and docid:
        # generate English translation from parallel data
        if pdp:
            trans = get_translation_from_prl(raw_text, docid)
        else:
            trans = []
        if trans:
            print(docid)
            sents = text.strip().split('\n')
            assert len(sents) == len(trans)
            if rtl:
                sent_div = ['<div lang="ar" dir="rtl">' + sents[i] + '<br>' + '<span lang="en" dir="ltr" style="color:#DF7401">' + trans[i] + '</span></div><br>'
                            for i in range(len(sents))]
            else:
                sent_div = [sents[i] + '<br>' + '<span style="color:#DF7401">' + trans[i] + '</span><br>'
                            for i in range(len(sents))]
            text = '<br>'.join(sent_div)
        else:
            text = pretty(text, rtl=rtl)
    else:
        text = pretty(text, rtl=rtl)

    # -------------------

    if n == -1:
        text = '<br>%s' % text
    else:
        text = '<code># of %s errors:</code> %d<br>%s' % (name, n, text)

    b_div = button % (divname, name)
    if divname == 'gold':
        t_div = button_div.replace('display:none', '') % (divname, text)
    elif divname == 'sys':
        # t_div = button_div.replace(':none', ':block') % (divname, text)
        t_div = button_div.replace('display:none', '') % (divname, text)
    else:
        t_div = button_div % (divname, text)
    return b_div, t_div


# ******** Main Functions ******** #
# Visualization ithout gold for single document.
def visualize_single_doc_without_gold(docid, doc_dir, tab_path,
                                      out_dir='', srctext='', lang='', rtl=False):
    res = ''
    tab = parse_tab(tab_path)

    ### Initialize HTML
    div_template = open('%s/div_template.html' % PWD, 'r').read()
    html_tail = '</div>'

    ### Src doc: str -> list
    if srctext != '':
        text = srctext
    else:
        try:
            text = open(os.path.join(doc_dir, docid)).read()
        except IOError:
            try:
                text = open(os.path.join(doc_dir, docid+'.rsd.txt')).read()
            except IOError:
                print('no rsd document found for %s' % docid)
                return res

    text = text.replace('<', '{').replace('>', '}') # Replace xml marks
    src_list = list(text)

    ### Count
    count = counts(tab[docid])
    # count_html = '<code>Total:</code> %d ' \
    #              '<code>NAM:</code> %d ' \
    #              '<code>NOM</code>: %d <br>' \
    #              '<span id="pertag" >PER</span>: %d ' \
    #              '<span id="orgtag" >ORG</span>: %d ' \
    #              '<span id="gpetag" >GPE</span>: %d ' \
    #              '<span id="loctag" >LOC</span>: %d ' \
    #              '<span id="factag" >FAC</span>: %d ' \
    #              '<span id="ttltag" >TTL</span>: %d ' \
    #              '<br>' \
    #              % (count['total'], count['nam'], count['nom'],
    #                 count['per'], count['org'], count['gpe'],
    #                 count['loc'], count['fac'], count['ttl'])

    count_html = '<code>Total:</code> %d ' \
                 '<code>NAM:</code> %d ' \
                 '<code>NOM</code>: %d <br>' \
                 '<span id="pertag" >PER</span>: %d ' \
                 '<span id="orgtag" >ORG</span>: %d ' \
                 '<span id="gpetag" >GPE</span>: %d ' \
                 '<span id="loctag" >LOC</span>: %d ' \
                 '<br>' \
                 % (count['total'], count['nam'], count['nom'],
                    count['per'], count['org'], count['gpe'],
                    count['loc'])

    res += '%s\n<hr>%s<br>\n%s\n' % (div_template, docid, count_html)

    ### Replace raw text with HTML
    for mid in sorted(tab[docid]):
        mention = tab[docid][mid]
        if mention.docid != docid:
            continue
        beg = mention.beg
        end = mention.end
        try: # TODO: Check offset
            pass
        except:
            pass
        # Replace the first char by HTML
        src_list[beg] = mention.tohtml(image=False)
        # Replace the remaining chars by ''
        for n in range(beg+1, end+1):
            src_list[n] = ''

    gres = get_div(src_list, 'gold', 'Silver', lang=lang, docid=docid, raw_text=text, rtl=rtl)
    # res += '%s\n%s\n' % (gres[0], gres[1])
    res += '%s\n%s\n' % ('', gres[1])

    # src_list = fix_unicode(src_list)
    # src_text = ''.join(src_list)
    # src_text = pretty(src_text, lang=lang)
    # res += '<div>%s<div>\n' % (src_text)
    res += html_tail
    res = res.replace('<br><br><br>', '')

    if out_dir:
        out = open(os.path.join(out_dir, '%s.html' % docid), 'w')
        out.write(res)

    return res


def visualize_batch_doc_without_gold(docs_dir, sys_path,
                                     out_dir='', lang=''):
    # if lang specified, show word translation for each word.
    if lang:
        # print 'ISI MT API will generate translations...'
        print('Translations will be generated from MT API or parallel data')

        # load word for word translation table
        w4w_translation_fp = os.path.join(elisa_ie_root, 'data/name_taggers/' \
                                                         'expectation_driven/w4w_translation/%s2eng' % lang)
        if not os.path.exists(w4w_translation_fp):
            print('word for word translation table file path not exists.')
            lang = ''
        global w4w_translation  # update global variable
        w4w_translation = dict()
        for line in io.open(w4w_translation_fp, 'r', -1, 'utf-8'):
            # line = line.split(' ')
            line = line.split('\t')
            if line[0] in w4w_translation:
                w4w_translation[line[0]].append((line[1], float(line[2])))
            else:
                w4w_translation[line[0]] = [(line[1], float(line[2]))]

        # sort translation by confidence
        for word in w4w_translation:
            translation = w4w_translation[word]
            sorted_translation = sorted(translation, key=operator.itemgetter(1), reverse=True)
            w4w_translation[word] = [item[0] for item in sorted_translation]

    # if "lang" specified, visualize English translation from parallel data.
    if lang:
        # load parallel data
        global pdp  # update global variable
        pdp = ParallelDataProcessor(lang, dev_mode=False)
        pdp.initialize()

    batch_visualization_html = []
    try:
        os.mkdir(out_dir)
    except:
        pass

    system = parse_tab(sys_path)
    for docid in system.keys():
        try:
            visualization_html = visualize_single_doc_without_gold(docid, docs_dir,
                                                                   sys_path,
                                                                   out_dir=out_dir,
                                                                   lang=lang)
            batch_visualization_html.append(visualization_html)
        except:
            print('Unexpected error: %s\n%s' % (sys.exc_info(), docid))
            continue

    print('%s Done.' % os.path.split(sys_path)[1])

    return batch_visualization_html


# Visualization with gold for single document
def visualize_single_doc_with_gold(docid, doc_dir, gold_path, sys_path,
                                   out_dir='', lang='', pl_dir='', srctext='', rtl=False):
    file_doc_id = docid
    if type(gold_path) != dict:
        gold = parse_tab(gold_path)

    system = parse_tab(sys_path)

    ### Initialize HTML
    res = ''
    div_template = open('%s/div_template.html' % PWD, 'r').read()
    html_tail = '</body>\n</html>\n'

    ### Src doc: str -> list
    if srctext:
        text = srctext
    else:
        try:
            text = open(os.path.join(doc_dir, docid)).read()
        except IOError:
            for fn in os.listdir(doc_dir):
                if docid in fn:
                    text = open(os.path.join(doc_dir, fn)).read()
                    if fn.replace('.rsd.txt', '') != docid:
                        file_doc_id = fn.replace('.rsd.txt', '')
            # text = open(os.path.join(doc_dir, '%s.rsd.txt' % docid)).read()

    text = text.replace('<', '{').replace('>', '}') # Replace xml marks
    orig_list = list(text)
    gold_list = list(text)
    sys_list = list(text)

    ### Count
    count = counts(gold[docid])
    # count_html = '<code>Total:</code> %d ' \
    #              '<code>NAM:</code> %d ' \
    #              '<code>NOM</code>: %d <br>' \
    #              '<span id="pertag" >PER</span>: %d ' \
    #              '<span id="orgtag" >ORG</span>: %d ' \
    #              '<span id="gpetag" >GPE</span>: %d ' \
    #              '<span id="loctag" >LOC</span>: %d ' \
    #              '<span id="factag" >FAC</span>: %d ' \
    #              '<span id="ttltag" >TTL</span>: %d ' \
    #              '<br>' \
    #              % (count['total'], count['nam'], count['nom'],
    #                 count['per'], count['org'], count['gpe'],
    #                 count['loc'], count['fac'], count['ttl'])

    count_html = '<code>Total:</code> %d ' \
                 '<code>NAM:</code> %d ' \
                 '<code>NOM</code>: %d <br>' \
                 '<span id="pertag" >PER</span>: %d ' \
                 '<span id="orgtag" >ORG</span>: %d ' \
                 '<span id="gpetag" >GPE</span>: %d ' \
                 '<span id="loctag" >LOC</span>: %d ' \
                 '<br>' \
                 % (count['total'], count['nam'], count['nom'],
                    count['per'], count['org'], count['gpe'],
                    count['loc'])
    res += div_template
    res += '<hr>%s<br>%s' % (docid, count_html)

    ### Replace raw text with HTML: GOLD
    for mid in sorted(gold[docid]):
        mention = gold[docid][mid]
        if mention.docid != docid:
            continue
        beg = mention.beg
        end = mention.end
        try: # TODO: Check offset
            pass
        except:
            pass
        # Replace the first char by HTML
        gold_list[beg] = mention.tohtml(id_='gold')
        # Replace the remaining chars by ''
        for n in range(beg+1, end+1):
            gold_list[n] = ''

    if lang in ['bn', 'ha', 'ta', 'th', 'tl', 'tr', 'ug', 'uz', 'yo', 'uig']:
        gold_or_silver = 'Gold'
    else:
        gold_or_silver = 'Silver'

    gres = get_div(gold_list, 'gold', gold_or_silver, lang=lang, docid=docid, raw_text=text, rtl=rtl)
    res += '%s\n%s\n' % (gres[0], gres[1])

    ### Replace raw text with HTML: System
    sys_list_missing = sys_list[:] # Missing errors only
    sys_list_spurious = sys_list[:] # Spurious errors only
    sys_list_linking = sys_list[:] # Linking errors only
    sys_list_offset = sys_list[:] # Offset errors only
    sys_list_etype = sys_list[:] # Entity type errors only
    sys_list_mtype = sys_list[:] # Mention type errors only

    ### Check erros
    count_spurious = 0
    count_linking = 0
    count_offset = 0
    count_etype = 0
    count_mtype = 0
    for mid in system[docid]:
        mention = system[docid][mid]
        if mention.docid != docid:
            continue
        beg = mention.beg
        end = mention.end
        try: # TODO: Check offset
            pass
        except:
            pass
        err = check_err(mention, gold[docid])
        if err == dict(): # No errors
            sys_list[beg] = mention.tohtml(id_='sys', image=False)
            sys_list_missing[beg] = mention.tohtml(id_='sys_mis')
            sys_list_spurious[beg] = mention.tohtml(id_='sys_s')
            sys_list_linking[beg] = mention.tohtml(id_='sys_l')
            sys_list_offset[beg] = mention.tohtml(id_='sys_o')
            sys_list_etype[beg] = mention.tohtml(id_='sys_e')
            sys_list_mtype[beg] = mention.tohtml(id_='sys_m')
        else:
            sys_list[beg] = mention.tohtml(err=err, image=False)
            if 'spurious' in err:
                sys_list_spurious[beg] = mention.tohtml(id_='sys_mis', err=err)
                count_spurious += 1
            if 'kb' in err:
                sys_list_linking[beg] = mention.tohtml(id_='sys_l', err=err)
                count_linking += 1
            if 'offset' in err:
                sys_list_offset[beg] = mention.tohtml(id_='sys_o', err=err)
                count_offset += 1
            if 'etype' in err:
                sys_list_etype[beg] = mention.tohtml(id_='sys_e', err=err)
                count_etype += 1
            if 'mtype' in err:
                sys_list_mtype[beg] = mention.tohtml(id_='sys_m', err=err)
                count_mtype += 1
        for n in range(beg+1, end+1):
            sys_list[n] = ''
            sys_list_missing[n] = ''
            sys_list_spurious[n] = ''
            sys_list_linking[n] = ''
            sys_list_offset[n] = ''
            sys_list_etype[n] = ''
            sys_list_mtype[n] = ''

    ### Check missing errors
    missing = check_missing(system[docid], gold[docid])
    for mid in missing:
        m_mention = missing[mid]
        sys_list[m_mention.beg] = '<a onmouseover="SelectText(\'%s\');"><mark' \
                                  '>%s</mark></a>' % (m_mention.mention_id,
                                                      m_mention.mention_str)
        for n in range(m_mention.beg+1, m_mention.end+1):
            sys_list[n] = ''

        sys_list_missing[m_mention.beg] = '<a onmouseover="SelectText(\'%s\')' \
                                          ';"><mark>%s</mark></a>' % \
                                          (m_mention.mention_id,
                                           m_mention.mention_str)
        for n in range(m_mention.beg+1, m_mention.end+1):
            sys_list_missing[n] = ''

    sys_res = list()
    for i in [(sys_list, 'sys', 'System', -1),
              (sys_list_missing, 'sys_mis', 'Missing', len(missing)),
              (sys_list_spurious, 'sys_s', 'Spurious', count_spurious),
              (sys_list_linking, 'sys_l', 'Linking', count_linking),
              (sys_list_offset, 'sys_o', 'Boundary', count_offset),
              (sys_list_etype, 'sys_e', 'Entity Type', count_etype),
              (sys_list_mtype, 'sys_m', 'Mention Type', count_mtype)]:
        # for i in [(sys_list, 'sys', 'System', -1)]:
        sys_res.append(get_div(i[0], i[1], i[2], i[3], lang=lang, docid=docid, raw_text=text, rtl=rtl))
    res += '<hr>\n'
    for i in sys_res:
        res += i[0]
    res += '<br>\n'
    for i in sys_res:
        res += i[1]
    # if lang:
    #     # trans_text = get_translation(text, lang)
    #     trans_text = get_translation_from_prl(text, docid)
    #     t_div = '<hr><code><font color=#DF7401>Translation</font></code>' \
    #             '<div id="trans" style=\'\'>%s</div>' % (trans_text)
    #     res += '%s\n' % (t_div)
    if pl_dir:
        try:
            pl_text = open('%s/%s' % (pl_dir, docid)).read()
            pl_text = pretty(pl_text)
            p_div = '<hr><code><font color=#DF7401>Parallel</font></code>' \
                    '<div id="pl" style=\'\'>%s</div>' % (pl_text)
            res += '%s\n' % (p_div)
        except:
            pass

    res += html_tail
    res = res.replace('<br><br><br>', '')

    if out_dir:
        out = open(os.path.join(out_dir, '%s.html' % file_doc_id), 'w')
        out.write(res)

    return res


pdp = None  # global variable ParallelDataProcessor
w4w_translation = None  # global variable word for word translation table
# Visualization with gold for batch of documents
def visualize_batch_doc_with_gold(docs_dir, gold_path, sys_path,
                                  out_dir='', lang='', rtl=False):
    if lang:
        # print 'ISI MT API will generate translations...'
        print('Translations will be generated from MT API or parallel data')

    batch_visualization_html = []
    try:
        os.mkdir(out_dir)
    except:
        pass

    # if lang specified, show word translation for each word.
    if lang:
        # load word for word translation table
        w4w_translation_fp = os.path.join(elisa_ie_root, 'data/name_taggers/' \
                                                         'expectation_driven/w4w_translation/%s2eng' % lang)
        if not os.path.exists(w4w_translation_fp):
            print('word for word translation table file path not exists.')
        else:
            global w4w_translation  # update global variable
            w4w_translation = dict()
            for line in io.open(w4w_translation_fp, 'r', -1, 'utf-8'):
                if not line.strip():
                    continue
                if '\t' in line:
                    line = line.split('\t')
                elif ' ' in line:
                    line = line.split(' ')
                if line[0] in w4w_translation:
                    w4w_translation[line[0]].append((line[1], float(line[2])))
                else:
                    w4w_translation[line[0]] = [(line[1], float(line[2]))]

            # sort translation by confidence
            for word in w4w_translation:
                translation = w4w_translation[word]
                sorted_translation = sorted(translation, key=operator.itemgetter(1), reverse=True)
                w4w_translation[word] = [item[0] for item in sorted_translation]

    # if "lang" specified, visualize English translation from parallel data.
    if lang:
        # load parallel data
        global pdp  # update global variable
        pdp = ParallelDataProcessor(lang, dev_mode=False)
        pdp.initialize()

    gold = parse_tab(gold_path)
    system = parse_tab(sys_path)
    for docid in system.keys():
        if docid not in gold.keys():
            continue
        try:
            visualization_html = visualize_single_doc_with_gold(docid, docs_dir,
                                                                gold_path, sys_path,
                                                                out_dir, lang, rtl=rtl)
            batch_visualization_html.append(visualization_html)
        except KeyError:
            print('Unexpected error: %s\n%s' % (sys.exc_info(), docid))
            continue
        except AssertionError:
            print('Unexpected error: %s\n%s' % (sys.exc_info(), docid))
            continue
        except UnboundLocalError:
            print('Unexpected error: %s\n%s' % (sys.exc_info(), docid))
            continue

    print('%s Done.' % os.path.split(sys_path)[1])

    return batch_visualization_html


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('USAGE: edl15_err_ana.py <source docs dirc> <gold> <system> <output dir>')
    else:
        docs_dir = sys.argv[1]
        gold_path = sys.argv[2]
        sys_path = sys.argv[3]
        out_dir = sys.argv[4]
        try:
            os.mkdir(out_dir)
        except:
            pass

        gold = parse_tab(gold_path)
        system = parse_tab(sys_path)
        for docid in system.keys():
            if docid not in gold.keys():
                continue
            try:
                visualize_single_doc_with_gold(docid, docs_dir, gold, system, out_dir,
                                               pl_dir='/Users/panx/Desktop/test/pl')
            except IndexError:
                print(docid)
                continue

        print('%s Done.' % os.path.split(sys_path)[1])
