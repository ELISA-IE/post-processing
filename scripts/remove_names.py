import re
import sys
import logging
import string
import argparse
from collections import defaultdict


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
LONG_NAME_THRES = 10


class TacTab(object):
    def __init__(self, runid, qid, mention, offset, kbid, etype, mtype, conf):
        self.runid = runid
        self.qid = qid
        self.mention = mention
        self.offset = offset
        self.docid = re.match('(.+):(\d+)-(\d+)', offset).group(1)
        self.beg = int(re.match('(.+):(\d+)-(\d+)', offset).group(2))
        self.end = int(re.match('(.+):(\d+)-(\d+)', offset).group(3))
        self.kbid = kbid
        self.etype = etype
        self.mtype = mtype
        self.conf = conf

    def __str__(self):
        return '\t'.join([self.runid, self.qid, self.mention, self.offset,
                          self.kbid, self.etype, self.mtype, self.conf])

def read_tab(ptab):
    tab = []
    with open(ptab, 'r') as f:
        for line in f:
            tab.append(TacTab(*line.rstrip('\n').split('\t')))
    return tab


def read_psm(ppsm):
    res = defaultdict(set)
    with open(ppsm, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            if tmp[0] == 'post':
                docid = tmp[1]
                poster = tmp[4]
                res[docid].add(poster)
    return res


def process(tab, outpath=None, ppsm=None, verbose=True):
    new_tab = []
    histories = []
    psm = None
    if ppsm:
        psm = read_psm(ppsm)

    for i in tab:
        remove = False

        # 1. Is digits
        if i.mention.isdigit():
            if psm and i.docid in psm and i.mention in psm[i.docid]:
                pass
            else:
                histories.append(('IS_DIGITS', i))
                remove = True
                continue

        # 2. Is punctuation
        translation = str.maketrans('', '', string.punctuation);
        s = i.mention.translate(translation)
        if s == '':
            histories.append(('IS_PUNCT', i))
            remove = True
            continue

        # 3. Contains HTTP
        if re.search('http', i.mention):
            histories.append(('HAS_HTTP', i))
            remove = True
            continue

        # 4. Contains digits
        if re.search('\d+', i.mention):
            if psm and i.docid in psm and i.mention in psm[i.docid]:
                pass
            else:
                histories.append(('HAS_DIGITS', i))
                remove = True
                continue

        # 5. Long names
        if len(i.mention.split()) >= LONG_NAME_THRES:
            histories.append(('IS_LONG(%s)' % LONG_NAME_THRES, i))
            remove = True
            continue

        # 0. Hard rules
        if re.search('\d+\:\d+|\d+\:\d+\:\d+', i.mention):
            histories.append(('HARD_RULE', i))
            remove = True
        if re.search('.+\.jpg', i.mention):
            histories.append(('HARD_RULE', i))
            remove = True

        if not remove:
            new_tab.append(i)

    if verbose:
        logger.info('%s names are removed' % len(histories))
        for r, i in sorted(histories, key=lambda x: x[0]):
            logger.info('%s\t%s\t%s\t%s' % (r, i.etype, i.offset, i.mention))

    if outpath:
        with open(outpath, 'w') as fw:
            fw.write('\n'.join([str(i) for i in new_tab]))
    else:
        return new_tab


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ptab', type=str, help='path to tab')
    parser.add_argument('outpath', type=str, help='output path')
    parser.add_argument('--ppsm', type=str, help='path to psm')
    args = parser.parse_args()

    tab = read_tab(args.ptab)
    process(tab, outpath=args.outpath, ppsm=args.ppsm)
