import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

import faust
from faust.serializers import codecs


class Location(faust.Record):
    host: str
    path: str


class Scan(faust.Record):
    id: int
    log_files: int
    locations: List[Location]
    created: datetime
    scan_id: Optional[int]


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)


class json_numpy(codecs.Codec):
    def _dumps(self, obj: Any) -> bytes:
        return json.dumps(obj, cls=NumpyEncoder).encode()

    def _loads(self, s: bytes) -> Dict:
        return json.loads(s)


codecs.register("json_numpy", json_numpy())


class ScanMetadata(faust.Record, serializer="json_numpy"):
    scan_id: int
    metadata: Dict[str, Any]
