#!/usr/bin/env python 

"""
Template for a cost effectiveness value
"""

__author__ = 'Rodney L. Summerscales'


import baseoutcomevaluetemplate


class CostValue(baseoutcomevaluetemplate.BaseOutcomeValueTemplate):
    """ manage the information relevant to cost value """

    def __init__(self, token):
        """ Initialize an outcome number template given an integer token object """
        baseoutcomevaluetemplate.BaseOutcomeValueTemplate.__init__(self, token, 'cost_value')

    def valueString(self):
        """ return a string containing the value and its units
        """
        return self.token.text + ' ' + self.token.getUnits()

    def toString(self):
        """ return a string containing all relevant info for this value """
        s = self.valueString()
        if self.group != None:
            s += ', GROUP = %s, (%.2f)' % (self.group.name, self.groupProb)
        if self.outcome != None:
            s += ', OUTCOME = %s, (%.2f)' % (self.outcome.name, self.outcomeProb)
        return s

