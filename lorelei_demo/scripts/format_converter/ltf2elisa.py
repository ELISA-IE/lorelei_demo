import argparse
import os
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET


def ltf2elisa(ltf_dir, elisa_file):
    # generate elisa xml file from ltf docs
    ELISA_LRLP_CORPUS = ET.Element('ELISA_LRLP_CORPUS')
    for i, fn in enumerate(os.listdir(ltf_dir)):
        if not fn.endswith('.ltf.xml'):
            continue
        # parse ltf file
        ltf_root = ET.parse(os.path.join(ltf_dir, fn))
        ltf_doc_id = ltf_root.find('.//DOC').get('id')
        segs = []
        for seg in ltf_root.findall('.//SEG'):
            seg_start = seg.get('start_char')
            seg_end = seg.get('end_char')
            seg_id = '%s-%s' % (ltf_doc_id, seg.get('id'))
            seg_orig_text = seg.find('ORIGINAL_TEXT').text
            tokens = []
            for token in seg.findall('.//TOKEN'):
                token_text = token.text
                token_start = token.get('start_char')
                token_end = token.get('end_char')
                tokens.append((token_text, token_start, token_end))
            segs.append((seg_orig_text, seg_start, seg_end, seg_id, tokens))

        document = ET.Element('DOCUMENT', {'id': ltf_doc_id})
        for j, s in enumerate(segs):
            segment = ET.Element('SEGMENT')

            source = generate_source_element(s, 'source')

            segment.append(source)

            document.append(segment)

        ELISA_LRLP_CORPUS.append(document)

    # pretty print xml
    root_str = ET.tostring(ELISA_LRLP_CORPUS, 'utf-8')
    f_xml = xml.dom.minidom.parseString(root_str)
    pretty_xml_as_string = f_xml.toprettyxml(encoding="utf-8")
    f = open(elisa_file, 'wb')
    f.write(pretty_xml_as_string)
    f.close()


def generate_source_element(sent, sent_type):
    ORIG_RAW_text = sent[0]
    LRLP_TOKENIZED_text = ' '.join([t[0] for t in sent[-1]])
    CDEC_TOKENIZED_text = LRLP_TOKENIZED_text

    s = ET.Element(sent_type.upper(), {'id': sent[3],
                                       'start_char': sent[1],
                                       'end_char': sent[2]})
    full_id = ET.Element('FULL_ID_%s' % sent_type.upper())
    full_id.text = sent[0]
    orig_raw = ET.Element('ORIG_RAW_%s' % sent_type.upper())
    orig_raw.text = ORIG_RAW_text
    lrlp_tokenized = ET.Element('LRLP_TOKENIZED_%s' % sent_type.upper())
    lrlp_tokenized.text = LRLP_TOKENIZED_text
    cdec_tokenized = ET.Element('CDEC_TOKENIZED_%s' % sent_type.upper())
    cdec_tokenized.text = CDEC_TOKENIZED_text

    s.append(full_id)
    s.append(orig_raw)
    s.append(lrlp_tokenized)
    s.append(cdec_tokenized)

    return s


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('ltf_dir')
    parser.add_argument('elisa_file')
    args = parser.parse_args()

    ltf2elisa(args.ltf_dir, args.elisa_file)