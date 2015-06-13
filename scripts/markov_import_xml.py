"""
An example importer script for the Markov chain database.
Reads the Finnish bible xml into the markov_entry table:
http://homepages.inf.ed.ac.uk/s0787820/bible/download.php?url=Finnish
"""

from itertools import tee, islice, chain
import re
from xml.etree import ElementTree

from commands.markovcommand import MarkovEntry
from services import database


def previous_and_next(iterable):
    prevs, items, nexts = tee(iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)

database.initialize()

session = database.Session

corpus_id = "raamattu2"

tree = ElementTree.parse('../data/raamattu.xml')
root = tree.getroot()

for seg in root.iter('seg'):
    text = re.sub('[^ .\w-]', '', seg.text.lower())
    sentences = text.split('.')
    for i, sentence in enumerate(sentences):
        id = '{}_{}'.format(seg.attrib['id'], i)
        words = sentence.split()
        for previous, current, next in previous_and_next(words):
            e = MarkovEntry()
            e.corpus_id = corpus_id
            e.sentence_id = id
            e.prev_2 = previous
            e.prev_1 = current
            e.next = next
            session.add(e)
    session.commit()
