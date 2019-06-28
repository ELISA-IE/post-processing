import re
import sys
import logging
import argparse
import string
import itertools
from collections import defaultdict

import util
from util import TacTab


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)


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


def add_gazetteer(bio, gaz, gaz_tree, des=None):
    res_trusted = []
    res_untrusted = []
    count = 0
    for docid in bio:
        for i, (tok, beg, end) in enumerate(bio[docid]):
            if tok in gaz_tree:
                tree = gaz_tree[tok]
                mention = [tok]
                offset = [(beg, end)]
                for j, (next_tok, next_beg, next_end) in \
                    enumerate(bio[docid][i+1:]):
                    if next_tok in tree:
                        tree = tree[next_tok]
                        mention.append(next_tok)
                        offset.append((next_beg, next_end))
                    else:
                        break
                mention = ' '.join(mention)
                if mention in gaz:
                    etype, op, additional_info = gaz[mention]

                    if des:
                        prev_tok, prev_beg, prev_end = bio[docid][i-1]
                        if prev_tok in des:
                            etype = des[prev_tok][0]
                            mention = '%s %s' % (prev_tok, mention)
                            offset = [(prev_beg, prev_end)] + offset

                    offset = '%s:%s-%s' % (docid, offset[0][0], offset[-1][1])
                    qid = 'GAZ_' + '{number:0{width}d}'.format(width=7,
                                                               number=count)
                    kbid = 'NIL'
                    mtype = 'NAM'
                    conf = '1.0'
                    trans = additional_info
                    tt = TacTab('Gazetterr', qid, mention, offset, kbid,
                                etype, mtype, conf, trans=trans)
                    if op == 'p':
                        res_trusted.append(tt)
                    elif op == 'p2':
                        res_untrusted.append(tt)
                    else:
                        logger.error('unrecognized op: %s' % op)
                        exit()
                    count += 1
    return res_trusted, res_untrusted


def add_sn(bio, gaz=None):
    res = []
    count = 0
    for docid in bio:
        if 'SN_' not in docid:
            continue
        for i, (tok, beg, end) in enumerate(bio[docid]):
            if tok.startswith('#'):
                name = tok[1:]
                if name.isdigit():
                    continue
                translation = str.maketrans('', '', string.punctuation);
                if name.translate(translation) == '':
                    continue
                if '#' in name or '@' in name:
                    continue
                mention = tok
                offset = '%s:%s-%s' % (docid, beg, end)
                qid = 'SNHASH_' + '{number:0{width}d}'.format(width=7,
                                                              number=count)
                kbid = 'NIL'
                additional_info = None
                if gaz and mention in gaz:
                    etype, op, additional_info = gaz[mention]
                    if etype == '-':
                        continue
                else:
                    etype = 'GPE'
                mtype = 'NAM'
                conf = '1.0'
                res.append(TacTab('SN_HASH', qid, mention, offset, kbid,
                                  etype, mtype, conf, trans=additional_info))
                count += 1

            if tok.startswith('@'):
                name = tok[1:]
                if name.isdigit():
                    continue
                translation = str.maketrans('', '', string.punctuation);
                if name.translate(translation) == '':
                    continue
                if '#' in name or '@' in name:
                    continue
                mention = tok
                offset = '%s:%s-%s' % (docid, beg, end)
                qid = 'SNAT_' + '{number:0{width}d}'.format(width=7,
                                                            number=count)
                kbid = 'NIL'
                additional_info = None
                if gaz and mention in gaz:
                    etype, op, additional_info = gaz[mention]
                    if etype == '-':
                        continue
                else:
                    etype = 'PER'
                mtype = 'NAM'
                conf = '1.0'
                res.append(TacTab('SN_AT', qid, mention, offset, kbid,
                                  etype, mtype, conf, trans=additional_info))
                count += 1
    return res


def check_conflicts_single_tab(tab):
    new_tab = []
    tab_doc = util.get_tab_in_doc_level(tab)
    overlapped_pair = []
    for docid in tab_doc:
        for i, j in itertools.combinations(tab_doc[docid], 2):
            if j.beg <= i.beg <= j.end or j.beg <= i.end <= j.end:
                overlapped_pair.append((i, j))

    dropped_tab = set()
    for i, j in overlapped_pair:
        # Select longer names
        if len(i.mention.split(' ')) < len(j.mention.split(' ')):
            dropped_tab.add(i)
        else:
            dropped_tab.add(j)

    for i in tab:
        if i not in dropped_tab:
            new_tab.append(i)

    logger.info('  # of names in the tab: %s' % len(tab))
    logger.info('  checking conflicted names...')
    logger.info('  %s overlapped matched names, select longer names' \
                % (len(tab) - len(new_tab)))
    return new_tab


