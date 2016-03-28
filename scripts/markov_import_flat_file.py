"""
An example importer script for reading a flat file into 
the Markov chain database. Example file parsed from:
https://fi.wikiquote.org/wiki/Suomalaisia_sananlaskuja
"""

from lib import markov_helper
from lib.markov_helper import parse_markov_sentences, insert_markov_sentences
from models.markov_corpus import MarkovCorpus
from services import database


FILE_PATH = '../data/fi_sayings.txt'
CORPUS_NAME = "sanonnat"

database.initialize()

with database.get_session() as session:
    corpus_id = MarkovCorpus.get_or_create(CORPUS_NAME)

with open(FILE_PATH) as file:
    for i, line in enumerate(file.readlines()):
        text_identifier = '{}_{}'.format(CORPUS_NAME, i)
        markov_helper.insert_text(line, corpus_id, text_identifier)
