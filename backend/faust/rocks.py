import rocksdb

for path in [
    "./distiller-scan-data/v1/tables/scan_id_to_id-0.db",
    "./distiller-scan-data/v1/tables/metadata-0.db",
    "./distiller-scan-data/v1/tables/status-0.db",
    "./distiller-scan-data/v1/tables/uuid-0.db",
]:
    db = rocksdb.DB(path, rocksdb.Options(create_if_missing=False), read_only=True)
    it = db.iteritems()
    it.seek_to_first()

    for item in it:
        print(item)
