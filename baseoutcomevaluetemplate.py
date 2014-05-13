#!/usr/bin/env python 

import sys
import math

from basequantitytemplate import BaseQuantityTemplate

__author__ = 'Rodney L. Summerscales'

class BaseOutcomeValueTemplate(BaseQuantityTemplate):
    """ manage the information relevant to an Outcome number template """
    outcomeIsBad = True   # is value number of good or bad outcomes?
    group = None      # link to group template
    groupProb = 0.0   # probability that group should be associated with this value
    outcome = None    # link to outcome template
    outcomeProb = 0.0   # probability outcome should be associated with this value
    groupSize = None  # (optional) link to group size template
    __matchFeatures = None

    def __init__(self, token, valueType):
        """ Initialize an outcome number template given an integer token object """
        BaseQuantityTemplate.__init__(self, token, valueType)
        self.outcomeIsBad = True
        self.group = None
        self.outcome = None
        self.groupSize = None
        self.groupProb = 0.0
        self.outcomeProb = 0.0
        self.__matchFeatures = {}

    def addMatchFeatures(self, featureVector):
        """ save feature vectors for associating a mention of a given type with this value """
        if featureVector == None:
            return
        mType = featureVector.mTemplate.type
        if mType not in self.__matchFeatures:
            self.__matchFeatures[mType] = {}
        rootMention = featureVector.mTemplate.rootMention()
        self.__matchFeatures[mType][rootMention] = featureVector

    def clearMatchFeatures(self, mentionType=None):
        """ erase all feature vectors for a given mention type.
            If not mention type given, erase all feature vectors """
        if mentionType == None:
            self.__matchFeatures.clear()
        elif mentionType in self.__matchFeatures:
            self.__matchFeatures[mentionType].clear()

    def getMatchFeatures(self, mTemplate):
        """ return the feature vector for associating this value with the entity for the given mention """
        rootMention = mTemplate.rootMention()
        mType = rootMention.type
        if mType not in self.__matchFeatures:
            return None
        else:
            return self.__matchFeatures[mType].get(rootMention, None)

    def getMatchFeatureList(self, type):
        """ return list of all feature vectors for associating this value with entities of given mention type """
        return self.__matchFeatures[type].values()


    def correctAssociation(self, mType):
        """ return True if quantity is correctly associated
          with mention of given type. """
        if mType == 'group':
            # check group association
            if self.group == None:
                return -1     # no association can be made
            if self.shouldBeAssociated(self.group):
                return 1
            else:
                return 0
        elif mType == 'outcome':
            # check outcome association
            if self.outcome == None:
                return -1     # no association can be made
            if self.shouldBeAssociated(self.outcome):
                return 1
            else:
                return 0
        else:
            print 'Error: invalid mention type in BaseOutcomeValue.correctAssociation'
            print 'mType:', mType
            sys.exit(1)


    def shouldBelongToSameOutcomeMeasurement(self, template):
        """ return True if the given template belongs to the same outcome measurement as this one.
            Annotated information is used.
            Must have matching Group, Outcome, Time, compare set IDs. """
        gid = self.token.getAnnotationAttribute(self.type, 'group')
        oid = self.token.getAnnotationAttribute(self.type, 'outcome')
        tid = self.token.getAnnotationAttribute(self.type, 'time')
        csID = self.token.getAnnotationAttribute(self.type, 'compareSet')

        gid2 = template.token.getAnnotationAttribute(template.type, 'group')
        oid2 = template.token.getAnnotationAttribute(template.type, 'outcome')
        tid2 = template.token.getAnnotationAttribute(template.type, 'time')
        csID2 = template.token.getAnnotationAttribute(template.type, 'compareSet')

        return len(gid) > 0 and len(oid) > 0 and gid == gid2 and oid == oid2 and tid == tid2 and csID == csID2


    def confidence(self):
        """ return a confidence score between 0 and 1 that this outcome number is correct
            currently this is the product of group and outcome association probabilities.
            """
        return self.groupProb * self.outcomeProb
    #    return  self.outcomeProb



    def toString(self):
        """ return a string containing all relevant info for this value """
        s = str(self.value)
        if self.group != None:
            s += ', GROUP = '+self.group.name + ', prob = ' + str(self.groupProb)
        if self.outcome != None:
            s += ', OUTCOME = '+self.outcome.name + ', prob = ' + str(self.outcomeProb)
        return s


    def display(self):
        self.write(sys.stdout)

    def write(self, out):
        """ write template info to file """
        s = self.toString()
        out.write(s)
        out.write('\n')
