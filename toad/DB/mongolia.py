"""
TOAD.mongolia

I am the mongodb storage interface for TOAD.
"""
import functools
import glob
import gzip
from mimetypes import guess_type
import random
import time

from pymongo import MongoClient
from Bio import SeqIO

from toad.lib import FASTx as fx


def RandomMetadata():
    labs = ['Cross', 'Enders', 'Lindemann', 'Unknown']
    source = ['Plant', 'Gut', 'Soil']
    location = ['Indiana', 'Michigan', 'Tennessee', 'Kentucky']
    return (random.choice(labs), random.choice(source), random.choice(location))


def RandomMetadata():
    labs = ['Cross', 'Enders', 'Lindemann', 'Unknown']
    source = ['Plant', 'Gut', 'Soil']
    location = ['Indiana', 'Michigan', 'Tennessee', 'Kentucky']
    return (random.choice(labs), random.choice(source), random.choice(location))


def MongoInserter(documents, db_name="DEFAULT", db_ad="localhost", port=27017, config=None):
    '''
    Eventually want to turn this into a class we can instantiate and then
    create a method for adding to the collection
    '''
    if config:
        print(f'Config is yes')
        db_name, db_ad, port = config['db'], config['db_address'], config['port']
    client = MongoClient(db_ad, port)
    db = client[db_name]
    print(f'Success with db')
    coll_name = config['collection']
    print(f'{coll_name=}')
    collection = db[coll_name]
    print(f'Success init coll')
    collection.insert_many(documents)
    print(f'Succ in mongoinserter')
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


def Reader(folder: str, files: list, config, verbose: bool = False) -> 0:
    '''
    May want to split this into 2 functions.
    '''
    start = time.time()
    print(f'Start time...')
    total_sequences = 0
    if not folder and not files:
        return 'No files were specified to read.'
    if folder:
        all_files = glob.glob(f"{folder}/*")
        all_files.extend(files)
    else:
        all_files = files
    print(all_files)
    print(config.show())
    import sys
    # for file in glob.glob(f"{folder}/*"):
    for file in all_files:
        print(f'Ingesting {file}...')
        # try to get metadata from them based on config
        _open, type_ = create_file_handle(file)
        metadata = RandomMetadata()

        documents = []
        with _open(file) as handle:
            for cnt, record in enumerate(SeqIO.parse(handle, type_)):
                total_sequences += 1
                if cnt > 0 and cnt % 5000 == 0:
                    print(f'Hopping into MongoInserter')
                    MongoInserter(documents, config=config)
                    iter_end = time.time()
                    print(
                        f'Processed {cnt} samples in {iter_end - start} seconds.')
                    documents = []
                if type_ == "fastq":
                    fastq = fx.RxFASTQ(record.description, record.seq,
                                       record.letter_annotations["phred_quality"])
                    document = fastq.to_mongo
                elif type_ == "fasta":
                    fasta = fx.RxFASTA(record.description, record.seq)
                    document = fasta.to_mongo
                document['lab'] = config['lab']

                documents.append(document)

            MongoInserter(documents, config=config)
            iter_end = time.time()
            print(
                f'\nProcessed {total_sequences} total sequences in {iter_end - start} seconds.\n\n')
    return 0


def MongoQuery(**kwargs):
    client = MongoClient("localhost", 27017)
    db = client.toad_test
    collection = db.fastq_tests
    start = time.time()

    query = []
    for key, value in kwargs.items():
        query.append({key: value})
    print(f'Query:\n{query}')
    myfilter = {"$and": query}
    print(f'My filter:\n{myfilter}')
    values = list(collection.find(myfilter))
    print(f'Found {len(values)} documents matching')
    for val in values[0:3]:
        print(val)

    # docs = list(collection.find({key: value}))
    end = time.time()
    print(end - start)
    return 0
