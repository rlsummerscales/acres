#!/usr/bin/python
# author: Rodney Summerscales
# add lemmas to each token

import sys
import nltk.stem.wordnet
import abstractlist


lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()

def lemmatizeToken(token):
    """
     Add lemma to given token
    """
    if len(token.pos) > 0 and token.pos[0] == 'N':
        token.lemma = lemmatizer.lemmatize(token.text, 'n')
    elif len(token.pos) > 0 and token.pos[0] == 'V':
        token.lemma = lemmatizer.lemmatize(token.text, 'v')
    else:
        token.lemma = lemmatizer.lemmatize(token.text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: lemmatizeabstracts.py <PATH>"
        print "Lookup lemmas for each token in a directory of abstracts."
        print "Modified files written to same directory"
        sys.exit()

    absPath = sys.argv[1]
    absList = abstractlist.AbstractList(absPath)

    for abs in absList:
        for sentence in abs.sentences:
            for token in sentence:
                lemmatizeToken(token)

    absList.writeXML(absPath, 'raw')