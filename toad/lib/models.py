'''
Base models. Will eventually spread these out
'''

from datetime import datetime
from typing import Any, Annotated, Union

from bson import ObjectId
from pydantic import BaseModel, Field, PlainSerializer, AfterValidator, WithJsonSchema
from pydantic import ConfigDict


def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[
    Union[str, ObjectId],
    AfterValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


class CoreModel(BaseModel):
    id: PyObjectId = Field(None, alias='_id')
    timestamp_: datetime = Field(default_factory=datetime.now)
    # creator: str TODO
    version_: str = '0.1.1-Jeeves'
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        # data['_id'] = data['hash_']
        return data

    def mongo_filter(self):
        ignore_keys = ['timestamp_', 'version_']
        hash_ = {k: v for k, v in vars(self).items() if k not in ignore_keys}
        return {k: v for k, v in hash_.items() if v is not None}


class Fasta(CoreModel):
    mongodb_collection: str = "Fastas"
    type_: str = "Fasta"
    name: str
    sequence: str
    description: str
    # symbol: Optional[str] = "default.jpg"
    # incompatibilities: list = []
