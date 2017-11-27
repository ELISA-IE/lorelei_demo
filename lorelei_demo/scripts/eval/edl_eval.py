# this script:
# 1. evaluates entity discovery and linking results. It takes tab or bio as
# input.
# 2. prints stats of the input and reference files.
# 3. runs error analysis of 5 error types.

import argparse
import codecs
import collections
import os
import sys

# dirty import from parent class
script_dirname = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dirname, os.pardir, 'format_converter'))
from bio2tab import bio2tab


#
# evaluate EDL performance
#
def evaluate(input_tab_str, ref_tab_str):
    # parse tab str into tab dict
    input_tab = parse_tab_str(input_tab_str)
    ref_tab = parse_tab_str(ref_tab_str)

    # count entry num by entity type
    input_counts = count_by_etype(input_tab)
    ref_counts = count_by_etype(ref_tab)

    # check correct input entry for each type
    correct_input_counts = {}
    for offset, entry in input_tab.items():
        entity_type = entry[2]

        if offset in ref_tab and entry[2] == ref_tab[offset][2]:
            try:
                correct_input_counts[entity_type] += 1
            except KeyError:
                correct_input_counts[entity_type] = 1

    # compute p, r, f scores for each type
    scores = collections.OrderedDict()
    for etype, ref_num in sorted(ref_counts.items()):
        if etype not in input_counts:
            input_num = 0
        else:
            input_num = input_counts[etype]
        if etype not in correct_input_counts:
            correct_input_num = 0
        else:
            correct_input_num = correct_input_counts[etype]
        if input_num == 0 or correct_input_num == 0:
            scores[etype] = (0, 0, 0)
        else:
            p = float(correct_input_num) / input_num
            r = float(correct_input_num) / ref_num
            f = 2 * p * r / (p + r)
            scores[etype] = (p, r, f)

    # compute overall p, r, f scores
    if not input_counts or not sum(correct_input_counts.values()):
        scores['overall'] = [0, 0, 0]
    else:
        p_overall = \
            float(sum(correct_input_counts.values())) / sum(input_counts.values())
        r_overall = \
            float(sum(correct_input_counts.values())) / sum(ref_counts.values())
        f_overall = 2 * p_overall * r_overall / (p_overall + r_overall)
        scores['overall'] = [p_overall, r_overall, f_overall]

    return scores


# count entries by entity type
def count_by_etype(tab_dict):
    counts = {}
    for offset, entry in tab_dict.items():
        _, _, entity_type = entry
        try:
            counts[entity_type] += 1
        except KeyError:
            counts[entity_type] = 1

    return counts


def split_data(input_bio_str, input_tab_str, ref_bio_str, ref_tab_str):
    input_bio = split_bio_by_doc(input_bio_str)
    ref_bio = split_bio_by_doc(ref_bio_str)
    input_tab = split_tab_by_doc(input_tab_str)
    ref_tab = split_tab_by_doc(ref_tab_str)

    # if no name found in a doc, make tab empty
    for d_id in input_bio:
        if d_id not in input_tab:
            input_tab[d_id] = ''

    for d_id in ref_bio:
        if d_id not in ref_tab:
            ref_tab[d_id] = ''

    return input_bio, ref_bio, input_tab, ref_tab


def split_bio_by_doc(bio_str):
    bio = {}
    for sent in bio_str.split('\n\n'):
        sent = sent.strip()
        if not sent:
            continue
        doc_id = sent.splitlines()[0].split()[1].split(':')[0]
        try:
            bio[doc_id].append(sent)
        except KeyError:
            bio[doc_id] = [sent]

    for doc_id, sents in bio.items():
        bio[doc_id] = '\n\n'.join(sents)

    return bio


def split_tab_by_doc(tab_str):
    tab = {}
    for line in tab_str.splitlines():
        if not line:
            continue
        doc_id = line.split('\t')[3].split(':')[0]
        try:
            tab[doc_id].append(line)
        except KeyError:
            tab[doc_id] = [line]

    for doc_id, lines in tab.items():
        tab[doc_id] = '\n'.join(lines)
    return tab


