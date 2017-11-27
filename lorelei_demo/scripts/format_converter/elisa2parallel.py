# this script convert ELISA xml format into parallel plain text files which
# can be used as GIZA++ input
import argparse
import xml.etree.ElementTree as ET
import codecs
import os
import gzip


def elisa2parallel(xml_str):
    src_sents = []
    trg_sents = []

    root = ET.fromstring(xml_str)
    for src in root.findall(".//SOURCE"):
        src_text = src.find("ORIG_RAW_SOURCE").text
        src_sents.append(src_text)
    for trg in root.findall(".//TARGET"):
        trg_text = trg.find("ORIG_RAW_TARGET").text
        trg_sents.append(trg_text)

    assert len(src_sents) == len(trg_sents), \
        "num of lorelei and trg sents not match."

    return src_sents, trg_sents


def write2file(src_sents, trg_sents, src_file, trg_file):
    with codecs.open(src_file, 'w', 'utf-8') as f:
        f.write('\n'.join(src_sents))

    with codecs.open(trg_file, 'w', 'utf-8') as f:
        f.write('\n'.join(trg_sents))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("input")
    parser.add_argument("output_dir")

    args = parser.parse_args()

    elisa_file = args.input

    print("parsing elisa file..."),
    if elisa_file.endswith('.gz'):
        with gzip.open(elisa_file, 'rb') as f:
            xml_str = f.read()
    else:
        xml_str = codecs.open(args.input, 'r', 'utf-8').read()
    print("done")

    src_sents, trg_sents = elisa2parallel(xml_str)

    input_basename = os.path.basename(args.input)

    src_file = os.path.join(args.output_dir, input_basename+'.src.txt')
    trg_file = os.path.join(args.output_dir, input_basename+'.trg.txt')

    write2file(src_sents, trg_sents, src_file, trg_file)