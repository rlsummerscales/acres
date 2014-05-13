#!/usr/bin/python
# author: Rodney Summerscales


import nltk
import numpy
import xmlutil
import sys
import math

from nltk.corpus import stopwords
from basementiontemplate import BaseMentionTemplate


#############################################
# Template for a time period (duration, follow-up)
#############################################

class Time(BaseMentionTemplate):
  """ Contains information related to an time phrase that describes
      some time period from the trial (e.g. treatment duration, follow-up time). 
  """
  value = 0
  units = None
  unitSet = {'s':'seconds', 'sec':'seconds', 'second':'seconds',\
             'min':'minutes', 'minute':'minutes',\
               'hr':'hours', 'hrs':'hours', 'hour':'hours', \
               'day':'days', 'days':'days', \
               'wk':'weeks', 'wks':'weeks', 'week':'weeks', \
               'month':'months', 'months':'months', \
               'yr':'years', 'yrs':'years', 'year':'years'}
  
  def __init__(self, mention):
    """ initialize population template given a population mention """
    BaseMentionTemplate.__init__(self, mention, 'time')
    self.value = 0
    self.units = ''
    for token in mention.tokens:
      if token.isNumber():
        # assume this number is the number of days, weeks, etc
        if token.isInteger():
          self.value = int(token.text)
        else:
          self.value = float(token.text)
      if token.text in self.unitSet:
        self.units = self.unitSet[token.text]

  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this
        mention """
    pass

  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    pass
  
  def toString(self):
    return str(self.value) + ' ' + self.units
  
  