#!/usr/bin/python
# Find entities in a collection of texts
# author: Rodney Summerscales

import sys
import os.path

from abstractlist import AbstractList
from finder import Finder

class DefaultFinder(Finder):
    """ The finder for a finder task if none is specified.
        It does nothing.
        """
    def __init__(self, entityTypes=[]):
        """ Does nothing """
        Finder.__init__(self, entityTypes)


    def computeFeatures(self, absList, mode=''):
        """ Does nothing """
        pass

    def train(self, absList, modelfilename):
        """ Does nothing """
        pass

    def test(self, absList, modelfilename, fold=None):
        """ Does nothing """
        pass

    def computeStats(self, absList, statOut=None, errorOut=None):
        """ Does nothing """
        pass



##############################################################
# Main class to find mentions or quantities
##############################################################
class FinderTask:
    """ Find mentions or quantities in a given set of XML files. """
    modelFilename = ''
    modelPath=None
    finder=None
    discardLabels=False
    finderFilters=[]

    def __init__(self, finder=None, modelFilename=None, modelPath=None, \
                 discardLabels=False, finderFilters=[]):
        """ Initialize new finder task given a Finder object and
            a destination path for writing the resulting abstract XML files.

            if discardLabels == True, clear the labels for each token that match
              the set of labels specified in the Finder. This is done after features
              are computed.
        """
        self.discardLabels = discardLabels
        if modelPath == None:
            self.modelPath = '.'
        else:
            if modelPath[-1] != '/':
                self.modelPath = modelPath + '/'
            else:
                self.modelPath = modelPath

        if finderFilters != None:
            self.finderFilters = finderFilters

        if finder == None:
            self.finder = DefaultFinder()
            self.modeFilename = ''
        else:
            self.finder = finder
            if modelFilename != None:
                self.modelFilename = self.modelPath+modelFilename
            else:
               # self.modelFilename = self.modelPath+self.finder.entityTypesString + '.model'
                self.modelFilename = self.modelPath+self.finder.getDefaultModelFilename() + '.model'

    def train(self, absList):
        """  train mention finding model """
        print 'Training model to recognize:', self.finder.entityTypes, self.modelFilename
        self.finder.computeFeatures(absList, mode='train')
        if self.discardLabels:
            self.removeLabels(absList, self.finder.entityTypes)
        self.finder.train(absList, self.modelFilename)

    def test(self, absList, statOut, postProcess=False, fold=None):
        """ apply mention finding model """
        print 'Finding:', self.finder.entityTypes
        self.finder.computeFeatures(absList, mode='test')
        if self.discardLabels:
            self.removeLabels(absList, self.finder.entityTypes)
        self.finder.test(absList, self.modelFilename, fold=fold)
        if postProcess:
            self.filterResults(absList)
        self.computeStats(absList, statOut, fold)

    def computeStats(self, absList, statOut, fold=None):
        """ compute finder performance stats for a given list of abstracts. write result to file """
        if fold != None:
            foldString = '.%d' % fold
        else:
            foldString = ''

        errorFilename = '%s.%s%s.errors.txt'%(self.finder.entityTypesString,self.finder.finderType, foldString)
        print '~~~~~~~~~~~~~~~~~ Writing:', errorFilename
        print 'fold=',fold

        errorOut = open(errorFilename, 'w')
        self.finder.computeStats(absList, statOut, errorOut)
        errorOut.close()


    def filterResults(self, absList):
        """ apply a collection of post-processing filters to list of abstracts """
        for abstract in absList:
            for filter in self.finderFilters:
                filter(abstract)

    def crossval(self, absList, statOut, postProcess=False):
        """ Perform crossvalidation on given list of abstracts.
            Assumes that the number of folds was specified when the abstracts
            were loaded.
        """
        print 'Training/testing models to recognize:', self.finder.entityTypes
        self.finder.computeFeatures(absList, mode='crossval')
        if self.discardLabels:
            self.removeLabels(absList, self.finder.entityTypes)
        self.finder.crossvalidate(absList, self.modelPath)
        if postProcess:
            self.filterResults(absList)
        errorFilename = self.finder.entityTypesString+'.'+self.finder.finderType + '.errors.txt'
        errorOut = open(errorFilename, 'w')
        self.finder.computeStats(absList, statOut, errorOut)
        errorOut.close()

    def removeLabels(self, absList, labels=[]):
        """ remove all labels (specified in given list of labels) from each token in each
            each abstract. If list of labels not given, remove all labels """
        for abs in absList:
            for sentence in abs.sentences:
                for token in sentence:
                    if len(labels) == 0:
                        # remove all labels from token
                        token.removeAllLabels()
                    else:
                        # only remove those labels in given list of labels.
                        for label in labels:
                            token.removeLabel(label)