def check_conflicts_duo_tab(tab, tab_to_add, trust_new=False, must_longer=True,
                            verbose=False):
    duplicate_tab = []
    overlapped_tab = []
    non_overlapped_tab = []
    count = defaultdict(int)
    logger.info('  # of names in the original tab: %s' % len(tab))
    logger.info('  # of names in the addtional tab: %s' % len(tab_to_add))
    logger.info('  checking conflicted names...')
    tab_doc = util.get_tab_in_doc_level(tab)
    for i in tab_to_add:
        overlapped = False
        for j in tab_doc[i.docid]:
            # if (i.beg, i.end) == (j.beg, j.end) and i.etype == j.etype:
            if (i.beg, i.end) == (j.beg, j.end):
                duplicate_tab.append((i, j))
                overlapped = True
                break
            if max(i.beg, j.beg) < min(i.end, j.end):
                overlapped_tab.append((i, j))
                overlapped = True
        if not overlapped:
            non_overlapped_tab.append(i)

    logger.info('  # of duplicate names: %s' % (len(duplicate_tab)))
    logger.info('  # of overlapped names: %s' % (len(overlapped_tab)))
    if trust_new:
        logger.info('TRUST NEW NAMES')
        new_main_tab = []

        # to_add = list(set([i[0] for i in overlapped_tab]))
        # to_remove = [i[1].offset for i in overlapped_tab]
        to_add = []
        to_remove = []
        for i, j in overlapped_tab:
            if must_longer and len(i.mention) < len(j.mention):
                continue
            to_add.append(i)
            to_remove.append(j.offset)
        to_add = list(set(to_add))
        if verbose:
            logger.info('verbose...')
            overlapped_tab_count = defaultdict(int)
            for i, j in overlapped_tab:
                if must_longer and len(i.mention) < len(j.mention):
                    continue
                m = "'%s' %s -> '%s' %s" % (j.mention, j.etype,
                                            i.mention, i.etype)
                overlapped_tab_count[m] += 1
            for m, c in sorted(overlapped_tab_count.items(),
                               key=lambda x: x[1], reverse=True):
                msg = '    %s | %s' % (m, c)
                logger.info(msg)
        for i in tab:
            if i.offset not in to_remove:
                new_main_tab.append(i)
        logger.info('  # of names revised: %s' % (len(to_add)))

        new_main_tab += to_add
        new_main_tab += non_overlapped_tab
        if verbose:
            logger.info('verbose...')
            for i in to_add:
                count[(i.mention, i.etype, i.trans)] += 1
            for i in non_overlapped_tab:
                count[(i.mention, i.etype, i.trans)] += 1
            for i, c in sorted(count.items(), key=lambda x: x[1], reverse=True):
                logger.info('  %s | %s | %s | %s' % (i[0], i[1], i[2], c))
        logger.info('  # of names added: %s' % (len(non_overlapped_tab)))
        logger.info('  # of names revised: %s' % (len(to_add)))
        return new_main_tab
    else:
        logger.info('TRUST ORIGINAL NAMES')
        tab += non_overlapped_tab
        if verbose:
            logger.info('verbose...')
            for i in non_overlapped_tab:
                count[(i.mention, i.etype, i.trans)] += 1
            for i, c in sorted(count.items(), key=lambda x: x[1], reverse=True):
                logger.info('  %s | %s | %s | %s' % (i[0], i[1], i[2], c))
        logger.info('  # of names added: %s' % len(non_overlapped_tab))
        return tab


def revise_etype(tab, gaz, verbose=False):
    tol = 0
    count = defaultdict(int)
    for i in tab:
        if i.mention in gaz and i.etype != gaz[i.mention][0]:
            count[(i.mention, i.etype, gaz[i.mention][0])] += 1
            i.etype = gaz[i.mention][0]
            tol += 1
    logger.info('# of revised etypes: %s' % tol)
    if verbose:
        logger.info('verbose...')
        for i, c in sorted(count.items(), key=lambda x: x[1], reverse=True):
            logger.info('  %s | %s -> %s | %s' % (i[0], i[1], i[2], c))


def process(tab, pbio, outpath=None, sn=True, lower=False,
            ppsm=None, pgaz=None, psn=None, pdes=None):
    bio = util.read_bio(pbio)
    logger.info('\n------ ADDING NAMES ------')

    if ppsm:
        logger.info('\n--- ADDING df poster authors ---')
        psm = util.read_psm(ppsm)
        tab_to_add = add_poster_author(bio, psm)
        logger.info('# of df poster authors found: %s' % (len(tab_to_add)))
        tab = check_conflicts_duo_tab(tab, tab_to_add, trust_new=True)

    if pgaz:
        logger.info('\n--- ADDING gazetterrs ---')
        if pdes:
            des, des_tree = util.read_gaz(pdes, lower=lower)
        else:
            des = None
        gaz, gaz_tree = util.read_gaz(pgaz, lower=lower)
        logger.info('loading gazetterrs...')
        tab_to_add_p, tab_to_add_p2 = add_gazetteer(bio, gaz, gaz_tree, des=des)
        logger.info('checking trusted (p) names...')
        tab_to_add_p = check_conflicts_single_tab(tab_to_add_p)
        logger.info('checking untrusted (p2) names...')
        tab_to_add_p2 = check_conflicts_single_tab(tab_to_add_p2)
        logger.info('-- trusted (p) names found: %s' % (len(tab_to_add_p)))
        tab = check_conflicts_duo_tab(tab, tab_to_add_p, trust_new=True,
                                      verbose=True)
        logger.info('-- untrusted (p2) names found: %s' % (len(tab_to_add_p2)))
        tab = check_conflicts_duo_tab(tab, tab_to_add_p2, trust_new=False,
                                      verbose=True)

        logger.info('\n--- REVISING entity types ---')
        revise_etype(tab, gaz, verbose=True)

    if sn:
        logger.info('\n--- ADDING social network names ---')
        if psn:
            gaz, gaz_tree = util.read_gaz(psn, lower=lower)
        else:
            gaz = None
        tab_to_add = add_sn(bio, gaz=gaz)
        logger.info('# of SN names found: %s' % (len(tab_to_add)))
        tab = check_conflicts_duo_tab(tab, tab_to_add, trust_new=True,
                                      verbose=True)

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
    parser.add_argument('--pdes', type=str, help='path to des')
    args = parser.parse_args()

    tab = util.read_tab(args.ptab)
    process(tab, args.pbio,
            ppsm=args.ppsm, pgaz=args.pgaz, pdes=args.pdes,
            outpath=args.outpath)
