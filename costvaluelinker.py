#!/usr/bin/env python 

"""
Use rules to associate cost values for the same cost outcome
"""

import math
import baseassociator
import outcomemeasurementtemplates

__author__ = 'Rodney L. Summerscales'


class RuleBasedCostValueLinker(baseassociator.BaseAssociator):
    """ Cost values are often reported in multiple currencies.
      This can confuse the value associator.
      Identify these cases and find the representative cost value.

      Currently, this method recognizes the following:
         COSTVALUE [units]? ( (other|COSTVALUE)+ )      => uses first COSTVALUE *outside* parenthesis
         ( (other|COSTVALUE)+ )                         => uses first COSTVALUE *inside* parenthesis
    """

    def __init__(self):
        """ create a cost value linker """
        baseassociator.BaseAssociator.__init__(self, 'cost_value', 'cost_value', useLabels=True)

    def train(self, absList, modelFilename):
        """ Rule-based approach does not need to perform training """
        pass

    def test(self, absList, modelFilename, fold=None):
        """ Apply the cost value linker to a given list of abstracts
        """
        # chose the most likely association for each value
        for abs in absList:
            for s in abs.sentences:
                self.linkTemplates(s)

    def computeTemplateFeatures(self, templates, mode=''):
        """ compute classifier features for each mention-quantity pair in
            a given sentence in an abstract. """
        pass

    def checkAssociations(self, sentence, errorOut, typeList=[]):
        """ return number of correct associations (TP, FP, FN)
            TP = number of ON,ER that are correctly associated
            FP = number of ON,ER that are associated that should *not* be
                 (includes FP numbers that are associated)
            FN = number of ON,ER that are not associated that should be
                 (does not count FN numbers that are not associated.
                 we can't associated them anyway since we could not find them)

            Note: Does nothing at the moment since there are no annotated cost values
                 """
        tp = 0
        fp = 0
        fn = 0
        falsePairs = 0

        cvList = sentence.templates.getList('cost_value')
        for cv in cvList:
            errorOut.write(cv.valueString())
            for linkedCV in cv.linkedValues:
                errorOut.write(', ' + linkedCV.valueString())
            errorOut.write('\n')

        return [tp, fp, fn, falsePairs]

    # use rule-based approach to find associations
    def linkTemplates(self, sentence):
        """ link value template to best matching mention template in the same sentence.
            It is assumed that mention clustering has not occurred yet.
            """
        templates = sentence.templates
        cvList = templates.getList('cost_value')

        if len(cvList) < 2:
            return

        if sentence.abstract.id == '16895945':
            print '16895945', cvList

        parenDepth = 0
        newCostValueList = []
        tIdx = 0
        cvIdx = 0
        linkToEndOfParens = False
        while tIdx < len(sentence):
            token = sentence[tIdx]
            if token.isLeftParenthesis():
                parenDepth += 1
            elif token.isRightParenthesis():
                parenDepth -= 1
                if parenDepth is 0:
                    linkToEndOfParens = False
            elif cvIdx < len(cvList) and token is cvList[cvIdx].token:
                # current token is a cost value
                if linkToEndOfParens is True:
                    # currently need to link to last cost value in new list
                    newCostValueList[-1].linkedValues.append(cvList[cvIdx])
                else:
                    # this value does not get linked to any previous values
                    # now check to see if it should be linked with *following* cost values
                    newCostValueList.append(cvList[cvIdx])

                    if parenDepth > 0:
                        # inside parenthesis. assume all values inside the parens should be linked
                        # however, use first (this) value in summary
                        linkToEndOfParens = True
                    else:
                        # it is outside parenthesis.
                        # check to see if it is followed by parenthesis (after possible units)
                        if tIdx + 2 < len(sentence) and \
                                (sentence[tIdx + 1].isLeftParenthesis()
                                 or (sentence[tIdx + 1].isCurrencyWord() and sentence[tIdx + 2].isLeftParenthesis())):
                            linkToEndOfParens = True
                cvIdx += 1
            tIdx += 1

        sentence.templates.setList('cost_value', newCostValueList)

