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

CREATE TABLE IF NOT EXISTS news_sources (
  id INTEGER PRIMARY KEY,
  source_key TEXT NOT NULL UNIQUE,
  scope TEXT NOT NULL,
  name TEXT NOT NULL,
  kind TEXT NOT NULL,
  url TEXT,
  homepage_url TEXT,
  enabled INTEGER NOT NULL DEFAULT 0,
  config_hash TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 50,
  tags_json TEXT NOT NULL DEFAULT '[]',
  policy_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news_fetch_runs (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  http_status INTEGER,
  item_count INTEGER NOT NULL DEFAULT 0,
  error_class TEXT,
  error_message TEXT,
  robots_allowed INTEGER,
  etag_sent TEXT,
  etag_received TEXT,
  last_modified_sent TEXT,
  last_modified_received TEXT,
  duration_ms INTEGER,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(source_id) REFERENCES news_sources(id)
);

CREATE TABLE IF NOT EXISTS news_source_registry (
  id INTEGER PRIMARY KEY,
  source_key TEXT NOT NULL UNIQUE,
  scope TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_family TEXT NOT NULL,
  source_class TEXT NOT NULL,
  adapter TEXT NOT NULL,
  kind TEXT NOT NULL,
  raw_url TEXT NOT NULL,
  priority INTEGER NOT NULL,
  interval_minutes INTEGER NOT NULL,
  official_status TEXT NOT NULL,
  privacy_risk TEXT NOT NULL,
  policy_risk TEXT NOT NULL,
  parser_risk TEXT NOT NULL,
  retention_sensitivity TEXT NOT NULL,
  verification_status TEXT NOT NULL,
  future_phase TEXT NOT NULL,
  expected_access_kind TEXT NOT NULL,
  homepage_url TEXT,
  parser TEXT,
  enabled_by_default INTEGER NOT NULL DEFAULT 0,
  why_it_matters TEXT,
  evidence_notes_json TEXT NOT NULL DEFAULT '[]',
  seen_at TEXT,
  last_synced_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news_items (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL,
  scope TEXT NOT NULL,
  local_event_id INTEGER,
  canonical_url TEXT,
  url TEXT NOT NULL,
  url_hash TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  source_published_at TEXT,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  tags_json TEXT NOT NULL DEFAULT '[]',
  rank_score INTEGER NOT NULL DEFAULT 0,
  trend_score INTEGER NOT NULL DEFAULT 0,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  content_hash TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  FOREIGN KEY(source_id) REFERENCES news_sources(id)
);

CREATE TABLE IF NOT EXISTS local_events (
  id INTEGER PRIMARY KEY,
  scope TEXT NOT NULL,
  event_key TEXT NOT NULL,
  event_type TEXT NOT NULL,
  title TEXT NOT NULL,
  representative_item_id INTEGER,
  severity TEXT NOT NULL DEFAULT 'notice',
  public_impact_score INTEGER NOT NULL DEFAULT 0,
  source_diversity_score INTEGER NOT NULL DEFAULT 0,
  official_confirmation_score INTEGER NOT NULL DEFAULT 0,
  social_echo_score INTEGER NOT NULL DEFAULT 0,
  news_echo_score INTEGER NOT NULL DEFAULT 0,
  transport_impact_score INTEGER NOT NULL DEFAULT 0,
  utility_impact_score INTEGER NOT NULL DEFAULT 0,
  hazard_score INTEGER NOT NULL DEFAULT 0,
  airport_port_score INTEGER NOT NULL DEFAULT 0,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  last_elevated_at TEXT,
  expires_at TEXT NOT NULL,
  geography_json TEXT NOT NULL DEFAULT '[]',
  neighborhoods_json TEXT NOT NULL DEFAULT '[]',
  title_tokens_json TEXT NOT NULL DEFAULT '[]',
  source_ids_json TEXT NOT NULL DEFAULT '[]',
  families_json TEXT NOT NULL DEFAULT '[]',
  item_ids_json TEXT NOT NULL DEFAULT '[]',
  evidence_json TEXT NOT NULL DEFAULT '{}',
  ranking_explanation_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS news_clusters (
  id INTEGER PRIMARY KEY,
  scope TEXT NOT NULL,
  cluster_key TEXT NOT NULL,
  title TEXT NOT NULL,
  representative_item_id INTEGER,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  item_count INTEGER NOT NULL DEFAULT 0,
  score INTEGER NOT NULL DEFAULT 0,
  tags_json TEXT NOT NULL DEFAULT '[]',
  evidence_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(representative_item_id) REFERENCES news_items(id)
);

CREATE TABLE IF NOT EXISTS news_source_health (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL,
  observed_at TEXT NOT NULL,
  state TEXT NOT NULL,
  last_success_at TEXT,
  last_failure_at TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  stale_after TEXT,
  message TEXT,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(source_id) REFERENCES news_sources(id)
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

CREATE INDEX IF NOT EXISTS idx_news_sources_scope_enabled
  ON news_sources(scope, enabled);

CREATE INDEX IF NOT EXISTS idx_news_sources_source_key
  ON news_sources(source_key);

CREATE INDEX IF NOT EXISTS idx_news_fetch_runs_source_started
  ON news_fetch_runs(source_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_fetch_runs_status_started
  ON news_fetch_runs(status, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_items_scope_seen
  ON news_items(scope, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_items_source_seen
  ON news_items(source_id, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_items_expires_at
  ON news_items(expires_at);

CREATE INDEX IF NOT EXISTS idx_news_items_url_hash
  ON news_items(url_hash);

CREATE INDEX IF NOT EXISTS idx_news_items_local_event
  ON news_items(local_event_id);

CREATE INDEX IF NOT EXISTS idx_news_source_registry_scope
  ON news_source_registry(scope, source_key);

CREATE INDEX IF NOT EXISTS idx_news_source_registry_family
  ON news_source_registry(source_family);

CREATE INDEX IF NOT EXISTS idx_news_source_registry_class
  ON news_source_registry(source_class);

CREATE INDEX IF NOT EXISTS idx_news_source_registry_verification_status
  ON news_source_registry(verification_status);

CREATE INDEX IF NOT EXISTS idx_news_items_rank_scope
  ON news_items(scope, rank_score DESC, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_clusters_scope_score
  ON news_clusters(scope, score DESC, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_clusters_key
  ON news_clusters(cluster_key);

CREATE INDEX IF NOT EXISTS idx_local_events_scope_time
  ON local_events(scope, status, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_local_events_key
  ON local_events(event_key);

CREATE INDEX IF NOT EXISTS idx_local_events_expires_at
  ON local_events(expires_at);

CREATE INDEX IF NOT EXISTS idx_news_source_health_source_observed
  ON news_source_health(source_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_source_health_state
  ON news_source_health(state, observed_at DESC);
