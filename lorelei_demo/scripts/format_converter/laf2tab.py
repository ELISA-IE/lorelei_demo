import xml.etree.ElementTree as ET
import argparse
import codecs
import os


def laf2tab(laf_root):
    tab = []
    doc_id = laf_root.find("DOC").get("id")

    for i, ann in enumerate(laf_root.findall(".//ANNOTATION")):
        text = ann.find("EXTENT").text
        start_char = ann.find("EXTENT").get("start_char")
        end_char = ann.find("EXTENT").get("end_char")

        # handle annotation format inconsistency
        try:
            tag = ann.find("TAG").text
        except AttributeError:
            tag = ann.get('type')

        if tag not in ['PER', 'GPE', 'LOC', 'ORG',
                       'per', 'gpe', 'loc', 'org']:
            continue

        tab.append('\t'.join(["laf2tab",
                              "%s-mention-%d" % (doc_id, i),
                              text,
                              "%s:%s-%s" % (doc_id, start_char, end_char),
                              'NIL',
                              tag,
                              'NAM',
                              '1.0']))
    return '\n'.join(tab)


def write2file(tab, tab_file):
    if not tab:
        print('empty tab %s' % tab_file)
        return
    with codecs.open(tab_file, 'w', 'utf-8') as f:
        f.write(tab)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("laf_file")
    parser.add_argument("tab_file")
    parser.add_argument("-d", action="store_true", default=False,
                        help="process directory")

    args = parser.parse_args()

    if args.d:
        for fn in os.listdir(args.laf_file):
            if not fn.endswith(".laf.xml"):
                continue
            try:
                laf_file = os.path.join(args.laf_file, fn)
                tab_file = os.path.join(args.tab_file,
                                        fn.replace(".laf.xml", '.tab'))

                laf_root = ET.parse(laf_file)
                tab = laf2tab(laf_root)
                write2file(tab, tab_file)
            except AttributeError as e:
                print("error in %s" % fn, e)
    else:
        laf_root = ET.parse(args.laf_file)

        tab = laf2tab(laf_root)

        write2file(tab, args.tab_file)