# Natural Language Toolkit: Support for OLAC Metadata
#
# Copyright (C) 2001-2007 University of Pennsylvania
# Author: Steven Bird <sb@csse.unimelb.edu.au>
# URL: <http://nltk.sf.net>
# For license information, see LICENSE.TXT


from StringIO import StringIO

def read_olac(xml):
    """
    Read an OLAC XML record and return a list of attributes.

    @param xml: XML string for conversion    
    @type xml: C{string}
    @rtype: C{list} of C{tuple}
    """
    from lxml import etree

    root = etree.parse(StringIO(xml)).getroot()
    return [(element.tag, element.attrib, element.text) for element in root.getchildren()]

def pprint_olac(xml):
    for tag, attrib, text in read_olac(xml):
        print "%-12s" % tag + ':',
        if text:
            print text,
        if attrib:
            print "(%s=%s)" % (attrib['type'], attrib['code']),
        print

def demo():
    from lxml import etree
    from nltk.corpus import find_corpus_file
    
    file = find_corpus_file('treebank', 'olac', '.xml')
    xml = open(file).read()
    pprint_olac(xml)

if __name__ == '__main__':
    demo()

__all__ = ['read_olac', 'pprint_olac']
