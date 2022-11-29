import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import faust
from faust.serializers import codecs
from json_utils import NumpyEncoder


class Location(faust.Record):
    host: str
    path: str


class Scan(faust.Record):
    id: int
    locations: List[Location]
    created: datetime
    scan_id: Optional[int]


class json_numpy(codecs.Codec):
    def _dumps(self, obj: Any) -> bytes:
        return json.dumps(obj, cls=NumpyEncoder).encode()

    def _loads(self, s: bytes) -> Dict:
        return json.loads(s)


codecs.register("json_numpy", json_numpy())


class ScanMetadata(faust.Record, serializer="json_numpy"):
    scan_id: int
    metadata: Dict[str, Any]
