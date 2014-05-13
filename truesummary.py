#!/usr/bin/python
# author: Rodney Summerscales
# create an EBM summary for a given abstract from annotated data

import sys

from summary import SummaryList
from abstractlist import AbstractList
from statlist import StatList
from systemconfig import RunConfiguration

if len(sys.argv) < 3:
  print "Usage: truesummary.py <INPUT_PATH> <OUTPUT_PATH>"
  print "Generate summaries of all files in the directory specified by <INPUT_PATH>"
  print "using their annotated information."
  print "The resulting summaries are written to <OUTPUT_PATH>" 
  sys.exit()
    
inputPath = sys.argv[1]
outputPath = sys.argv[2]
absList = AbstractList(inputPath)

# Compute summary statistics
# file containing statistics for all components
statList = StatList()
summaryList = SummaryList(absList, statList, useAnnotated=True)
statList.write('truestats.txt')

# write summaries
summaryList.writeXML(outputPath, RunConfiguration.version)  
summaryList.writeHTML('summaries.true.html')

    