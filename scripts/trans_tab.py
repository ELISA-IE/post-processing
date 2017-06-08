#!/usr/bin/env python3
import os
import sys
import re
import collections


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


def main(pdic, ptab, outpath):
    dic = read_dic(pdic)
    out = open(outpath, 'w')
    n = 0
    for line in open(ptab):
        tmp = line.rstrip('\n').split('\t')
        mention = tmp[2]
        trans = 'NULL'
        if mention in dic:
            trans = '|'.join(dic[mention])
        tmp.append(trans)
        out.write('\t'.join(tmp) + '\n')
        if trans != 'NULL':
            n += 1
    print(n)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('USAGE: python foo.py <path to dic file> <path to tab> <output path>')
        sys.exit()

    pdic = sys.argv[1]
    ptab = sys.argv[2]
    outpath = sys.argv[3]
    main(pdic, ptab, outpath)
