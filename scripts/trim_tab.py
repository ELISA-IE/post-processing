#!/usr/bin/env python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import re
import sys
import logging
import string


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)


def main(ptab, outpath='', verbose=True):
    res = []
    history = []
    count = 0
    with open(ptab, 'r') as f:
        for line in open(ptab):
            tmp = line.strip().split('\t')
            mention = tmp[2]
            etype = tmp[5]
            offset = tmp[3]
            m = re.match('(.+):(\d+)-(\d+)', offset)
            docid = m.group(1)
            remove = False

            # 1. Is digits
            if mention.isdigit():
                history.append('REMOVE: DIGITS\t%s\t%s\t%s' % \
                               (etype, offset, mention))
                remove = True
                count += 1
                continue

            # Is punctuation
            translation = str.maketrans('', '', string.punctuation);
            s = mention.translate(translation)
            if s == '':
                history.append('REMOVE: PUNCTUATION\t%s\t%s\t%s' % \
                               (etype, offset, mention))
                remove = True
                count += 1
                continue

            # 2. Contain HTTP
            if re.search('http', mention):
                history.append('REMOVE: HTTP\t%s\t%s\t%s' % \
                               (etype, offset, mention))
                remove = True
                count += 1
                continue

            # 3. Contain digits
            if re.search('\d+', mention):
                if not mention.startswith('@'):
                # if not mention.startswith('@') and \
                #    mention.decode('utf-8') not in poster:
                    history.append('REMOVE: DIGITS\t%s\t%s\t%s' % \
                                   (etype, offset, mention))
                    remove = True
                    count += 1
                    continue

            # 4. Long names
            if len(mention.split()) > 8:
                # history.append('REMOVE: LONG(8)\t%s\t%s\t%s' % \
                #                (etype, tmp[3], mention))
                remove = True
                count += 1
                continue

            # 0. Hard rules
            if re.search('\d+\:\d+', mention):
                if not mention.startswith('@'):
                # if not mention.startswith('@') and \
                #    mention.decode('utf-8') not in poster:
                    history.append('REMOVE: HARD\t%s\t%s\t%s' % \
                                   (etype, offset, mention))
                    count += 1
                    remove = True
            if re.search('.+\.jpg', mention):
                history.append('REMOVE: HARD\t%s\t%s\t%s' % \
                               (etype, offset, mention))
                count += 1
                remove = True

            if not remove:
                res.append(line.strip())

    if verbose:
        for i in sorted(history):
            logger.info(i)
        logger.info('%s names are deleted' % count)

    if outpath:
        out = open(outpath, 'w')
        out.write('\n'.join(res))
        out.close()
    else:
        return res


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
