'''
Classes for handling different API data. For now, just a DefaultAPI handler class
'''
from bson.json_util import dumps
from flask import request
from flask.views import MethodView
from pydantic import BaseModel, ValidationError


# from toad.api.lib import api_models
from toad import mongo
from toad.api.lib.dn_exceptions import RequestValidationException
from toad.api.lib.utilities import (
    get_entry,
    create_entry,
    update_entry,
    delete_entry,
    parse_qstring
)


class DefaultAPI(MethodView):
    print(f'In the default API')
    init_every_request = True

    def __init__(self, model: BaseModel, request_data: dict = None):
        self.model = model
        try:
            self.collection = model.mongodb_collection.get_default()
        except AttributeError:
            try:
                self.collection = model.mongodb_collection.get_default()
            except AttributeError:
                self.collection = model.model_fields["mongodb_collection"].get_default(
                )

        self.request_data = request_data

    def validate_request_data(self, Datamodel: type[BaseModel], request_data=None) -> BaseModel:
        if not self.request_data:
            self.request_data = request.get_json(force=True)
        try:
            return Datamodel(**self.request_data)
        except ValidationError as error:  # TODO - ValidationError
            raise RequestValidationException(f'{Datamodel}: {error}')

    def get(self, id: str):
        filter_ = parse_qstring(request.args, self.model)
        return get_entry(self.collection, id_=id, qstring_filter=filter_)

    def post(self):
        data = self.validate_request_data(
            Datamodel=self.model, request_data=self.request_data)
        return create_entry(entry=data, db_mongo_collection_name=self.collection)

    def delete(self, id: str):
        return delete_entry(db_mongo_collection_name=self.collection, id_=id)

    def put(self, id: str):
        data = self.validate_request_data(
            Datamodel=self.model, request_data=self.request_data)
        return update_entry(entry=data, db_mongo_collection_name=self.collection, id_=id)


class PluginAPI(MethodView):
    init_every_request = True

    def __init__(self, model: BaseModel, request_data: dict = None):
        self.model = model
        self.request_data = request_data
        self.collection = "plugins"

    def json_to_model(self, data: dict):
        for key, value in data.items():
            if isinstance(value, list):
                value = tuple(value)
                data[key] = value
        return data

    def validate_request_data(self, Datamodel: type[BaseModel], request_data=None) -> BaseModel:
        if not self.request_data:
            self.request_data = request.get_json(force=True)
        try:
            data = self.json_to_model(self.request_data)
            return data
            return Datamodel(**data)
        except ValidationError as error:  # TODO - ValidationError
            raise RequestValidationException(f'{Datamodel}: {error}')

    def get(self, id: str):
        filter_ = parse_qstring(request.args, self.model)
        return get_entry(self.collection, id_=id, qstring_filter=filter_)

    def post(self):
        data = self.validate_request_data(
            Datamodel=self.model, request_data=self.request_data)
        return (dumps(mongo.db.plugins.insert_one(data).inserted_id), 201, {'ContentType': 'application/json'})
        # print(f'Self.collection={self.collection}')
        # print(self.model.__fields__)
        # return create_entry(entry=data, db_mongo_collection_name=self.collection)

    def delete(self, id: str):
        return delete_entry(db_mongo_collection_name=self.collection, id_=id)

    def put(self, id: str):
        data = self.validate_request_data(
            Datamodel=self.model, request_data=self.request_data)
        return update_entry(entry=data, db_mongo_collection_name=self.collection, id_=id)
