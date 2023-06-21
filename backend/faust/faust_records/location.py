import faust


class Location(faust.Record):
    host: str
    path: str
