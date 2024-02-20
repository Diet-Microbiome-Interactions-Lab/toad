import glob
import json
import os

import pymongo


def hydrate_database(seed):
    print(f'Hydrating with seed={seed}/*.json')
    print(f'CWD = {os.getcwd()}')
    files = glob.glob(f'{seed}/*')

    client = pymongo.MongoClient("mongodb://localhost:27017/Toad-Default")
    db = client.get_database()

    for file in files:
        bn = os.path.basename(file)
        collection = os.path.splitext(bn)[0].title()
        db[collection].drop()  # Remove stale or out-of-date data
        with open(file) as open_file:
            data = json.load(open_file)
            db[collection].insert_many(data)
        print(f'Added data from {file} to collection {collection}')
    return 0