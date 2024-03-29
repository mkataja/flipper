"""
An example importer script for the Markov chain database.
Reads the Finnish bible xml into the markov_entry table:
http://homepages.inf.ed.ac.uk/s0787820/bible/download.php?url=Finnish
"""

from xml.etree import ElementTree

from lib import markov_helper
from models.markov_corpus import MarkovCorpus
from services import database

FILE_PATH = '../data/raamattu.xml'
CORPUS_NAME = "raamattu"

database.initialize()

with database.get_session() as session:
    corpus_id = MarkovCorpus.get_or_create(CORPUS_NAME)

tree = ElementTree.parse(FILE_PATH)
root = tree.getroot()

for seg in root.iter('seg'):
    text_identifier = seg.attrib['id']
    markov_helper.insert_text(seg.text.lower(), corpus_id, text_identifier)
