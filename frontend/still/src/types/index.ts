export type IdType = string;

export type User = {
  username: string;
}

export type Scan = {
  id: IdType;
  scan_id: IdType;
  log_files: number;
  created: string;
}
