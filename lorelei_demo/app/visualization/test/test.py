import sys
sys.path.append('../')
import edl_err_ana

def test_single():
    docid = 'NW_CRI_HAU_006004_20130113'
    doc_dir = 'src_doc/'
    out_dir = './'
    tab_path = 'tab/eval.tab'
    edl_err_ana.visualization(docid, doc_dir, out_dir, tab_path, lang='hau')

def test_multi():
    docid = 'NW_CRI_HAU_006004_20130113'
    doc_dir = 'src_doc/'
    out_dir = './'
    gold_path = 'tab/eval.tab'
    sys_path = 'tab/eval.tab'
    gold = edl_err_ana.parse_tab(gold_path)
    system = edl_err_ana.parse_tab(sys_path)

    edl_err_ana.err_ana_visualization(docid, doc_dir, out_dir, gold, system, lang='hau')

def test_mtapi_output():
    import json
    tres = json.loads(open('json2', 'r').read())
    trg = tres['translation'][0]['nbest'][0]['text']
    toked_trg = tres['translation'][0]['nbest'][0]['alignment']['tokenized-target']
    toked_src = tres['translation'][0]['nbest'][0]['alignment']['tokenized-source']

    alig_toked_trg = list()
    alig = dict()
    print toked_src
    print trg
    ti = 0
    for tt in toked_trg:
        src_toks_index = list()
        for st in tt['source']:
            try:
                si = st['index']
                src_toks_index.append(si)
            except:
                alig_toked_trg.append((tt['token'], list()))
        alig_toked_trg.append((tt['token'], src_toks_index))
        for si in src_toks_index:
            if si not in alig:
                alig[si] = list()
            alig[si].append(ti)
        ti += 1
    src_html = toked_src.split(' ')
    trg_html = trg.split(' ')
    n = 0
    snt_count = 0
    for i in alig:
        print i, alig[i]

    for n in range(len(src_html)):
        if n in alig:
            spanid = 'snt%s-tok%s' % (snt_count, n)
            src_html[n] = '<a onmouseover="SelectText(\'%s\');"><i>%s</i></a>' % \
                          (spanid, src_html[n])
            tt = alig[n]
            print n, alig[n]
            trg_toks = trg_html[tt[0]:tt[-1]+1]
            print trg_toks
            trg_html[tt[0]] = '<span id="%s">%s</span>' % (spanid,
                                                           ' '.join(trg_toks))
            for i in tt[1:]:
                trg_html[i] = ''
            # print n, alig[n][0], alig[n][1:]
    #         th = '<span id="%s">%s</span>' % (spanid, ' '.join(alig[n]))
    #         trg_html = trg_html.replace(' '.join(alig[n]), th, 1)

    src_html = ' '.join(src_html)
    trg_html = ' '.join(trg_html)
    res = '%s<br><font color=#DF7401>%s</font><br>' % (src_html, trg_html)
    print res


    # pre_toks = alig_toked_trg[0][1]
    # for a in alig_toked_trg:
    #     if a[1] != pre_toks:
    #         spanid = 'snt%s-tok%s' % (snt_count, n)
    #         th = '<span id="%s">%s</span>' % (spanid, a[0])
    #         trg_html.append(th)

    #     # spanid = 'snt%s-tok%s' % (snt_count, n)
    #     #         if n in alig:
    #     #             src_html[n] = '<a onmouseover="SelectText(\'%s\');"><i>%s</i></a>' % \
    #     #                           (spanid, src_html[n])
    #     th = '<span id="%s">%s</span>' % (spanid, a[0])
    #     trg_html.append(th)
    #     n += 1
    # print ' '.join(trg_html)

if __name__ == '__main__':
    # test_single()
    test_multi()
    # test_mtapi_output()
