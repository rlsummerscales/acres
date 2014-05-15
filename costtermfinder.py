#!/usr/bin/env python

"""
  Rule-based finder for extracting cost-effectiveness terms
"""

__author__ = 'Rodney L. Summerscales'

from rulebasedfinder import RuleBasedFinder


class CostTermFinder(RuleBasedFinder):
    """ Find and label tokens in phrases cost effectiveness terms.
      """
    label = "cost_term"
    cueLemmaSet = {"cost", "QALY", "QALYs"}

    def __init__(self):
        """ Create a finder that identifies age phrases. All tokens in
        age phrases are labeled 'age'.
    """
        RuleBasedFinder.__init__(self, [self.label])

    def applyRules(self, token):
        """ Label the given token as a 'cost_value'
        """

        if token.hasLabel(self.label) is True:
            # token has already been labeled
            return


        if token.lemma not in self.cueLemmaSet:
            # do nothing until we find a cue term
            return

        # we have found a cue term, label maximal NP that includes this term
        phraseNode = token.parseTreeNode
        while phraseNode.parent is not None and phraseNode.parent.type == "NP":
            phraseNode = phraseNode.parent

        # label each token in maximal NP as a cost effectiveness term
        for node in phraseNode.tokenNodes():
            node.token.addLabel(self.label)
