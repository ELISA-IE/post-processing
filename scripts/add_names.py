import re
import sys
import logging
import argparse
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
                    res.append(TacTab('Gazetterr', qid, mention, offset, kbid,
                                      etype, mtype, conf, trans=trans))
                    count += 1
    return res


def check_conflict(main_tab, added_tab, trust_new=False, verbose=False):
    duplicate_tab = []
    overlapped_tab = []
    checked_tab = []
    logger.info('checking conflicted names...')
    main_tab_doc = util.get_tab_in_doc_level(main_tab)
    for i in added_tab:
        overlapped = False
        for j in main_tab_doc[i.docid]:
            if (i.beg, i.end) == (j.beg, j.end):
                duplicate_tab.append((i, j))
                overlapped = True
                break
            if j.beg <= i.beg <= j.end:
                overlapped_tab.append((i, j))
                overlapped = True
                break
            elif j.beg <= i.end <= j.end:
                overlapped_tab.append((i, j))
                overlapped = True
                break
        if not overlapped:
            checked_tab.append(i)

    logger.info('# of duplicate names: %s' % (len(duplicate_tab)))
    logger.info('# of overlapped names: %s' % (len(overlapped_tab)))
    if trust_new:
        logger.info('  trust new names')
        new_main_tab = []
        to_add = [i[0] for i in overlapped_tab]
        to_remove = [i[1] for i in overlapped_tab]
        if verbose:
            for i, j in overlapped_tab:
                logger.info('%s %s -> %s %s' % (j.mention, j.trans,
                                                i.mention, i.trans))
        for i in main_tab:
            if i not in to_remove:
                new_main_tab.append(i)
        logger.info('  # of names revised: %s' % (len(to_add)))
        logger.info('  # of names added: %s' % (len(checked_tab)))
        logger.info('  # of total: %s' % (len(checked_tab) + len(to_add)))
        new_main_tab += to_add
        new_main_tab += checked_tab
        return new_main_tab
    else:
        logger.info('  trust original names')
        logger.info('# of names added: %s' % len(checked_tab))
        main_tab += checked_tab
        return main_tab


def revise_etype(tab, gaz):
    count = 0
    for i in tab:
        if i.mention in gaz and i.etype != gaz[i.mention][0]:
            i.etype = gaz[i.mention][0]
            count += 1
    logger.info('# of revised etypes: %s' % count)


def process(tab, pbio, outpath=None, ppsm=None, pgaz=None):
    bio = util.read_bio(pbio)
    logger.info('ADDING NAMES...')

    if ppsm:
        logger.info('ADDING df poster authors...')
        psm = util.read_psm(ppsm)
        added_tab = add_poster_author(bio, psm)
        logger.info('# of df poster authors found: %s' % (len(added_tab)))
        tab = check_conflict(tab, added_tab, trust_new=True)

    if pgaz:
        logger.info('ADDING gazetterrs...')
        gaz, gaz_tree = util.read_gaz(pgaz)
        added_tab = add_gazetteer(bio, gaz, gaz_tree)
        logger.info('# of gaz names found: %s' % (len(added_tab)))
        tab = check_conflict(tab, added_tab, trust_new=True, verbose=False)

        logger.info('REVISING entity types...')
        revise_etype(tab, gaz)

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

    tab = util.read_tab(args.ptab)
    process(tab, args.pbio,
            ppsm=args.ppsm, pgaz=args.pgaz,
            outpath=args.outpath)
