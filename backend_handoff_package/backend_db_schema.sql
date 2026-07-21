-- Payment-time card recommendation app schema draft
-- This is a backend handoff draft. Adjust data types/indexes for the actual DB engine.

CREATE TABLE cards (
  card_id INTEGER PRIMARY KEY,
  issuer VARCHAR(80) NOT NULL,
  card_name VARCHAR(255) NOT NULL,
  card_type VARCHAR(40),
  brands TEXT,
  min_previous_month_spend INTEGER,
  min_annual_fee INTEGER,
  domestic_only BOOLEAN,
  overseas_available BOOLEAN,
  source_snapshot_date DATE NOT NULL
);

CREATE TABLE card_benefits (
  benefit_id VARCHAR(40) PRIMARY KEY,
  card_id INTEGER NOT NULL REFERENCES cards(card_id),
  category VARCHAR(80),
  benefit_type VARCHAR(40),
  benefit_value NUMERIC(12, 4),
  benefit_unit VARCHAR(20),
  min_payment INTEGER,
  previous_month_spend_condition INTEGER,
  monthly_cap INTEGER,
  per_transaction_cap INTEGER,
  daily_count_limit INTEGER,
  monthly_count_limit INTEGER,
  day_condition VARCHAR(120),
  time_condition VARCHAR(120),
  excluded_conditions TEXT,
  scoring_grade VARCHAR(40) NOT NULL,
  rule_confidence NUMERIC(4, 2),
  caution_flags TEXT,
  source_summary TEXT
);

CREATE TABLE benefit_tiers (
  benefit_id VARCHAR(40) NOT NULL REFERENCES card_benefits(benefit_id),
  tier_order INTEGER NOT NULL,
  min_spend INTEGER,
  monthly_cap INTEGER,
  benefit_value NUMERIC(12, 4),
  benefit_unit VARCHAR(20),
  needs_review BOOLEAN,
  PRIMARY KEY (benefit_id, tier_order)
);

CREATE TABLE merchant_aliases (
  alias VARCHAR(255) PRIMARY KEY,
  canonical_merchant VARCHAR(255),
  category VARCHAR(80) NOT NULL,
  match_type VARCHAR(80),
  priority INTEGER DEFAULT 0,
  source VARCHAR(80)
);

CREATE TABLE users (
  user_id VARCHAR(80) PRIMARY KEY,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE user_cards (
  user_card_id VARCHAR(80) PRIMARY KEY,
  user_id VARCHAR(80) NOT NULL REFERENCES users(user_id),
  card_id INTEGER NOT NULL REFERENCES cards(card_id),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  registered_at TIMESTAMP NOT NULL
);

CREATE TABLE transactions (
  transaction_id VARCHAR(100) PRIMARY KEY,
  user_id VARCHAR(80) NOT NULL REFERENCES users(user_id),
  user_card_id VARCHAR(80) REFERENCES user_cards(user_card_id),
  card_id INTEGER REFERENCES cards(card_id),
  approved_at TIMESTAMP NOT NULL,
  merchant_raw_name VARCHAR(255) NOT NULL,
  matched_category VARCHAR(80),
  amount INTEGER NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'KRW',
  approval_status VARCHAR(40) NOT NULL,
  is_cancelled BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE monthly_card_usage (
  usage_month CHAR(7) NOT NULL,
  user_id VARCHAR(80) NOT NULL REFERENCES users(user_id),
  user_card_id VARCHAR(80) NOT NULL REFERENCES user_cards(user_card_id),
  card_id INTEGER NOT NULL REFERENCES cards(card_id),
  previous_month_spend INTEGER NOT NULL DEFAULT 0,
  current_month_spend INTEGER NOT NULL DEFAULT 0,
  performance_estimated BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMP NOT NULL,
  PRIMARY KEY (usage_month, user_card_id)
);

CREATE TABLE benefit_usage (
  usage_month CHAR(7) NOT NULL,
  user_id VARCHAR(80) NOT NULL REFERENCES users(user_id),
  user_card_id VARCHAR(80) NOT NULL REFERENCES user_cards(user_card_id),
  benefit_id VARCHAR(40) NOT NULL REFERENCES card_benefits(benefit_id),
  used_benefit_amount INTEGER NOT NULL DEFAULT 0,
  used_count INTEGER NOT NULL DEFAULT 0,
  last_transaction_id VARCHAR(100),
  PRIMARY KEY (usage_month, user_card_id, benefit_id)
);

CREATE TABLE recommendation_logs (
  recommendation_id VARCHAR(100) PRIMARY KEY,
  user_id VARCHAR(80) NOT NULL REFERENCES users(user_id),
  transaction_id VARCHAR(100),
  requested_at TIMESTAMP NOT NULL,
  merchant_raw_name VARCHAR(255),
  amount INTEGER,
  recommended_user_card_id VARCHAR(80),
  expected_benefit_amount INTEGER,
  scoring_snapshot_json TEXT
);