#
# error analysis
#
def error_analysis(input_tab_str, ref_tab_str):
    # parse tab str into tab dict
    input_tab = parse_tab_str(input_tab_str)
    ref_tab = parse_tab_str(ref_tab_str)

    # compute errors
    errors = compute_error(input_tab, ref_tab)

    return errors


def compute_error(input_tab, ref_tab):
    errors = collections.OrderedDict()
    errors['missing'] = {}
    errors['spurious'] = {}
    errors['boundary'] = {}
    errors['type'] = {}
    errors['linking'] = {}

    # convert tab dict from token level to char level
    input_tab_by_char = convert_tab_dict(input_tab)
    ref_tab_by_char = convert_tab_dict(ref_tab)

    # missing error
    for offset, entry in ref_tab.items():
        doc_id, start, end = offset
        if all(['%s:%d' % (doc_id, i) not in input_tab_by_char
                for i in range(start, end+1)]):
            errors['missing'][offset] = entry

    # spurious errors
    for offset, entry in input_tab.items():
        doc_id, start, end = offset
        if all(['%s:%d' % (doc_id, i) not in ref_tab_by_char
                for i in range(start, end+1)]):
            errors['spurious'][offset] = entry

    # boundary errors
    for offset, entry in input_tab.items():
        if offset in ref_tab:
            continue
        doc_id, start, end = offset
        if any(['%s:%d' % (doc_id, i) in ref_tab_by_char
                for i in range(start, end+1)]):
            errors['boundary'][offset] = entry

    # type errors
    for offset, entry in input_tab.items():
        if offset not in ref_tab:
            continue
        # if input entity type doesn't equal to reference entity type
        if entry[2] != ref_tab[offset][2]:
            errors['type'][offset] = entry

    # linking errors
    for offset, entry in input_tab.items():
        if offset not in ref_tab:
            continue
        # if input linking result doesn't equal to reference linking result
        if entry[1] != ref_tab[offset][1]:
            errors['linking'][offset] = entry

    return errors


def convert_tab_dict(tab_dict):
    tab_dict_by_char = {}
    for offset, entry in tab_dict.items():
        doc_id, start, end = offset
        for i in range(int(start), int(end)+1):
            tab_dict_by_char['%s:%d' % (doc_id, i)] = entry
    return tab_dict_by_char


#
# utils
#
# parse tab str into a tab dict
def parse_tab_str(tab_str):
    tab_dict = {}
    for line in tab_str.splitlines():
        line = line.strip()
        if not line:
            continue

        # parse tab line
        sys_name, mtn_id, mtn_text, offset, \
        linking, entity_type, mtn_type, conf = line.split('\t')

        doc_id, o = offset.split(':')
        start, end = o.split('-')
        offset = (doc_id, int(start), int(end))

        # check duplicate result
        if offset in tab_dict:
            print('duplicated result: %s' % line)
            continue

        tab_dict[offset] = (sys_name, linking, entity_type)

    return tab_dict


#
# compute stats
#
def stats(bio_str, tab_str):
    # bio stats
    num_sents = 0
    num_tokens = 0
    doc_ids = set()
    for sent in bio_str.split('\n\n'):
        sent = sent.strip()
        if not sent:
            continue
        tokens = sent.splitlines()
        d_id = tokens[0].split()[1].split(':')[0]
        doc_ids.add(d_id)

        num_sents += 1
        num_tokens += len(tokens)
    num_docs = len(doc_ids)

    # tab stats
    sys_name = ''
    tab = parse_tab_str(tab_str)
    num_entries_by_type = {}
    for offset, entry in tab.items():
        entity_type = entry[2]
        sys_name = entry[0]
        try:
            num_entries_by_type[entity_type] += 1
        except KeyError:
            num_entries_by_type[entity_type] = 1

    res = {}
    res['sys_name'] = sys_name
    res['num_docs'] = num_docs
    res['num_sents'] = num_sents
    res['num_tokens'] = num_tokens
    res['num_entries_by_type'] = num_entries_by_type

    return res


