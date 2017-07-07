import os
import sys
import re
import collections
import itertools
import logging


class OrderedSet(collections.MutableSet):
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]
        self.map = {}
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


def read_dic(pdic):
    dic = {}
    with open(pdic, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            if tmp[0] not in dic:
                dic[tmp[0]] = OrderedSet()
            dic[tmp[0]].add(tmp[1])
    return dic


def isListEmpty(inList):
    if isinstance(inList, list):
        return all( map(isListEmpty, inList) )
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


def main(pdic, ptab, outpath):
    logger.info('loading dict...')
    dic = read_dic(pdic)
    logger.info('dict size: %s' % len(dic))

    count = {
        'tol': 0,
        'trans': 0
    }
    out = open(outpath, 'w')
    for line in open(ptab):
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
        out.write('\t'.join(tmp) + '\n')

    logger.info('# of translated mentions: %s' % count['trans'])
    logger.info('# of total mentions: %s' % count['tol'])


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('USAGE: python foo.py <path to dic> <path to tab> <output path>')
        sys.exit()

    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    pdic = sys.argv[1]
    ptab = sys.argv[2]
    outpath = sys.argv[3]
    main(pdic, ptab, outpath)
