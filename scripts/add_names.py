import re
import sys
import logging
from collections import defaultdict
import argparse

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)


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


def add_poster_author(bio, psm):
    res = []
    count = 0
    for docid in bio:
        if 'DF_' not in docid:
            continue
        for tok, beg, end in bio[docid]:
            if tok in psm[docid]:
                offset = '%s:%s-%s' % (docid, beg, end)
                qid = 'DFPA_' + '{number:0{width}d}'.format(width=7,
                                                            number=count)
                kbid = 'NIL'
                etype = 'PER'
                mtype = 'NAM'
                conf = '1.0'
                res.append(TacTab('DF_poster_author', qid, tok,
                                  offset, kbid, etype, mtype, conf))
                count += 1
    return res


def add_gazetteer(bio, gaz, gaz_tree):
    res = []
    count = 0
    for docid in bio:
        for i, (tok, beg, end) in enumerate(bio[docid]):
            if tok in gaz_tree:
                tree = gaz_tree[tok]
                mention = [tok]
                offset = [(beg, end)]
                for j, (next_tok, next_beg, next_end) \
                    in enumerate(bio[docid][i+1:]):
                    if next_tok in tree:
                        tree = tree[next_tok]
                        mention.append(next_tok)
                        offset.append((next_beg, next_end))
                    else:
                        break
                mention = ' '.join(mention)
                if mention in gaz:
                    offset = '%s:%s-%s' % (docid, offset[0][0], offset[-1][1])
                    qid = 'GAZ_' + '{number:0{width}d}'.format(width=7,
                                                               number=count)
                    kbid = 'NIL'
                    etype = gaz[mention][0]
                    mtype = 'NAM'
                    conf = '1.0'
                    trans = gaz[mention][1]
                    res.append(TacTab('Gazetterr', qid, tok, offset, kbid,
                                      etype, mtype, conf, trans=trans))
                    count += 1
    return res




def check_overlap(main_tab, added_tab):
    duplicate_tab = []
    overlapped_tab = []
    checked_tab = []
    main_tab_doc = get_tab_in_doc_level(main_tab)
    for i in added_tab:
        overlapped = False
        for j in main_tab_doc[i.docid]:
            if (i.beg, i.end) == (j.beg, j.end):
                duplicate_tab.append(i)
                overlapped = True
                break
            if j.beg <= i.beg <= j.end:
                overlapped_tab.append(i)
                overlapped = True
                break
            elif j.beg <= i.end <= j.end:
                overlapped_tab.append(i)
                overlapped = True
                break
        if not overlapped:
            checked_tab.append(i)
    return checked_tab, duplicate_tab, overlapped_tab


def process(tab, pbio, outpath=None, ppsm=None, pgaz=None):
    bio = read_bio(pbio)

    # if ppsm:
    #     psm = read_psm(ppsm)
    #     added_tab = add_poster_author(bio, psm)
    #     logger.info('%s df poster authors found' % (len(added_tab)))
    #     logger.info('checking overlapped mentions...')
    #     r = check_overlap(tab, added_tab)
    #     checked_tab, duplicate_tab, overlapped_tab = r
    #     logger.info('duplicate mentions: %s' % (len(duplicate_tab)))
    #     logger.info('overlapped mentions: %s' % (len(overlapped_tab)))
    #     logger.info('%s df poster authors added' % (len(checked_tab)))
    #     tab += checked_tab

    if pgaz:
        gaz, gaz_tree = read_gaz(pgaz)
        added_tab = add_gazetteer(bio, gaz, gaz_tree)
        logger.info('%s gaz names found' % (len(added_tab)))
        logger.info('checking overlapped mentions...')
        r = check_overlap(tab, added_tab)
        checked_tab, duplicate_tab, overlapped_tab = r
        logger.info('duplicate mentions: %s' % (len(duplicate_tab)))
        logger.info('overlapped mentions: %s' % (len(overlapped_tab)))
        logger.info('%s gaz names added' % (len(checked_tab)))
        tab += checked_tab

    if outpath:
        with open(outpath, 'w') as fw:
            fw.write('\n'.join([str(i) for i in tab]))
    else:
        return tab


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ptab', type=str, help='path to tab')
    parser.add_argument('pbio', type=str, help='path to bio')
    parser.add_argument('outpath', type=str, help='output path')
    parser.add_argument('--ppsm', type=str, help='path to psm')
    parser.add_argument('--pgaz', type=str, help='path to gaz')
    args = parser.parse_args()

    tab = read_tab(args.ptab)
    process(tab, args.pbio,
            ppsm=args.ppsm, pgaz=args.pgaz,
            outpath=args.outpath)
