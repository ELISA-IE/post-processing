import re
from collections import defaultdict
import logging


logger = logging.getLogger()


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
                exit()
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


def read_gaz(pgaz, lower=False):
    ETYPES = ['PER', 'ORG', 'GPE', 'LOC', 'FAC', '-', 'WEA', 'VEH', 'SID']
    res = {}
    res_tree = {}
    with open(pgaz, 'r') as f:
        for line in f:
            if not line.rstrip() or line.startswith('//'):
                continue
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[0]
            if lower:
                mention = mention.lower()
            etype = tmp[1]
            op = tmp[2]
            if len(tmp) > 3:
                additional_info = tmp[3]
            else:
                additional_info = None
            if mention in res and not lower:
                try:
                    assert etype in ETYPES
                except AssertionError:
                    msg = 'bad gaz type: %s' % (tmp)
                    logger.warning(msg)
                try:
                    assert res[mention][0] == etype
                    assert res[mention][1] == op
                except AssertionError:
                    msg = 'bad gaz: %s, conflict with %s, skip' \
                        % (tmp, res[mention])
                    logger.warn(msg)

            res[mention] = (etype, op, additional_info)

            toks = mention.split(' ') # TO-DO: no space langs
            tree = res_tree
            for tok in toks:
                if tok not in tree:
                    tree[tok] = {}
                tree = tree[tok]
    return res, res_tree


def read_rule(prule, lower=False):
    ETYPES = ['PER', 'ORG', 'GPE', 'LOC', 'ALL']
    OPS = ['mv', 'rm', 'in_rm']
    res = defaultdict(dict)
    with open(prule, 'r') as f:
        for line in f:
            if not line.rstrip() or line.startswith('//'):
                continue
            tmp = line.rstrip('\n').split('\t')
            mention = tmp[0]
            if lower:
                mention = mention.lower()
            etype = tmp[1]
            try:
                assert etype in ETYPES
            except AssertionError:
                logger.error('bad rule: %s' % tmp)
                exit()
            operate = (tmp[2], tmp[3:])
            assert operate[0] in OPS
            if operate[0] == 'mv':
                assert operate[1][0] in ETYPES
            res[mention][etype] = operate
    return res
