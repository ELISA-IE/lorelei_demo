import codecs
import os
import argparse
import operator
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET


def bio2laf_no_offset(bio_str, doc_id, delimiter=' '):
    bio_sents = bio_str.split('\n\n')
    sents = []
    tags = []
    for sent in bio_sents:
        s = []
        t = []
        for line in sent.splitlines():
            token = line.split(' ')[0]
            tag = line.split(' ')[-1]
            s.append(token)
            t.append(tag)
        sents.append(s)
        tags.append(t)

    doc_text = '\n'.join([delimiter.join(sent) for sent in sents])

    # laf xml root
    laf_root = ET.Element('LCTL_ANNOTATIONS')
    laf_doc_element = ET.Element('DOC', {'id': doc_id})
    laf_root.append(laf_doc_element)

    prev_seg_end = -2
    for i in range(len(sents)):
        # ======== generate ltf file
        seg_text = delimiter.join(sents[i])
        seg_start_char = prev_seg_end + 2  # '\n' between segs
        seg_end_char = seg_start_char + len(seg_text) - 1
        prev_seg_end = seg_end_char

        # ======= generate laf file
        # get annotations
        annotations = []
        tmp_ann_start = -1
        for j in range(len(sents[i])):
            if tags[i][j].startswith('B'):
                if tmp_ann_start != -1:
                    tmp_ann_end = j - 1
                    e_type = tags[i][tmp_ann_end].split('-')[1]
                    annotations.append((tmp_ann_start, tmp_ann_end, e_type))
                tmp_ann_start = j
            elif tags[i][j].startswith('O'):
                if tmp_ann_start != -1:
                    tmp_ann_end = j - 1
                    e_type = tags[i][tmp_ann_end].split('-')[1]
                    annotations.append((tmp_ann_start, tmp_ann_end, e_type))
                tmp_ann_start = -1
            elif j == len(sents[i]) - 1:
                if tmp_ann_start != -1:
                    tmp_ann_end = j
                    e_type = tags[i][tmp_ann_end].split('-')[1]
                    annotations.append((tmp_ann_start, tmp_ann_end, e_type))
        # map offsets to annotation
        for j, ann in enumerate(annotations):
            start_index = int(ann[0])
            end_index = int(ann[1])
            e_type = ann[2]

            annotation_text = delimiter.join(sents[i][start_index:end_index+1])
            start_offset = len(delimiter.join(sents[i][:start_index+1])) - len(sents[i][start_index]) + seg_start_char
            end_offset = len(delimiter.join(sents[i][:end_index+1])) + seg_start_char - 1
            assert doc_text[start_offset:end_offset+1] == annotation_text
            ann_id = '%s-ann-%d' % (doc_id, j)
            annotation_element = ET.Element('ANNOTATION', {'id': ann_id,
                                                           'task': 'NE',
                                                           'type': e_type})
            extent_element = ET.Element('EXTENT', {'start_char': str(start_offset),
                                                   'end_char': str(end_offset)})
            extent_element.text = annotation_text
            annotation_element.append(extent_element)
            laf_doc_element.append(annotation_element)

    return laf_root


