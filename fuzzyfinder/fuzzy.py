import json
import os

from pymongo import MongoClient


client = MongoClient("localhost", 27017)

db = client.fuzzy
collection = db.tests


with open("fuzzyfinder/USCities.json") as handle:
    data = json.load(handle)

print(len(data))

collection.drop()
collection.insert_one(data[0])
collection.find_one()
