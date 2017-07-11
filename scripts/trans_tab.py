import os
import sys
import re
from collections import defaultdict
import itertools
import logging


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)


def read_dic(pdic):
    RE_STRIP = r' \([^)]*\)|\<[^)]*\>|,|"|\.|\'|:|-'
    res = defaultdict(lambda : defaultdict(int))
    with open(pdic, 'r') as f:
        for line in f:
            src, trg = line.rstrip('\n').split('\t')
            # trg = ' '.join(re.sub(RE_STRIP, '', trg).strip().split())
            res[src][trg] += 1
    for i in res:
        res[i] = [x for x, y in sorted(res[i].items(),
                                       key=lambda x: x[1], reverse=True)]
    return res


def isListEmpty(inList):
    if isinstance(inList, list):
        return all(map(isListEmpty, inList))
    return False


def partial_trans(mention, dic):
    res = []
    trans_toks = []
    for tok in mention.split(' '):
        if tok in dic:
            trans_toks.append([list(dic[tok])[0]])
        else:
            trans_toks.append([])

    if not isListEmpty(trans_toks):
        for n in range(len(trans_toks)):
            if not trans_toks[n]:
                trans_toks[n] = ['NULL']
        for i in list(itertools.product(*trans_toks)):
            res.append(' '.join(i))
        return '*' + '|'.join(res)
    return None


def main(pdic, tab, outpath=None):
    logger.info('loading dict...')
    dic = read_dic(pdic)
    logger.info('dict size: %s' % len(dic))

    count = {
        'tol': 0,
        'trans': 0
    }

    for i, line in enumerate(tab):
        if not line:
            continue
        tmp = line.rstrip('\n').split('\t')
        mention = tmp[2]
        trans = None
        if mention in dic:
            trans = '|'.join(dic[mention])
        else:
            trans = partial_trans(mention, dic)
        if not trans:
            trans = 'NULL'
        else:
            count['trans'] += 1
        count['tol'] += 1

        tmp.append(trans)
        tab[i] = '\t'.join(tmp)

    logger.info('# of translated mentions: %s' % count['trans'])
    logger.info('# of total mentions: %s' % count['tol'])

    if outpath:
        with open(outpath, 'w') as fw:
            fw.write('\n'.join(tab))
    else:
        return tab


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('USAGE: <path to dict> <path to tab> <output path>')
        sys.exit()

    pdic = sys.argv[1]
    ptab = sys.argv[2]
    outpath = sys.argv[3]
    tab = open(ptab, 'r').read().split('\n')
    main(pdic, tab, outpath)
