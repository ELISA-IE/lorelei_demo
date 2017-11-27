import sys


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('USAGE <path to tab file>')
        exit()

    docids = set()
    with open(sys.argv[1], 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            docid = tmp[3].split(':')[0]
            docids.add(docid)

    outpath = sys.argv[1].split('/')[:-1]
    outpath.append('filelist.txt')
    outpath = '/'.join(outpath)
    with open(outpath, 'w') as fw:
        for docid in sorted(docids):
            fw.write('%s\tTRUE\n' % (docid))
    print('# of docs: %s' % len(docids))
