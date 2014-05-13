#!/usr/bin/env python

"""
 Maintain a list of Mesh terms for a document
"""

import xmlutil

__author__ = 'Rodney L. Summerscales'

class MeshTopic:
  """ a descriptor or qualifier mesh topic term """
  name = None
  majorTopic = False

  def __init__(self, node):
    self.name = xmlutil.getText(node)
    self.majorTopic = node.getAttribute('MajorTopicYN') == 'Y'

  def getXML(self, doc, tagName):
    """ return an xml element containing descriptor/qualifier information
        tagName = DescriptorName or QualifierName """
    node = xmlutil.createNodeWithTextChild(doc, tagName, self.name)
    if self.majorTopic:
      topicValue = 'Y'
    else:
      topicValue = 'N'
    node.setAttribute('MajorTopicYN', topicValue)
    return node

class MeshHeading:
  """ A topic and optional list of qualifier topics """
  descriptorName = None
  qualifierList = None

  def __init__(self, node):
    """ create a new mesh topic given a MeshHeading element """
    dNodeList = node.getElementsByTagName('DescriptorName')
    self.descriptorName = MeshTopic(dNodeList[0])

    qNodeList = node.getElementsByTagName('QualifierName')
    self.qualifierList = []
    for qNode in qNodeList:
      self.qualifierList.append(MeshTopic(qNode))

  def getXML(self, doc):
    """ return an xml element containing information for a MeshHeading element"""
    node = doc.createElement('MeshHeading')
    node.appendChild(self.descriptorName.getXML(doc, 'DescriptorName'))
    for qualifierName in self.qualifierList:
      node.appendChild(qualifierName.getXML(doc, 'QualifierName'))
    return node


class MeshHeadingList(list):
  """ Manage a list of mesh terms for an abstract """

  def __init__(self, node):
    """ create a new list of mesh terms given an xml node for a MeshHeadingList """
    nodeList = node.getElementsByTagName('MeshHeading')
    for node in nodeList:
      self.append(MeshHeading(node))

  def getXML(self, doc):
    """ create an xml element containing the entire list of mesh headings """
    node = doc.createElement('MeshHeadingList')
    for meshHeading in self:
      node.appendChild(meshHeading.getXML(doc))
    return node