#
# print results
#
def print_stats(stats):
    print('=> %s stats' % stats['sys_name'])
    if stats['num_docs'] and stats['num_sents'] and stats['num_tokens']:
        print('  %d documents; %d sentences; %d tokens.' %
              (stats['num_docs'], stats['num_sents'], stats['num_tokens']))
    print('  ', end='')
    for entity_type, count in stats['num_entries_by_type'].items():
        print('%s %d' % (entity_type, count), end='; ')
    print('overall mentions %d' % sum(stats['num_entries_by_type'].values()))


def print_errors(errors):
    print('=> error analysis')
    # overall errors
    for error_type, e in errors.items():
        print(' %s: %d' % (error_type, len(e)))


def print_scores(scores):
    print('=> performance')
    print("  {:<14}{:<14}{:<14}{:<14}".format(
        'entity_type', 'precision', 'recall', 'f1'
    ))
    for etype, s in scores.items():
        print("  {:<14}{:<14.4f}{:<14.4f}{:<14.4f}".format(
            etype, s[0], s[1], s[2]
        ))

#
# main function
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_bio')
    parser.add_argument('--input_tab')
    parser.add_argument('--ref_bio')
    parser.add_argument('--ref_tab')
    parser.add_argument('-d', action="store_true", default=False,
                        help="evaluate by document level")

    args = parser.parse_args()

    assert args.input_bio or args.input_tab, 'no input found.'
    assert args.ref_bio or args.ref_tab, 'no reference found.'

    if args.input_bio:
        input_bio_str = codecs.open(args.input_bio, 'r', 'utf-8').read()
        input_tab_str = bio2tab(input_bio_str)
    elif args.input_tab:
        input_bio_str = ''
        input_tab_str = codecs.open(args.input_tab, 'r', 'utf-8').read()

    if args.ref_bio:
        ref_bio_str = codecs.open(args.ref_bio, 'r', 'utf-8').read()
        ref_tab_str = bio2tab(ref_bio_str)
    elif args.ref_tab:
        ref_bio_str = ''
        ref_tab_str = codecs.open(args.ref_tab, 'r', 'utf-8').read()

    if args.d:
        input_bio, ref_bio, input_tab, ref_tab = split_data(
            input_bio_str, input_tab_str, ref_bio_str, ref_tab_str
        )
        overall_input_stats = {}
        overall_ref_stats = {}
        overall_scores = {}
        overall_errors = {}
        for doc_id in ref_bio:
            if doc_id not in input_tab:
                input_tab[doc_id] = ''
            if doc_id not in input_bio:
                input_bio[doc_id] = ''

            # ref stats
            input_stats = stats(input_bio[doc_id], input_tab[doc_id])
            ref_stats = stats(ref_bio[doc_id], ref_tab[doc_id])
            overall_input_stats[doc_id] = input_stats
            overall_ref_stats[doc_id] = ref_stats

            # evaluate tab
            scores = evaluate(input_tab[doc_id], ref_tab[doc_id])

            # error analysis
            errors = error_analysis(input_tab[doc_id], ref_tab[doc_id])

            overall_scores[doc_id] = scores
            overall_errors[doc_id] = errors

        # sort overall score by f1
        sorted_overall_scores = sorted(overall_scores.items(),
                                       key=lambda x: x[1]['overall'][2],
                                       reverse=True)

        # print results
        for doc_id, _ in sorted_overall_scores:
            print('########### %s ###########' % doc_id)
            print_stats(overall_input_stats[doc_id])
            print_stats(overall_ref_stats[doc_id])
            print_scores(overall_scores[doc_id])
            print_errors(overall_errors[doc_id])
            print('\n')

    else:
        # ref stats
        input_stats = stats(input_bio_str, input_tab_str)
        ref_stats = stats(ref_bio_str, ref_tab_str)
        print_stats(input_stats)
        print_stats(ref_stats)

        # evaluate tab
        scores = evaluate(input_tab_str, ref_tab_str)
        print_scores(scores)

        # error analysis
        errors = error_analysis(input_tab_str, ref_tab_str)
        print_errors(errors)
