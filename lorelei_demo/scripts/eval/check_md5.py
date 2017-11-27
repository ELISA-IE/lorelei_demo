import hashlib
import os
import sys


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


if __name__ == '__main__':
    indir = sys.argv[1]
    extension = sys.argv[2]
    for i in sorted(os.listdir(indir)):
        if i.endswith(extension):
            print(i, md5('%s/%s' % (indir, i)))
