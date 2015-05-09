"""
An example importer script for the Markov chain database.
Reads the Finnish bible xml into the markov_entry table:
http://homepages.inf.ed.ac.uk/s0787820/bible/download.php?url=Finnish
"""

import re
from xml.etree import ElementTree

from commands.markovcommand import MarkovEntry
from services import database


database.initialize()

s = database.Session

corpus_id = "raamattu"

tree = ElementTree.parse('../data/raamattu.xml')
root = tree.getroot()

for seg in root.iter('seg'):
    id = seg.attrib['id']
    text = re.sub('[^ \w-]', '', seg.text.lower())
    words = text.split()
    prev_2 = None
    prev_1 = words[0]
    for word in words[1:]:
        e = MarkovEntry()
        e.corpus_id = corpus_id
        e.sentence_id = id
        e.prev_2 = prev_2
        e.prev_1 = prev_1
        e.next = word
        s.add(e)
        prev_2 = prev_1
        prev_1 = word

s.commit()
