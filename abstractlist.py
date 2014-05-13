#!/usr/bin/env python 


"""
maintain lists of abstracts
"""

import glob
import gc

import abstract
from operator import attrgetter
from crossvalidate import CrossValidationSets
from templates import Templates


__author__ = 'Rodney L. Summerscales'


class AbstractList:
    """ maintain a list of Abstract objects """
    __list = []       # list of abstracts
    __index = 0       # current index into list of abstracts (used by iterator)
    cvSets = []       # list of testing/training sets for k-fold crossvalidation
    nFolds = 0      # number of folds used for crossvalidation
    sentenceFilter = None

    def __init__(self, path=None, nFolds=0, sentenceFilter=None, label='', \
                 loadRegistries=True):
        """ create new list of abstracts
            allow list to be populated from an xml file

            path = directory containing xml files
            nFolds = number of folds used for cross-validation
            sentenceFilter = function that takes a Sentence object as a parameter
                     and returns True if the sentence should be included
                     and False if it should be ignored.
                     (optional. default is to include every sentence.)
                             """
        self.__list = []
        self.__index = 0
        self.cvSets = []
        self.nFolds = nFolds
        if sentenceFilter == None:
            self.sentenceFilter = lambda sentence: True
        else:
            self.sentenceFilter = sentenceFilter

        # read list of abstracts from file (if given)
        if path != None:
            self.readXML(path, label, loadRegistries)

        # create testing/training sets
        self.createCrossValidationSets(nFolds)

    def copyList(self, absList):
        """ copy list of abstracts from given abstract list """
        self.__list = []
        for abstract in absList:
            self.__list.append(abstract)

    def createCrossValidationSets(self, nFolds, randomSeed=42):
        """ create new crossvalidation sets """
        if nFolds > 1:
            self.nFolds = nFolds
            self.cvSets = CrossValidationSets(self.__list, self.nFolds, randomSeed)
            print 'Abstract list built'
            print len(self.__list), 'abstracts'
            print 'Crossvalidation sets'
            for dataSet in self.cvSets:
                print 'Training:', len(dataSet.train), '\tTesting:', len(dataSet.test)
            self.sort()

    def sort(self):
        """ sort the list of abstracts by pubmed id """
        self.__list = sorted(self.__list, key=attrgetter('id'))

    def remove(self, abstract):
        """ remove a given abstract from list of abstracts """
        if abstract in self.__list:
            self.__list.remove(abstract)

    def applySentenceFilter(self, sentenceFilter):
        """ apply a given filter to determine which sentences are included in the
            main sentence list (Abstract.sentence) for each abstract.

            Filter is applied to entire collection of sentences, not the results
            from a previous filter operation."""
        for abs in self.__list:
            abs.filterSentences(sentenceFilter)

    def labelsToAnnotations(self, labelList):
        """ For each token in the list of abstracts, if it has been assigned a label in
            a given list of labels, change the label into an annotation for the token"""
        for abs in self.__list:
            for sentence in abs.allSentences():
                for token in sentence:
                    for label in labelList:
                        if token.hasAnnotation(label):
                            token.removeAnnotation(label)
                        if token.hasLabel(label):
                            token.convertLabelToAnnotation(label)
                        #              token.setAnnotationAttribute(label, 'new', 'true')

    def labelsToSemanticTag(self, labelList):
        """ For each token in the list of abstracts, if it has been assigned a label in
            a given list of labels, change the label into a semantic tag for the token"""
        for abs in self.__list:
            for sentence in abs.sentences:
                for token in sentence:
                    for label in labelList:
                        if token.hasLabel(label):
                            token.removeLabel(label)
                            token.addSemanticTag(label)

    def cleanupAnnotations(self):
        """ Cleanup minor annotation inconsistencies in the current list of abstracts. """
        determinerSet = set(['a', 'the', 'an'])
        for abstract in self.__list:
            for sentence in abstract.allSentences():
                for token in sentence:
                    nextToken = token.nextToken()
                    if nextToken != None:
                        # add determiner at beginning of mention if not already there
                        if token.text in determinerSet:
                            typeList = ['group', 'outcome']
                            for type in typeList:
                                token.copyAnnotation(nextToken, type)

                        if token.text == 'with':
                            token.copyAnnotation(nextToken, 'condition')

    def removeLabels(self, labelList=[]):
        """ For each token in the list of abstracts, if it has been assigned a label in
            a given list of labels, remove it.
            if no list of labels is given, remove all labels. """
        for abstract in self.__list:
            for sentence in abstract.allSentences():
                sentence.templates = None
                sentence.annotatedTemplates = None
                for token in sentence:
                    token.removeAllLabels(labelList)

    def createTemplates(self, useLabels=True):
        """ create mention and number templates for entity in each sentence in the list of abstracts
            if useLabels is True, then detected mentions and numbers are used for templates
            otherwise use annotated information.

            this also creates annotated templates regardless. """
        for abstract in self.__list:
            for sentence in abstract.sentences:
                sentence.templates = Templates(sentence, useLabels=useLabels)
                sentence.annotatedTemplates = Templates(sentence, useLabels=False)

    def readXML(self, path='', label='', loadRegistries=True):
        """ read all xml files in a given directory """
        if len(path) > 0 and path[-1] != '/':
            path = path + '/'

        self.__list = []

        # get list of xml files in given directory
        if len(label) > 0:
            fileList = glob.glob(path+'*.'+label+'.xml')
        else:
            fileList = glob.glob(path+'*.xml')

        print 'Reading files from', path
        for file in fileList:
            print 'Reading:',file
            self.__list.append(abstract.Abstract(file, self.sentenceFilter, loadRegistries))
        print 'Done!'
        gc.collect()
        self.cleanupAnnotations()


    def writeHTML(self, filename, labelList=[]):
        """ write sentences to html file. highlight correct and incorrect tokens
            of a given label type (e.g. group, outcome number).
            supports up to 7 label types. colors for label types are (in order):

            blue, green, purple, darkorange, darkcyan, maroon, brown

            if more than 7 types are specified, all types are just blue.
            tokens with incorrect labels are colored red.

            If no labels are specified, all text is black.
            """

        out = open(filename, mode='w')
        out.write("<html><head><title>" + filename + "</title><body>\n<p>")
        for abs in self.__list:
            out.write('<p><b><u>' + abs.id + ':</u></b></p>\n')
            abs.writeHTML(out, labelList)

        out.write('</body></html>\n')
        out.close()

    def writeXML(self, path='', label=''):
        """ write all abstracts to xml files in the given path
            abstract names are "<ABS_ID>.<LABEL>.xml" """
        if len(path) > 0 and path[-1] != '/':
            path = path + '/'
        for abs in self.__list:
            filename = path+abs.id
            if len(label) > 0:
                filename = filename+'.'+label
            filename = filename+'.xml'
            abs.writeXML(filename)
        gc.collect()

    def __len__(self):
        """ implement len() method """
        return len(self.__list)

    def __getitem__(self, index):
        return self.__list[index]

    def __setitem__(self, index, value):
        self.__list[index] = value

    # routines needed for implementing the iterator
    def __iter__(self):
        self.__index = 0
        return self

    def next(self):
        if self.__index == len(self.__list):
            raise StopIteration
        self.__index = self.__index + 1
        return self.__list[self.__index-1]

