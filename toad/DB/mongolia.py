"""
TOAD.mongolia

I am the mongodb storage interface for TOAD.
"""
import argparse
import functools
import glob
import gzip
from mimetypes import guess_type
import random
import time

from pymongo import MongoClient
from Bio import SeqIO

from toad.utils import common as cx
from toad.utils import FASTx as fx


def RandomMetadata():
    labs = ['Cross', 'Enders', 'Lindemann', 'Unknown']
    source = ['Plant', 'Gut', 'Soil']
    location = ['Indiana', 'Michigan', 'Tennessee', 'Kentucky']
    return (random.choice(labs), random.choice(source), random.choice(location))


def MongoInserter(documents):
    '''
    Eventually want to turn this into a class we can instantiate and then
    create a method for adding to the collection
    '''
    client = MongoClient("localhost", 27017)
    db = client.toad_test
    collection = db.fastq_tests
    collection.insert_many(documents)
    return 0


def create_file_handle(file):
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
    return (_open, type_)


def Reader(folder, db, verbose=False):
    '''
    May want to split this into 2 functions.
    '''
    start = time.time()
    total_sequences = 0
    for file in glob.glob(f"{folder}/*"):
        # print(f'Ingesting {file}...')
        _open, type_ = create_file_handle(file)
        # print(f'Opening file: {file} of type: {type_}')
        metadata = RandomMetadata()

        documents = []
        with _open(file) as handle:
            for cnt, record in enumerate(SeqIO.parse(handle, type_)):
                total_sequences += 1
                if cnt > 0 and cnt % 5000 == 0:
                    MongoInserter(documents)
                    iter_end = time.time()
                    print(
                        f'Processed {cnt} samples in {iter_end - start} seconds.')
                    documents = []

                fastq = fx.RxFASTQ(record.description, record.seq,
                                   record.letter_annotations["phred_quality"])
                document = fastq.to_mongo
                document['lab'] = metadata[0]
                document['source'] = metadata[1]
                document['location'] = metadata[2]

                documents.append(document)

            print(f'Inserting the remaining {len(documents)} documents.')
            MongoInserter(documents)
            iter_end = time.time()
            print(
                f'\nProcessed {total_sequences} total sequences in {iter_end - start} seconds.\n\n')
    return 0


def MongoQuery(key, value):
    client = MongoClient("localhost", 27017)
    db = client.toad_test
    collection = db.fastq_tests
    start = time.time()

    docs = list(collection.find({key: value}))
    end = time.time()
    print(end - start)
    return docs
