#!/usr/bin/python
# author: Rodney Summerscales
import sys

if len(sys.argv) < 2:
  print "Usage: avgcomplementarity.py <RERANK_LABEL_FILES>"
  sys.exit()

filelist = []

i = 1
totalComp = 0
while i < len(sys.argv):
  print sys.argv[i], ':', 
  lines = open(sys.argv[i], 'r').readlines()
  lastLine = lines[-1]
  [desc, compValue] = lastLine.split('=')
  compValue = float(compValue)
  print compValue
  totalComp += compValue
  i += 1
  
n = i - 1
avgComp = totalComp / n 
#print totalComp, n
print 'Average =', avgComp
