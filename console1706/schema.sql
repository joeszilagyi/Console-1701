CREATE TABLE IF NOT EXISTS repos (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  path TEXT NOT NULL UNIQUE,
  role TEXT,
  category TEXT,
  importance TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repo_snapshots (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER NOT NULL,
  scanned_at TEXT NOT NULL,
  branch TEXT,
  commit_sha TEXT,
  commit_subject TEXT,
  commit_author TEXT,
  commit_time TEXT,
  is_dirty INTEGER,
  has_untracked INTEGER,
  ahead_count INTEGER,
  behind_count INTEGER,
  changed_files_json TEXT,
  path_clusters_json TEXT,
  recent_commits_json TEXT,
  diff_fingerprint TEXT,
  raw_git_status TEXT,
  scan_error TEXT,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS test_snapshots (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER NOT NULL,
  scanned_at TEXT NOT NULL,
  detected INTEGER NOT NULL DEFAULT 0,
  command TEXT,
  status TEXT,
  duration_seconds REAL,
  summary TEXT,
  raw_tail TEXT,
  fingerprint TEXT,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS log_events (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  source_path TEXT,
  event_time TEXT,
  observed_at TEXT NOT NULL,
  severity TEXT,
  category TEXT,
  message TEXT,
  raw_line TEXT,
  fingerprint TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS interpreted_states (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER,
  scope TEXT NOT NULL,
  state TEXT NOT NULL,
  severity TEXT NOT NULL,
  headline TEXT NOT NULL,
  meaning TEXT NOT NULL,
  why_it_matters TEXT NOT NULL,
  next_sane_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  rule_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS attention_items (
  id INTEGER PRIMARY KEY,
  fingerprint TEXT NOT NULL UNIQUE,
  repo_id INTEGER,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  why_it_matters TEXT NOT NULL,
  next_sane_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  resolved_at TEXT,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS handoff_packets (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER,
  created_at TEXT NOT NULL,
  title TEXT NOT NULL,
  path TEXT NOT NULL,
  task TEXT,
  evidence_json TEXT NOT NULL,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS scan_runs (
  id INTEGER PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  repos_seen INTEGER DEFAULT 0,
  repos_scanned INTEGER DEFAULT 0,
  errors_json TEXT
);

CREATE TABLE IF NOT EXISTS host_snapshots (
  id INTEGER PRIMARY KEY,
  scanned_at TEXT NOT NULL,
  hostname TEXT,
  os_pretty_name TEXT,
  kernel_release TEXT,
  uptime_seconds REAL,
  health_state TEXT NOT NULL,
  health_score INTEGER,
  summary_json TEXT NOT NULL,
  snapshot_json TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  errors_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_repo_snapshots_repo_time
  ON repo_snapshots(repo_id, scanned_at DESC);

CREATE INDEX IF NOT EXISTS idx_test_snapshots_repo_time
  ON test_snapshots(repo_id, scanned_at DESC);

CREATE INDEX IF NOT EXISTS idx_interpreted_states_repo_time
  ON interpreted_states(repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_attention_status
  ON attention_items(status, severity);

CREATE INDEX IF NOT EXISTS idx_host_snapshots_scanned_at
  ON host_snapshots(scanned_at DESC);
