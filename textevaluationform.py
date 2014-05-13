#!/usr/bin/python
# author: Rodney Summerscales


def getIndent(indentLevel):
  return '\t'*indentLevel

def bullet(indentLevel):
  indent = '\t'+getIndent(indentLevel)
  if indentLevel==0:
    bullet = '-- '
  elif indentLevel == 1:
    bullet = '** '
  else:
    bullet = '- '
  return indent+bullet
    
def evaluationPrompt(indentLevel=0):
  indent = '\t\t\t' + getIndent(indentLevel)
  return indent+' Correct [ ] \t\t Qualitatively Correct [ ] \t\t Incorrect [ ]\n\n'

def writeEvaluationElement(value, out, indentLevel=0):
  out.write(bullet(indentLevel)+value+'\n')
  out.write(evaluationPrompt(indentLevel))

def writeElementsMissing(type, out):
  out.write('\n\tNumber of '+ type +' missing?  [   ]\n\n')     
    