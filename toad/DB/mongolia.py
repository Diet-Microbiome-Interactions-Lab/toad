"""
TOAD.mongolia

I am the mongodb storage interface for TOAD.
"""
import functools
import glob
import gzip
from mimetypes import guess_type
import os
import random
import requests
import ssl
import sys
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


# def MongoInserter(documents, db_name="DEFAULT", db_ad="localhost", port=27017, config=None):
def FastaInserter(documents, api_prefix="http//127.0.0.1:5000/api/v1", config=None):
    '''
    Eventually want to turn this into a class we can instantiate and then
    create a method for adding to the collection
    '''
    if config:
        api_prefix = config['api_prefix']
    print(f'Documents: {documents=}')
    api_suffix = "amplicon/fastas"
    api_uri = os.path.join(api_prefix, api_suffix)
    print(f'Post request with {api_uri=}')
    response = requests.post(api_uri, verify=False)
    print(f'Response:\n{response=}')
    print(response.json())
    return 0
    # return response.json()
    # if config:
    # print(f'Config is yes')
    # db_name, db_ad, port = config['db'], config['db_address'], config['port']
    # db_name, db_uri = config['db'], config['uri']
    # client = MongoClient(db_uri)
    # db = client[db_name]
    # print(f'Success with db')
    # coll_name = config['collection']
    # print(f'{coll_name=}')
    # collection = db[coll_name]
    # print(f'Success init coll')
    # collection.insert_many(documents)

    # print(f'Success in mongoinserter')
    # return 0


def query_fasta(api_prefix="http://127.0.0.1:5000/api/v1", **kwargs):
    '''
    General query call to grab fasta files
    '''
    api_suffix = "amplicon/fastas"
    api_uri = os.path.join(api_prefix, api_suffix)
    response = requests.get(api_uri, verify=False)
    return response.json()


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
    for file in all_files:
        print(f'Ingesting {file}...')
        # try to get metadata from them based on config
        _open, type_ = create_file_handle(file)
        metadata = RandomMetadata()  #TODO: REPLACE THIS

        documents = []
        with _open(file) as handle:
            for cnt, record in enumerate(SeqIO.parse(handle, type_)):
                total_sequences += 1
                if cnt > 0 and cnt % 5000 == 0:
                    print(f'Hopping into FastaInserter')
                    FastaInserter(documents, config=config)
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

            print('Hopping into FastaInserter')
            FastaInserter(documents, config=config)
            print(f'Completed FastaInserter...')
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


def query_fasta(api_prefix="http://127.0.0.1:5000/api/v1", qparams=None, **kwargs):
    '''
    General query call to grab fasta files
    '''
    api_suffix = "amplicon/fastas"
    api_uri = os.path.join(api_prefix, api_suffix)
    print(f'API query = {api_uri}')
    print(f'[mx.query_fasta]: {qparams=}')
    response = requests.get(api_uri, params=qparams,
                            verify=False, timeout=1.5)
    return response.json()


def post_fasta(api_prefix="http://127.0.0.1:5000/api/v1", **kwargs):
    '''
    General post call
    '''
    api_suffix = "amplicon/fastas"
    api_uri = os.path.join(api_prefix, api_suffix)
    data = {'name': 'Toad Sequence', 'sequence': 'ATGC',
            'description': 'Test toad sequence'}

    response = requests.post(api_uri, json=data, verify=False, timeout=1.5)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {"Response": e, "Description": "Bad request"}

    return response.json()
