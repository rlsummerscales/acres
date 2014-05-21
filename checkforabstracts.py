#!/usr/bin/env python 

"""
 Check a given directory to see if it contains abstracts with ids from a given list
"""

import sys
import glob

__author__ = 'Rodney L. Summerscales'


def readListOfAbstractIds(filename):
    """
     Read a text file containing a list of abstract ids and return a set containing these ids
    """
    file = open(filename, 'r')
    idSet = set([])
    for line in file.readlines():
        line = line.strip()
        idSet.add(line)

    return idSet

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: checkforabstracts.py <INPUT_PATH> <ABSTRACT_ID_LIST> "
        print "Read MEDLINE XML abstracts in the directory specified by <INPUT_PATH>"
        print "Display those ids from the given <ABSTRACT_ID_LIST> that are not found in the directory"
        sys.exit()

    inputPath = sys.argv[1]
    abstractIdListFilename = sys.argv[2]

    idSet = readListOfAbstractIds(abstractIdListFilename)

    fileList = glob.glob(inputPath+'*.xml')
    idsInPath = set([])
    for fullPathFilename in fileList:
        filenameComponents = fullPathFilename.split('/')
        [pmid, xmlExtention] = filenameComponents[-1].split('.')
        pmid = pmid.strip()
        idsInPath.add(pmid)

    missingAbstracts = list(idSet - idsInPath)
    missingAbstracts.sort()
    if len(missingAbstracts) == 0:
        print 'All abstracts exist in', inputPath
    else:
        foundIds = list(idSet.intersection(idsInPath))
        foundIds.sort()
        print len(foundIds), 'abstracts found'
        for pmid in foundIds:
            print pmid

        print len(missingAbstracts), 'Missing abstracts:'
        for pmid in missingAbstracts:
            print pmid