def bio2laf_with_offset(bio_str):
    parsed_bios = parse_bio(bio_str)
    rtn_laf = {}
    for doc_id, bios in parsed_bios.items():
        # generate doc text
        doc_text = ''
        prev_word_end = -1
        for s in bios:
            doc_text += '\n' * (s[0][1] - prev_word_end - 1)
            for i, w in enumerate(s):
                if i == 0:
                    doc_text += w[0]
                else:
                    doc_text += ' ' * (w[1] - prev_word_end - 1) + w[0]

                assert doc_text[w[1]:w[2]+1] == w[0]

                prev_word_end = w[2]

        # laf xml root
        laf_root = ET.Element('LCTL_ANNOTATIONS')
        laf_doc_element = ET.Element('DOC', {'id': doc_id})
        laf_root.append(laf_doc_element)

        for i in range(len(bios)):
            # ======= generate laf file
            # get annotations
            annotations = []
            tmp_ann_start = -1
            for j in range(len(bios[i])):
                if bios[i][j][3].startswith('B'):
                    if tmp_ann_start != -1:
                        tmp_ann_end = j - 1
                        e_type = bios[i][tmp_ann_end][3].split('-')[1]
                        annotations.append((tmp_ann_start, tmp_ann_end, e_type))
                    tmp_ann_start = j
                elif bios[i][j][3].startswith('O'):
                    if tmp_ann_start != -1:
                        tmp_ann_end = j - 1
                        e_type = bios[i][tmp_ann_end][3].split('-')[1]
                        annotations.append((tmp_ann_start, tmp_ann_end, e_type))
                    tmp_ann_start = -1
                elif j == len(bios[i]) - 1:
                    if tmp_ann_start != -1:
                        tmp_ann_end = j
                        e_type = bios[i][tmp_ann_end][3].split('-')[1]
                        annotations.append((tmp_ann_start, tmp_ann_end, e_type))
            # map offsets to annotation
            for j, ann in enumerate(annotations):
                start_index = int(ann[0])
                end_index = int(ann[1])
                e_type = ann[2]

                annotation_text = ''
                prev_word_end = bios[i][start_index][1] - 1
                for word in bios[i][start_index:end_index+1]:
                    annotation_text += ' ' * (word[1] - prev_word_end - 1) + word[0]
                    prev_word_end = word[2]

                start_offset = bios[i][start_index][1]
                end_offset = bios[i][end_index][2]

                assert doc_text[start_offset:end_offset + 1] == annotation_text

                ann_id = '%s-ann-%d' % (doc_id, j)
                annotation_element = ET.Element('ANNOTATION', {'id': ann_id,
                                                               'task': 'NE',
                                                               'type': e_type})
                extent_element = ET.Element('EXTENT',
                                            {'start_char': str(start_offset),
                                             'end_char': str(end_offset)})
                extent_element.text = annotation_text
                annotation_element.append(extent_element)
                laf_doc_element.append(annotation_element)
        rtn_laf[doc_id] = laf_root

    return rtn_laf


def parse_bio(bio_str):
    print('=> parsing bio string...')
    bio = {}
    num_token = 0
    for i, sent in enumerate(bio_str.split('\n\n')):
        sent = sent.strip()
        if not sent:
            continue
        tokens = []
        d_id = ''
        for t in sent.splitlines():
            word, offset, tag = operator.itemgetter(0, 1, -1)(t.split())
            d_id, o = offset.split(':')
            start, end = o.split('-')

            tokens.append((word, int(start), int(end), tag))
        try:
            bio[d_id].append(tokens)
        except KeyError:
            bio[d_id] = [tokens]

        num_token += len(tokens)

        sys.stdout.write(
            '%d sentences, %d tokens parsed.\r' % (i, num_token))
        sys.stdout.flush()

    sys.stdout.write('%d docs, %d sentences, %d tokens parsed.\n' %
                     (len(bio), len(bio_str.split('\n\n')), num_token))

    return bio


def write2file(laf_root, laf_fp):
    laf_xml = xml.dom.minidom.parseString(ET.tostring(laf_root, 'utf-8'))
    f = codecs.open(laf_fp, 'w', 'utf-8')
    f.write(laf_xml.toprettyxml(indent='\t'))
    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('bio_fp', type=str,
                        help='input bio file path.')
    parser.add_argument('laf_fp', type=str,
                        help='output laf file path.')
    parser.add_argument('--with_offset',  action='store_true', default=False,
                        help='bio with offset')
    parser.add_argument('--delimiter', type=str, default=' ',
                        help='delimiter used to join words when offset '
                             'is not provided.')
    parser.add_argument('-d', '--dir', action='store_true', default=False,
                        help='input and output are directories')

    args = parser.parse_args()

    bio_files = []
    if args.dir:
        for f in os.listdir(args.bio_fp):
            if not f.endswith('.bio'):
                continue
            f_path = os.path.join(args.bio_fp, f)
            bio_files.append(f_path)
    else:
        bio_files.append(args.bio_fp)

    for f in bio_files:
        bio_str = codecs.open(f, 'r', 'utf-8').read()

        if args.with_offset:
            laf_root = bio2laf_with_offset(bio_str)
        else:
            doc_id = f.split('/')[-1].replace('.bio', '')
            laf_root = bio2laf_no_offset(bio_str, doc_id, args.delimiter)

        if type(laf_root) is dict:
            for d_id, r in laf_root.items():
                laf_file = os.path.join(args.laf_fp, doc_id + '.laf.xml')
                write2file(r, laf_file)
        else:
            write2file(laf_root, os.path.join(args.laf_fp, doc_id + '.laf.xml'))
