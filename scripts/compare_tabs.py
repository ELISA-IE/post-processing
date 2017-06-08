#!/usr/bin/env python3
import re
import sys


def read_tab(ptab):
    res = {}
    with open(ptab, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[2]
            kbid = tmp[4]
            etype = tmp[5]
            mtype = tmp[6]
            m = re.match('(.+):(\d+)-(\d+)', tmp[3])
            docid = m.group(1)
            beg = int(m.group(2))
            end = int(m.group(3))
            if docid not in res:
                res[docid] = list()
            res[docid].append((mention, kbid, etype, beg, end))
    return res


def count(tab):
    n = 0
    for docid in tab:
        n += len(tab[docid])
    return n


def read_tab_m2t(ptab):
    m2t = {}
    with open(ptab, 'r') as f:
        for line in f:
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[2]
            kbid = tmp[4]
            etype = tmp[5]
            mtype = tmp[6]
            m = re.match('(.+):(\d+)-(\d+)', tmp[3])
            docid = m.group(1)
            beg = int(m.group(2))
            end = int(m.group(3))

            if mention not in m2t:
                m2t[mention] = {}
            if etype not in m2t[mention]:
                m2t[mention][etype] = 0
            m2t[mention][etype] += 1
    return m2t


def count_mention(mention):
    n = 0
    for t in mention:
        n += mention[t]
    return n


if __name__ == '__main__':
    pa = sys.argv[1]
    pb = sys.argv[2]

    a = read_tab(pa)
    b = read_tab(pb)

    print('a: %s' % pa)
    print('b: %s' % pb)
    print('')
    print('# docs:')
    print('a: %s' % len(a))
    print('b: %s' % len(b))
    print('')
    print('# tagged names:')
    print('a: %s' % count(a))
    print('b: %s' % count(b))
    print('')

    a_m2t = read_tab_m2t(pa)
    b_m2t = read_tab_m2t(pb)
    a_names = set(a_m2t.keys())
    b_names = set(b_m2t.keys())
    print('a - b: %s' % len(a_names - b_names))
    # for i in a_names - b_names:
    #     print i
    for i in sorted(a_names - b_names, key=lambda x: count_mention(a_m2t[x]),
                    reverse=True):
        print(i, a_m2t[i])
    print('')
    print('b - a: %s' % len(b_names - a_names))
    # for i in b_names - a_names:
    #     print i
    for i in sorted(b_names - a_names, key=lambda x: count_mention(b_m2t[x]),
                    reverse=True):
        print(i, b_m2t[i])
    print('')

    print('names sort by frequence a:')
    for i in sorted(a_m2t, key=lambda x: count_mention(a_m2t[x]), reverse=True):
        print(i, a_m2t[i])
    print('')
    print('names sort by frequence b:')
    for i in sorted(b_m2t, key=lambda x: count_mention(b_m2t[x]), reverse=True):
        print(i, b_m2t[i])
    print('')
