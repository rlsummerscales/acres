#!/usr/bin/env python

"""
Rule-based methods for extracting cost values from text
"""

__author__ = "Rodney L. Summerscales"

from rulebasedfinder import RuleBasedFinder


class CostValueFinder(RuleBasedFinder):
    """ Find and label tokens in phrases cost effectiveness values.
        """
    label = 'cost_value'


    def __init__(self):
        """ Create a finder that identifies age phrases. All tokens in
            age phrases are labeled 'age'.
        """
        RuleBasedFinder.__init__(self, [self.label])

    def applyRules(self, token):
        """ Label the given token as a 'cost_value'
            """
        if token.isNumber() is False:
            return

        if self.tokenIsCostValue(token):
            token.addLabel(self.label)

    def tokenIsCostValue(self, token):
        """
         return True if a given token is a cost value
        """
        return (token.nextToken() is not None and (token.nextToken().isCurrencyWord())
                or (token.previousToken() is not None and (token.previousToken().isCurrencyWord())))