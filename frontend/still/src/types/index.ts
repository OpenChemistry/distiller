export type IdType = string;

export type User = {
  username: string;
}

export type ScanLocation = {
  id: IdType;
  host: string;
  path: string;
}

export type Scan = {
  id: IdType;
  scan_id: IdType;
  log_files: number;
  created: string;
  locations: ScanLocation[];
  notes?: string;
  haadf_path?: string;
}
