from typing import List, Optional
from datetime import datetime
import faust

class Location(faust.Record):
    host: str
    path: str


class Scan(faust.Record):
    id: int
    log_files: int
    locations: List[Location]
    created: datetime
    scan_id: Optional[int]
