import os
import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from pathlib import Path


DB_PATH = Path(__file__).parent / "tennis_stats.db"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS players (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  country TEXT,
  birth_year INTEGER,
  hand TEXT CHECK (hand IN ('R', 'L')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tournaments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  level TEXT,
  location TEXT,
  surface TEXT CHECK (surface IN ('Hard', 'Clay', 'Grass', 'Carpet')),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL,
  match_date TEXT NOT NULL,
  round TEXT,
  best_of INTEGER NOT NULL DEFAULT 3,
  winner_player_id INTEGER NOT NULL,
  loser_player_id INTEGER NOT NULL,
  score TEXT,
  FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE RESTRICT,
  FOREIGN KEY (winner_player_id) REFERENCES players(id) ON DELETE RESTRICT,
  FOREIGN KEY (loser_player_id) REFERENCES players(id) ON DELETE RESTRICT,
  CHECK (winner_player_id != loser_player_id)
);

CREATE TABLE IF NOT EXISTS match_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  match_id INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  aces INTEGER NOT NULL DEFAULT 0,
  double_faults INTEGER NOT NULL DEFAULT 0,
  first_serve_in INTEGER NOT NULL DEFAULT 0,
  first_serve_total INTEGER NOT NULL DEFAULT 0,
  winners INTEGER NOT NULL DEFAULT 0,
  unforced_errors INTEGER NOT NULL DEFAULT 0,
  break_points_won INTEGER NOT NULL DEFAULT 0,
  break_points_total INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE RESTRICT,
  UNIQUE (match_id, player_id)
);

CREATE TRIGGER IF NOT EXISTS players_updated_at
AFTER UPDATE ON players
FOR EACH ROW
BEGIN
  UPDATE players SET updated_at = datetime('now') WHERE id = OLD.id;
END;
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()

app = Flask(__name__)
init_db()



if __name__ == "__main__":
    app.run(debug=True)
