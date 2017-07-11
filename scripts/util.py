import re
from collections import defaultdict


class TacTab(object):
    def __init__(self, runid, qid, mention, offset, kbid, etype, mtype, conf,
                 trans=None):
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
        self.trans = trans

    def __str__(self):
        return '\t'.join([self.runid, self.qid, self.mention, self.offset,
                          self.kbid, self.etype, self.mtype, self.conf])

def read_tab(ptab):
    res = []
    with open(ptab, 'r') as f:
        for line in f:
            res.append(TacTab(*line.rstrip('\n').split('\t')))
    return res


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


def read_bio(pbio):
    res = defaultdict(list)
    data = re.split('\n\s*\n', open(pbio).read())
    for i in data:
        sent = i.split('\n')
        for i, line in enumerate(sent):
            if not line:
                continue
            ann = line.split(' ')
            try:
                assert len(ann) >= 2
            except AssertionError:
                logger.error('line is less than two columns')
                logger.error(repr(line))
            tok = ann[0]
            offset = ann[1]
            m = re.match('(.+):(\d+)-(\d+)', offset)
            docid = m.group(1)
            beg = int(m.group(2))
            end = int(m.group(3))
            res[docid].append((tok, beg, end))
    return res


def get_tab_in_doc_level(tab):
    res = defaultdict(list)
    for i in tab:
        res[i.docid].append(i)
    return res


def read_gaz(pgaz):
    res = {}
    res_tree = {}
    with open(pgaz, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[0]
            etype = tmp[1]
            if len(tmp) > 2:
                add_info = tmp[2]
            else:
                add_info = None
            if mention in res:
                assert res[mention][0] == etype
            res[mention] = (etype, add_info)

            toks = mention.split(' ')
            tree = res_tree
            for tok in toks:
                if tok not in tree:
                    tree[tok] = {}
                tree = tree[tok]
    return res, res_tree


def read_rule(prule):
    res = defaultdict(dict)
    with open(prule, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[0]
            etype = tmp[1]
            operate = (tmp[2], tmp[3:])
            res[mention][etype] = operate
    return res
