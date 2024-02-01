'''
Utilities to support the API connection
'''
import traceback
from typing import Any

from bson import ObjectId
from bson.json_util import dumps
from flask import request, Blueprint
from flask.views import MethodView
from pydantic import BaseModel, ValidationError

from toad import mongo
from toad.api.lib import dn_exceptions as dexp


def parse_qstring(args: dict, model: BaseModel):
    filter_ = {}
    for key, value in args.items():
        if key in model.model_fields.keys():
            filter_[key] = value
    return filter_


def validate_request_data(Datamodel: type[BaseModel], request_data: dict = None) -> BaseModel:
    if not request_data:
        request_data = request.get_json(force=True)
    try:
        return Datamodel(**request_data)
    except ValidationError as e:
        raise dexp.RequestValidationException(f'{Datamodel}: {e}')


def generate_filters(entry: BaseModel, filters: list[str] | None = None) -> list[dict[str, Any]]:
    """Creates a list of filters, based on the entry's fields
    that is compatible with mongo.db.collection's find()
    """
    if not filters:
        return [{'_id': None}]

    validated_filters = []
    for attribute in filters:
        current_filter = {attribute: getattr(entry, attribute)}
        validated_filters.append(current_filter)
    return validated_filters


def get_entry(db_mongo_collection_name: str, id_: str = None, qstring_filter: dict = None):
    # Here, issue is ('str', 'Plugins')
    collection = mongo.db[db_mongo_collection_name]
    if id_ is None:
        if qstring_filter is None:
            return (dumps(list(collection.find())), 200, {'ContentType': 'application/json'})
        else:
            return (dumps(list(collection.find(qstring_filter))), 200, {'ContentType': 'application/json'})

    if not ObjectId.is_valid(id_):
        return ({'success': False, 'reason': 'Invalid ObjectId to search'}, 400, {'ContentType': 'application/json'})
    mongo_entry = ObjectId(id_)
    return (dumps(collection.find_one({'_id': mongo_entry})), 200, {'ContentType': 'application/json'})


def create_entry(entry: str, db_mongo_collection_name: str, field_filters: list[dict] = None):
    return insert_to_mongo_collection(entry, db_mongo_collection_name, field_filters)


def update_entry(entry: BaseModel, db_mongo_collection_name: str, id_: str):
    collection = mongo.db[db_mongo_collection_name]
    if not ObjectId.is_valid(id_):
        return ({'success': False, 'reason': 'Invalid ObjectId for Insertion'}, 400, {'ContentType': 'application/json'})
    mongo_entry = ObjectId(id_)

    if not collection.find_one({'_id': mongo_entry}):
        return ({'success': False, 'reason': 'No document exists with that id_'}, 400, {'ContentType': 'application/json'})

    fields_to_update = entry.model_dump(
        exclude={'id', 'timestamp_'}, exclude_unset=True)  # this might not be quite right
    result = collection.update_one({'_id': mongo_entry},  {
                                   "$set": fields_to_update})
    # the assertion below will be hit if the fields_to_update values are the same as what was previously in the document. may be useful, may not be
    # assert result.modified_count == 1, f'Expected 1 document to be updated. Instead updated {result.modified_count} document(s) for {mongo_entry=}'
    assert result.raw_result[
        'updatedExisting'], f'Update to document was not successful: {collection=} {mongo_entry=}'
    return (dumps(collection.find_one({'_id': mongo_entry})), 200, {'ContentType': 'application/json'})


def delete_entry(db_mongo_collection_name: str, id_: str, field_filters: list[dict] = None):
    collection = mongo.db[db_mongo_collection_name]

    if not ObjectId.is_valid(id_):
        return ({'success': False, 'reason': 'Invalid ObjectId for Insertion'}, 400, {'ContentType': 'application/json'})
    mongo_entry = ObjectId(id_)

    if not collection.find_one({'_id': mongo_entry}):
        return ({'success': False, 'reason': 'No document exists with that id_'}, 400, {'ContentType': 'application/json'})

    collection.delete_one({'_id': mongo_entry})
    return (dumps({"$oid": id_}), 200, {'ContentType': 'application/json'})


def insert_to_mongo_collection(entry: BaseModel, db_mongo_collection_name: str, field_filters: list[dict] = None):
    """
    Raises: AttributeError, dexp.DBInsertException
    """
    print(f'Mongo: {db_mongo_collection_name}')  # Here is a tuple.
    collection = mongo.db[db_mongo_collection_name]

    try:
        field_filters = generate_filters(entry, field_filters)
    except AttributeError as e:
        raise
        # filters aren't currently provided by the client? so this error wouldn't make sense to them
        # return ({'success': False, 'reason': f'Invalid test attribute: {e}'}, 409, {'ContentType': 'application/json'})

    found_matching_entries = len(
        list(collection.find({"$or": field_filters}))) != 0

    if not found_matching_entries:
        print(f'No duplicate entries found with: {field_filters=}')
        try:
            return (dumps(collection.insert_one(entry.to_bson()).inserted_id), 201, {'ContentType': 'application/json'})
        except Exception as e:
            traceback.print_exc()
            raise dexp.DBInsertException(
                f'Unexpected issue: {db_mongo_collection_name}: {e}')
    else:
        raise dexp.DBInsertException('Invalid Duplicate item')


def register_api(bp: Blueprint, views: MethodView, model: BaseModel, endpoint: str, url: str, pk: str = 'id'):
    view_func = views.as_view(endpoint, model)
    bp.add_url_rule(url, defaults={pk: None},
                    view_func=view_func, methods=['GET', ])
    bp.add_url_rule(url, view_func=view_func, methods=['POST', ])
    bp.add_url_rule(f'{url}<{pk}>', view_func=view_func,
                    methods=['GET', 'PUT', 'DELETE'])
