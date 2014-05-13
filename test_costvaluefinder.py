#!/usr/bin/env python

import itertools
import costvaluefinder
import tokenlist
import sentencetoken

from sentence import Sentence


__author__ = 'Rodney L. Summerscales'

import unittest

class TokenTestCase:
    token = None
    label = None
    sentence = None

    def __init__(self, token=None, sentence=None, label=''):
        self.token = token
        self.sentence = sentence
        self.label = label


class TokenLabelCorrect(unittest.TestCase):
    valueTokens = []
    currencyTokens = []
    otherTokens = []
    finder = costvaluefinder.CostValueFinder()

    def setUp(self):
        self.valueTokens = [sentencetoken.Token("54.3"), sentencetoken.Token("0"), sentencetoken.Token("72")]
        self.currencyTokens = [sentencetoken.Token(text="pounds", lemma="pound"),
                               sentencetoken.Token(text="$", lemma="$"),
                               sentencetoken.Token(text="dollars", lemma="dollar"),
                               sentencetoken.Token(text="euros", lemma="euro")]
        self.otherTokens = [sentencetoken.Token("("), sentencetoken.Token("cost"), sentencetoken.Token("weeks")]


    def test_positive_cases(self):
        testCases = []
        for vToken, cToken, otherToken in itertools.product(self.valueTokens, self.currencyTokens, self.otherTokens):
            # other value units
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([otherToken, vToken, cToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)
            # units value other
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([cToken, vToken, otherToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)
            # units value --
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([cToken, vToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)
            # -- value units
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([vToken, cToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)

        for tc in testCases:
            tc.token.removeAllLabels()
            self.finder.applyRules(tc.token)
            self.assertEqual(tc.token.hasLabel(name=tc.label), True)

    def test_negative_cases(self):
        testCases = []
        for vToken, cToken, otherToken in itertools.product(self.valueTokens, self.currencyTokens, self.otherTokens):
            # other value other
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([otherToken, vToken, otherToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)
            # value other
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([vToken, otherToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)
            # other value --
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([otherToken, vToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)
            # value
            tList = tokenlist.TokenList()
            tList.convertListOfTokens([vToken])
            s = Sentence(tokenList=tList)
            tc = TokenTestCase(token=vToken, sentence=s, label=costvaluefinder.CostValueFinder.label)
            testCases.append(tc)

        for tc in testCases:
            tc.token.removeAllLabels()
            self.finder.applyRules(tc.token)
            self.assertEqual(tc.token.hasLabel(name=tc.label), False)


if __name__ == '__main__':
    unittest.main()
