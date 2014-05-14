#!/usr/bin/env python

"""
 Unit tests for sentence token classes (work in progress)
"""

__author__ = 'Rodney L. Summerscales'

import unittest
import sentencetoken


class TokenTest(unittest.TestCase):
    def testCreation(self):
        t = sentencetoken.Token()
        self.assertIs(t.text, '')
        self.assertIs(t.lemma, '')
        self.assertIs(t.pos, '')

        t = sentencetoken.Token(text='hello')
        self.assertIs(t.text, 'hello')
        self.assertIs(t.lemma, 'hello')
        self.assertIs(t.pos, '')

        t = sentencetoken.Token(text='hello', lemma='world')
        self.assertIs(t.text, 'hello')
        self.assertIs(t.lemma, 'world')
        self.assertIs(t.pos, '')

        t = sentencetoken.Token(text='hello', lemma='world', pos='JJ')
        self.assertIs(t.text, 'hello')
        self.assertIs(t.lemma, 'world')
        self.assertIs(t.pos, 'JJ')


if __name__ == '__main__':
    unittest.main()
