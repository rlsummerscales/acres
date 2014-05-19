#!/usr/bin/python
# author: Rodney Summerscales
# associate event rates and outcome numbers

import math
import baseassociator
import outcomemeasurementtemplates

#######################################################################
# class definition for object that associates mentions with quantities
#######################################################################

class RuleBasedOutcomeMeasurementLinker(baseassociator.BaseAssociator):
    """ train/test system that associates event rates and outcome numbers in a sentence """

    def __init__(self):
        """ create a new mention-quantity associator given a specific mention type
            and quantity type. """
        baseassociator.BaseAssociator.__init__(self, 'eventrate', 'on', useLabels=True)

    def train(self, absList, modelFilename):
        """ Train an outcome measurement associator model given a list of abstracts """
        pass

    def test(self, absList, modelFilename, fold=None):
        """ Apply the outcome measurement associator to a given list of abstracts
            using the given model file.
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
                 """
        tp = 0
        fp = 0
        fn = 0
        falsePairs = 0
        templates = sentence.templates
        onList = templates.getList('on')
        erList = templates.getList('eventrate')

        if len(onList) > 0 and len(erList) > 0:
            errorOut.write(sentence.toString()+'\n')

        for on in onList:
            for er in erList:
                #        errorOut.write('%d (%d), %f (%d) should be associated = %s, pattern match = %s\n' \
                #                       %(on.value, on.token.index, er.value, er.token.index, on.shouldBelongToSameOutcomeMeasurement(er),\
                #                         self.patternMatch(er, on)))

                if on.shouldBelongToSameOutcomeMeasurement(er):
                    # the outcome number and event rate *should* be associated
                    if on.outcomeMeasurement != None and on.outcomeMeasurement == er.outcomeMeasurement:
                        tp += 1  # correctly associated
                        errorOut.write('+TP: %d, %f should be associated\n' %(on.value, er.value))

                    else:
                        errorOut.write('-FN: %d, %f should be associated, but were not.\n' %(on.value, er.value))
                        fn += 1  # missing association
                else:
                    # the two should *not* be associated
                    if on.outcomeMeasurement != None and on.outcomeMeasurement == er.outcomeMeasurement:
                        fp += 1  # incorrectly associated
                        errorOut.write('-FP: %d, %f should *not* be associated\n' %(on.value, er.value))
                        if on.token.hasAnnotation('on') == False and er.token.hasAnnotation('eventrate') == False:
                            errorOut.write('-FP Detection error: %d, %f are incorrectly labeled\n'%(on.value, er.value))
                            falsePairs += 1

        return [tp, fp, fn, falsePairs]

    # use rule-based approach to find associations
    def linkTemplates(self, sentence):
        """ link value template to best matching mention template in the same sentence.
            It is assumed that mention clustering has not occurred yet.
            """
        templates = sentence.templates
        onList = templates.getList('on')
        erList = templates.getList('eventrate')

        omList = []
        unmatchedER = []
        unmatchedON = []
        for er in erList:
            for on in onList:
                if on.textEventrate == None and self.patternMatch(er, on) and \
                        (on.hasAssociatedGroupSize() == False or on.equivalentEventRates(er.eventRate()) == True):
                    om = outcomemeasurementtemplates.OutcomeMeasurement(on)
                    om.addEventRate(er)
                    omList.append(om)
                    #          print 'Associating:', on.value, er.value, on.outcomeMeasurement, er.outcomeMeasurement
                    break
                elif on.textEventrate == None and self.patternMatch(er, on) and \
                        (on.hasAssociatedGroupSize() == True and on.equivalentEventRates(er.eventRate()) == False):
                    print sentence.toString()
                    print 'Event rates not equal', on.eventRate(), er.eventRate(), \
                        int(round(on.eventRate() * 100)), int(round(100*er.eventRate())), \
                        int(math.floor(on.eventRate() * 100)), int(math.floor(100*er.eventRate())), \
                        int(math.ceil(on.eventRate() * 100)), int(math.ceil(100*er.eventRate()))

            if er.outcomeNumber == None:
                unmatchedER.append(er)
            #        om = OutcomeMeasurement(er)
            #        omList.append(om)
        # create outcome measurement templates lone on templates
        for on in onList:
            if on.textEventrate == None:
                unmatchedON.append(on)
            #        om = OutcomeMeasurement(on)
            #        omList.append(om)

            #     diffs = []
            #     for er in unmatchedER:
            #       for on in unmatchedON:
            #         if on.hasAssociatedGroupSize() and on.equivalentEventRates(er.eventRate()):
            #           dist = abs(on.eventRate() - er.eventRate())
            #           if dist < 0.011:
            #             diffs.append((dist, on, er))
            #     if len(diffs) > 0:
            #       print sentence.toString()
            #       for dist, on, er in diffs:
            #         print '@@@@@@@ Linking ON-ER: dist=',dist, 'onER=', on.eventRate(), 'erER=', er.eventRate()
            #         if on.textEventrate == None and er.outcomeNumber == None:
            #           om = OutcomeMeasurement(on)
            #           om.addEventRate(er)
            #           omList.append(om)

        for er in unmatchedER:
            if er.outcomeNumber == None:
                # eventrate still not matched, create outcome measurement just for it
                om = outcomemeasurementtemplates.OutcomeMeasurement(er)
                omList.append(om)

        for on in unmatchedON:
            if on.textEventrate == None:
                # outcome number still not matched, create outcome measurement just for it
                om = outcomemeasurementtemplates.OutcomeMeasurement(on)
                omList.append(om)

        sentence.templates.addOutcomeMeasurementList(omList)

    def patternMatch(self, erTemplate, onTemplate):
        """ return True if event rate and outcome number match one of a set of textual patterns """
        sepTokens = set([',', '-LRB-', ';'])
        erToken = erTemplate.token
        onToken = onTemplate.token
        distance = erToken.index - onToken.index
        sentence = erToken.sentence

        if distance == -2:
            # match "ER ( ON"
            if sentence.tokens[erToken.index+1].text == '-LRB-':
                return True
        elif distance == 2:
            # match "ON ( ER"
            if sentence.tokens[onToken.index+1].text == '-LRB-':
                return True
        elif distance == 3:
            # match "ON POPULATION ( ER"
            if sentence.tokens[onToken.index+1].hasSemanticTag('people') \
                    and sentence.tokens[onToken.index+2].text in sepTokens:
                return True
        elif distance == 4:
            # match "ON of GS ( ER"
            if sentence.tokens[onToken.index+1].text == 'of' \
                    and sentence.tokens[onToken.index+2].hasLabel('gs') \
                    and sentence.tokens[onToken.index+3].text in sepTokens:
                return True # we have a match
        elif distance == 5:
            # match "ON of GS POPULATION ( ER"
            if sentence.tokens[onToken.index+1].text == 'of' \
                    and sentence.tokens[onToken.index+2].hasLabel('gs') \
                    and sentence.tokens[onToken.index+3].hasSemanticTag('people') \
                    and sentence.tokens[onToken.index+4].text in sepTokens:
                return True # we have a match


            #    if abs(onTemplate.token.index - erTemplate.token.index) == 2:
            #      # check pattern "ON ( ER" and "ER ( ON"
            #      middleTokenIndex = (onTemplate.token.index + erTemplate.token.index) / 2
            #      if onTemplate.token.sentence.tokens[middleTokenIndex].text == '-LRB-':
            #        return True  # we have a match
            ##    elif (erTemplate.token.index - onTemplate.token.index) == 3:
            ##      # check pattern "ON POPULATION ( ER"
            #    elif (erTemplate.token.index - onTemplate.token.index) == 4:
            #      # check pattern "ON of GS ( ER"
            #      inBetweenTokens = onTemplate.token.listOfNextTokens(3)
            #      if len(inBetweenTokens) > 0 and inBetweenTokens[0].text == 'of' \
            #        and inBetweenTokens[1].hasLabel('gs') \
            #        and inBetweenTokens[2].text in sepTokens:
            #        return True # we have a match
            ##      else:
            ##        print inBetweenTokens[0].text, inBetweenTokens[1].hasLabel('gs'), inBetweenTokens[2].text == '-LRB-'

        return False
    
