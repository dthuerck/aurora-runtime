import os
import os.path
import urllib.request
from lxml import html, etree

################################################################################
################################################################################
################################################################################

intrin_url = 'https://sx-aurora-dev.github.io/velintrin.html'

################################################################################
################################################################################
################################################################################

def list_funs(tree):
    if(tree.tag == 'td'):
        if(tree.text is not None and '_vel' in tree.text and 'approx' not in tree.text):
            print('%s;' % tree.text.replace('_vel', '__builtin_ve_vl'))

    for c in tree:
        list_funs(c)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':

    # download current intrinsic list
    req = urllib.request.urlopen(intrin_url)
    txt = req.read()
    req.close()

    # print type definitions
    # print('struct __vr;')
    # print('struct __vm;')
    # print('struct __vm256;')
    # print('struct __vm512;')

    # now parse it to get all buildin definitions
    tree = html.fromstring(txt)
    list_funs(tree)
    


