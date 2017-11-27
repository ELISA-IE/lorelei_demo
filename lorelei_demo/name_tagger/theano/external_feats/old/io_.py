#encoding=utf-8

import io
import os
import tempfile
import shutil
import subprocess
import itertools
import xml.etree.ElementTree as ET
from fb_intern.name_taggers.dnn import elisa_ie_root


# ============ load gazetteers ============ #
def load_gaz(il, combined=True):
    gaz = dict()
    gaz_dir = os.path.join(elisa_ie_root, 'data/name_taggers/dnn/gaz/%s' % il)

    if not combined:
        # load gazetteers separately
        for fn in os.listdir(gaz_dir):
            if '.dic' in fn:
                gaz[fn] = parse_dict(os.path.join(gaz_dir, fn))
            elif '.txt' in fn:
                gaz[fn] = parse_gazetteer(os.path.join(gaz_dir, fn))

    elif combined:
        # combine same type gazetteers
        per_set = set()
        gpe_set = set()
        org_set = set()
        loc_set = set()

        per_gaz_fn = ['giga_per.txt', 'per.txt', 'per_uig_wiki.txt', 'self_training_per.txt']
        gpe_gaz_fn = ['giga_gpe.txt', 'gpe_uig_wiki.txt', 'self_training_gpe.txt', 'oov_gpe.txt',
                      'related_gpe.txt', 'xinjiang_gpe.txt']
        org_gaz_fn = ['giga_org.txt', 'org_uig_wiki.txt', 'related_org.txt']
        loc_gaz_fn = ['loc.txt', 'loc_uig_wiki.txt', 'related_loc.txt', 'context_xinjiang_loc']

        for fn in os.listdir(os.path.join(gaz_dir, 'cleaned_gaz')):
            if 'txt' not in fn or 'dic' not in fn:
                continue
            if fn in gpe_gaz_fn:
                s = gpe_set
                gaz_type = 'il_gpe'
            elif fn in org_gaz_fn:
                s = org_set
                gaz_type = 'il_org'
            elif fn in per_gaz_fn:
                s = per_set
                gaz_type = 'il_per'
            elif fn in loc_gaz_fn:
                s = loc_set
                gaz_type = 'il_loc'
            else:
                continue

            # parse gazetteers
            for line in io.open(os.path.join(gaz_dir, fn), 'r', -1, 'utf-8').read().splitlines():
                if line.strip():
                    s.add(line.strip())
            gaz[gaz_type] = s

    return gaz


def parse_gazetteer(gaz_fp):
    s = set()
    f = []
    for encoding in ['utf-8', 'GB2312', 'GBK']:
        try:
            f = io.open(gaz_fp, 'r', -1, encoding).read().splitlines()
        except UnicodeDecodeError:
            continue

    for line in f:
        s.add(line.strip())

    return s


def parse_dict(dict_fp):
    s = set()
    f = []
    for encoding in ['utf-8', 'GB2312', 'GBK']:
        try:
            f = io.open(dict_fp, 'r', -1, encoding).read().splitlines()
            break
        except UnicodeDecodeError:
            continue

    for line in f:
        s.add(line.strip().split('|')[0])

    return s


def get_combination_and_permutation(iterable, combination_r):
    combinations = itertools.combinations(iterable, combination_r)

    res = []
    for c in combinations:
        res += itertools.permutations(c)

    return [''.join(item) for item in res]



