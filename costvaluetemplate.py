#!/usr/bin/env python 

"""
Template for a cost effectiveness value
"""

__author__ = 'Rodney L. Summerscales'

import sys
import math
import baseoutcomevaluetemplate


class CostValue(baseoutcomevaluetemplate.BaseOutcomeValueTemplate):
  """ manage the information relevant to cost value """


  def __init__(self, token):
    """ Initialize an outcome number template given an integer token object """
    baseoutcomevaluetemplate.BaseOutcomeValueTemplate.__init__(self, token, 'cost_value')