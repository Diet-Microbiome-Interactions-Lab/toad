"""
TOAD.mongolia

I am the mongodb storage interface for TOAD.
"""
from pymongo import MongoClient
from Bio import SeqIO
import sys
import functools
from mimetypes import guess_type

from toad.utils import common as cx
from toad.utils import FASTx as fx


client = MongoClient("localhost", 27017)
# client = MongoClient("mongodb://localhost:27017/")
db = client.test_db
collection = db.test_collection

data = {
    "name": "Dane",
    "age": 31
}
# collection.insert_one(data)
# print(collection.find_one())


def Reader(file, db):
    '''
    May want to split this into 2 functions.
    '''
    encoding = guess_type(file)
    _open = functools.partial(
        gzip.open, mode='rt') if encoding[1] == 'gzip' else open

    if file.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
        type_ = "fastq"
    elif file.endswith((".fasta", ".fa", ".fasta.gz", ".fa.gz")):
        type_ = "fasta"
    else:
        raise ValueError(
            "Unknown type plumbed to Reader Class. Sorry, Dog (ruff ruff)")

    with _open(file) as handle:
        for cnt, record in enumerate(SeqIO.parse(handle, type_)):
            if cnt < 2:
                fastq = fx.RxFASTQ(record.description, record.seq,
                                   record.letter_annotations["phred_quality"])
                print(fastq.to_mongo())
            else:
                break
    return 0
