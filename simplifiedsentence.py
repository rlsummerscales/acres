#!/usr/bin/env python 

"""
 Classes for creating a simplified, chunked version of a sentence
"""

__author__ = 'Rodney L. Summerscales'


class SimpleSentenceToken:
    """ A token in the simplified sentence. Can be a mention, noun phrase, verb,
        or special token of interest. """

    tokens = []  # tokens in the phrase
    type = ''  # type of phrase

    def __init__(self, type, token=None):
        self.clear()
        if token != None:
            self.tokens.append(token)
        self.type = type


    def clear(self):
        self.tokens = []
        self.type = ''

    def addToken(self, token):
        """ add a sentence token to the list of tokens """
        self.tokens.append(token)


    def isMention(self, entityTypes):
        return self.type in entityTypes

    def toString(self):
        """ return string representing this token in the simplified sentence """
        return self.type


class SimplifiedSentence(list):
    """ create a special simplified version of a given sentence. """

    entityTypes = None
    specialTokens = {'/', 'versus', '=', ',', 'n', 'interval', 'risk', 'ratio', ';', '-LRB-', '-RRB-'}
    verbSet = {'occur', 'receive', 'assign', 'treat', 'determine', 'compare', 'assess', 'show', 'enroll'}


    def __init__(self, sentence, entityTypes, mode):
        """ create a simplified version of a given sentence.
            replace noun phrases with NP token, verb phrases with VP token,
            entity mentions with label for the entity type.
            if mode == 'train', use annotated labels. Otherwise use detected ones. """

        self.entityTypes = entityTypes
        #    self.verbSet = verbSet

        curToken = None
        simpleTree = sentence.getSimpleTree()
        for tNode in simpleTree.tokenNodes():
            if tNode.isNounPhraseNode():
                # in a base noun phrase
                npUnbroken = True
                for npToken in tNode.npTokens:
                    newToken = self.createOrAddToToken(curToken, npToken.token, mode)
                    if newToken != None:
                        curToken = newToken
                        npUnbroken = False
                if npUnbroken:
                    # NP did not contain any mentions or special tokens
                    # create a token in simplified sentence for it
                    curToken = SimpleSentenceToken('NP')
                    for npToken in tNode.npTokens:
                        curToken.addToken(npToken)
                    self.append(curToken)
            else:  # not a base noun phrase
                newToken = self.createOrAddToToken(curToken, tNode.token, mode)
                if newToken != None:
                    curToken = newToken

    def createOrAddToToken(self, simpleToken, token, mode):
        """ Either add the given sentence token to a simple sentence token
            (if appropriate) or create, return a new simple token, or ignore the token
            If a new token is created, it is added to the simplified sentence.
        """
        newToken = None

        if self.belongsWithToken(simpleToken, token, mode):
            simpleToken.addToken(token)
        elif token.isNumber():
            if token.isInteger():
                type = 'INT'
            elif token.isPercentage():
                type = 'PERCENT'
            else:
                type = 'NUM'
            newToken = SimpleSentenceToken(type, token)
            self.append(newToken)
        elif token.lemma in self.specialTokens \
                or token.pos[0:2] == 'VB':
            newToken = SimpleSentenceToken(token.lemma, token)
            self.append(newToken)
        else:
            for type in self.entityTypes:
                if token.hasLabel(type, mode):
                    newToken = SimpleSentenceToken(type, token)
                    self.append(newToken)
                    break

        return newToken


    def belongsWithToken(self, simpleToken, token, mode):
        """ return True if a given token is part of the same mention as the one
            in a given simple sentence token. """
        if simpleToken == None or simpleToken.isMention(self.entityTypes) == False:
            return False
        return token.hasLabel(simpleToken.type, mode)

    def toString(self):
        """ return a string containing all of the tokens in the simplified sentence."""
        s = []
        for sToken in self:
            s.append(sToken.type)
        return ' '.join(s)


