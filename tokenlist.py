#!/usr/bin/python
# author: Rodney Summerscales
# define classes for a token in a sentence


import re

from sentencetoken import Token


##############################################################
# stores a list of tokens
##############################################################

class TokenList(list):
    """ class for managing a list of Token objects """

    def convertString(self, text, separator='\W+'):
        tokenTextList = re.split(separator, text)
        #    print 'Parsed string: ', tokenTextList
        self.convertStringList(tokenTextList)

    def convertStringList(self, stringList):
        """ convert list of strings into list of Token elements """
        del self[:]
        for text in stringList:
            token = Token(text)
            #      print 'adding: ', token.text
            self.append(token)

    def convertListOfTokens(self, listOfTokens):
        """ Create a new token list from a regular python list of Token elements
        """
        del self[:]
        for token in listOfTokens:
            self.append(token)

    def toStringList(self):
        """ convert list of token objects to a list of string objects """
        list = []
        for token in self:
            list.append(token.text)
        return list

    def toLemmaList(self):
        """ convert list of token objects to a list of lemmas. """
        list = []
        for token in self:
            list.append(token.lemma)
        return list

    def toString(self):
        """ convert list of token objects to a string """
        #    return ' '.join(self.toStringList())
        s = ''
        i = 0
        s = []
        while i < len(self):
            token = self[i]
            if i+1 < len(self) and token.text == 'greater' and self[i+1].text == 'than':
                if token.hasAnnotation('greater_than_equal_to'):
                    s.append('>=')
                else:
                    s.append('>')
                i += 1
            elif i+1 < len(self) and token.text == 'less' and self[i+1].text == 'than':
                if token.hasAnnotation('less_than_equal_to'):
                    s.append('<=')
                else:
                    s.append('<')
                i += 1
            else:
                s.append(token.getDisplayText())
                # separate tokens with a space
            #       if i < len(self):
            #         s += ' '
            # move to next token in sentence
            i += 1
        return ' '.join(s)

    def toStringSet(self):
        """ return set of token text strings """
        return set(self.toStringList())

    def toLemmaSet(self):
        """ return set of token lemmas """
        return set(self.toLemmaList())

    def removeLabel(self, label):
        """ remove the mention label from each token in the mention """
        for token in self:
            token.removeLabel(label)

