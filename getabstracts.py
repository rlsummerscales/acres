#!/usr/bin/python
# author: Rodney Summerscales

import urllib2
import xml.dom
import xmlutil
import checkforabstracts
import sys

eutils = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

# search for texts
# searchArgs = '&term="cardiovascular%20disease"[title]%20AND%20("humans"' \
#              +'[MeSH%20Terms]%20AND%20Randomized%20Controlled%20Trial' \
#              + '[ptyp])&cmd=DetailsSearch&retmax=500'
# searchArgs = '&term=("cardiovascular%20diseases"[MeSH%20Terms]%20OR%20' \
#              + '("cardiovascular"[All%20Fields]%20AND%20"diseases"[All%20Fields])'\
#              + '%20OR%20"cardiovascular%20diseases"[All%20Fields]' \
#              + '%20OR%20("cardiovascular"[All%20Fields]' \
#              + '%20AND%20"disease"[All%20Fields])' \
#              + '%20OR%20"cardiovascular%20disease"[All%20Fields])'\
#              + '%20AND%20("humans"[MeSH%20Terms]' \
#              + '%20AND%20Randomized%20Controlled%20Trial[ptyp]'\
#              + '%20AND%20jsubsetaim[text])' \
#              + '&cmd=DetailsSearch&retmax=500'
# #             '&term="cardiovascular%20disease AND (Humans[Mesh] AND Randomized Controlled Trial[ptyp] AND jsubsetaim[text])

# search used for ischemia corpus
# searchArgs = '&term=("myocardial%20ischemia"[MeSH%20Terms]'\
#              + '%20AND%20("humans"[MeSH%20Terms]' \
#              + '%20AND%20Randomized%20Controlled%20Trial[ptyp]'\
#              + '%20AND%20jsubsetaim[text])' \
#              + '&cmd=DetailsSearch&retmax=500'

# search used for diabetes corpus
searchArgs = '&term=(("diabetes")' \
             + '%20AND%20(cost)' \
             + '%20AND%20(english[Language])' \
             + '%20AND%20("humans"[MeSH%20Terms]' \
             + '("1991/01/01"[PDat]:"2006/12/31"[PDat])' \
             + '&cmd=DetailsSearch&retmax=5000'

# # diabetes cost education
# searchArgs = '&term=(("diabetes")' \
#              + '%20AND%20(cost)' \
#              + '%20AND%20(education)' \
#              + '%20AND%20(hasabstract[text])' \
#              + '%20AND%20(english[Language])' \
#              + '%20AND%20("humans"[MeSH%20Terms]' \
#              + '("1991/01/01"[PDat]:"2006/12/31"[PDat])' \
#              + '&cmd=DetailsSearch&retmax=5000'

# diabetes education
searchArgs = '&term=(("diabetes")' \
             + '%20AND%20(education)' \
             + '%20AND%20(hasabstract[text])' \
             + '%20AND%20(english[Language])' \
             + '%20AND%20("humans"[MeSH%20Terms]' \
             + '("1991/01/01"[PDat]:"2006/12/31"[PDat])' \
             + '&cmd=DetailsSearch&retmax=10000'

if len(sys.argv) > 1:
    targetIdSet = checkforabstracts.readListOfAbstractIds(sys.argv[1])
else:
    targetIdSet = set([])

searchCmd = eutils + 'esearch.fcgi?db=pubmed'+ searchArgs
print searchCmd
searchResults = urllib2.urlopen(searchCmd)

# parse results
xmldoc = xml.dom.minidom.parseString(searchResults.read())
idNodeList = xmldoc.getElementsByTagName('Id')
print 'Number of documents found =', len(idNodeList)

#idNodeList = open('abs.txt', 'r').readlines()
searchResultSet = set([])
for idNode in idNodeList:
    id = xmlutil.getText(idNode)
    id.strip()
    searchResultSet.add(id)

if len(targetIdSet) > 0:
    missingAbstracts = list(targetIdSet - searchResultSet)
    missingAbstracts.sort()
    foundIds = list(targetIdSet.intersection(searchResultSet))
    foundIds.sort()
    print len(foundIds), 'abstracts found'
    for pmid in foundIds:
        print pmid

    print len(missingAbstracts), 'Missing abstracts:'
    for pmid in missingAbstracts:
        print pmid

# download files
for idNode in idNodeList:
    #   id = idNode[:-1]
    #   fetchCmd = 'http://www.ncbi.nlm.nih.gov/pubmed/'+id
    #   doc = urllib2.urlopen(fetchCmd)
    #   out = open(id+'.htm', 'w')
    id = xmlutil.getText(idNode)
    print 'Fetching article with id =', id
    fetchCmd = eutils+'efetch.fcgi?db=pubmed&id='+id+'&retmode=xml&rettype=abstract'
    print fetchCmd
    doc = urllib2.urlopen(fetchCmd)
    out = open(id+'.xml', 'w')
    out.write(doc.read())
    out.close()
