#!/usr/bin/python
# author: Rodney Summerscales

from rulebasedfinder import RuleBasedFinder

######################################################################
# Primary outcome finder
######################################################################

class PrimaryOutcomeFinder(RuleBasedFinder):
  """ Find and label tokens in phrases describing the primary outcome of a trial.
      """
  label = 'primary_outcome'
  middleWordSet = set(['composite'])
  endWordSet = set(['outcome', 'endpoint', 'endpoints', 'outcomes', 'end'])
  currentID = 0
  currentAbstract = ''
  
  def __init__(self):
    """ Create a finder that identifies age phrases. All tokens in 
        age phrases are labeled 'age'.
    """
    RuleBasedFinder.__init__(self, [self.label])
    self.currentID = 0
    self.currentAbstract = ''
              
  def applyRules(self, token):
    """ Label the given token as a 'primary_outcome'. Also label all of the neighboring 
        tokens in the same phrase.
        
        """
    if token.hasLabel(self.label) == True or token.text != 'primary':
      # token has already been labeled
      return
            
    if token.nextToken() != None \
      and (token.nextToken().text in self.endWordSet \
           or (token.nextToken().text in self.middleWordSet \
               and token.nextToken().nextToken() != None \
               and token.nextToken().nextToken() in self.endWordSet)):
      # found cue phrase (e.g. primary end point, primary outcome)
      parent = token.parseTreeNode.parent
      npNodes = parent.tokenNodes()
      # make sure that cue phrase is annotated as an outcome
      # sometime this is missed in the annotation process
#       for node in npNodes:
#         node.token.addAnnotation('outcome')
#         node.token.addLabel('outcome')
#         node.token.addLabel('referring_outcome')
# 
#       # if cue phrase is child of higher NP, add labels to all tokens in that one
#       if parent.parent != None and parent.parent.type == 'NP':
#         parent = parent.parent
#         npNodes = parent.tokenNodes()
#       # add candidate labels to each token in expanded cue phrase         
#       for node in npNodes:
#         node.token.addLabel(self.label)
# #        node.token.setLabelAttribute('outcome', 'focus', 'primary')

      # get the next token after the expanded cue phrase
      nextToken = parent.lastToken().nextToken()
      # if it is some form of TO BE label all of the tokens in the VP as candidate outcomes
      if nextToken != None:
        if nextToken.lemma == 'be':
          # assign unique id for both phrases so they can be linked together later
          idString = str(self.currentID)
          # reset outcome pair counter for each abstract
          if self.currentAbstract != token.sentence.abstract.id:
            self.currentAbstract = token.sentence.abstract.id
            self.currentID = 0
          else:
            self.currentID += 1
            
          vpNodes = nextToken.parseTreeNode.parent.tokenNodes()
          for i in range(1, len(vpNodes)):
            node = vpNodes[i]
            node.token.addLabel(self.label)
#            node.token.addLabel('outcome')
#            node.token.setLabelAttribute(self.label, 'id', idString)

#          for node in npNodes:
#            node.token.removeAnnotation('outcome')

