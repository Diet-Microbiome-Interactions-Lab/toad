'''
Base models. Will eventually spread these out
'''

from datetime import datetime
from typing import Any, Annotated, Optional, Union
import uuid

from bson import CodecOptions, ObjectId
from flask_pymongo.wrappers import Collection
from pydantic import BaseModel, Field, PlainSerializer, AfterValidator, WithJsonSchema
from pydantic import ConfigDict

from toad import mongo


def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


def string_uuid4() -> str:
    return str(uuid.uuid4())

PyObjectId = Annotated[
    Union[str, ObjectId],
    AfterValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


class CoreModel(BaseModel):
    id: PyObjectId = Field(None, alias='_id')
    dbeUUID: str = Field(default_factory=string_uuid4)
    timestamp_: datetime = Field(default_factory=datetime.now)
    # creator: str TODO
    version_: str = '0.1.1-Tadpole'
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_bson(self, exclude_fields=[]):
        data = self.model_dump(by_alias=True, exclude_none=True)
        # data['_id'] = data['hash_']
        return data

    def mongo_filter(self):
        ignore_keys = ['timestamp_', 'version_']
        hash_ = {k: v for k, v in vars(self).items() if k not in ignore_keys}
        return {k: v for k, v in hash_.items() if v is not None}
    
    @classmethod
    def get_collection_name(cls) -> str:
        return cls.model_fields['mongodb_collection'].default
    
    @classmethod
    def get_collection(cls) -> Collection:
        opts = CodecOptions(tz_aware=True)
        collection = mongo.db.get_collection(cls.get_collection_name(), codec_options=opts)
        return collection

class Fasta(CoreModel):
    mongodb_collection: str = "Fastas"
    type_: str = "Fasta"
    name: str
    # header: str
    sequence: str
    description: str
    # symbol: Optional[str] = "default.jpg"
    # incompatibilities: list = []

class UserSession(CoreModel):
    mongodb_collection: str = 'UserSession'
    type_: str = 'UserSession'
    user_dbeUUID: str


class UserPublicInfo(CoreModel):
    mongodb_collection: str = 'Users'
    type_: str = 'User'
    email: str
    handle: str
    # photo: str
    first_name: str
    last_name: str
    configuration: dict

class User(CoreModel):
    mongodb_collection: str = "Users"
    type_: str = "User"
    email: str
    handle: str
    password: str
    first_name: str
    last_name: str
    default_config: str
    profile_pic: str
    configuration: dict


class UserConfigUpdate(BaseModel):
    lab: Optional[str] = None
    source: Optional[str] = None
    project: Optional[str] = None

class Configuration(CoreModel):
    mongodb_collection: str = "Configurations"
    type_: str = "Configuration"
    # Connections
    db_address: str = "localhost"
    port: int = 27017
    db: str =  "Toad-Default"
    uri: str = "mongodb://localhost:27017"
    # More fun config stuff
    source: str = "microbiome"
    lab: str = "lindemann"
    project: "default"
    # user: str