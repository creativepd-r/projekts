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


def to_int(value, default=0):
    value = (value or "").strip()
    return int(value) if value else default


app = Flask(__name__)
init_db()


@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("players_list"))


@app.route("/players", methods=["GET"])
def players_list():
    conn = get_db()
    players = conn.execute(
        """
        SELECT id, first_name, last_name, country, birth_year, hand
        FROM players
        ORDER BY last_name, first_name, id
        """
    ).fetchall()
    conn.close()
    return render_template("players/list.html", players=players)


@app.route("/players/new", methods=["GET"])
def players_new():
    return render_template("players/new.html")


@app.route("/players", methods=["POST"])
def players_create():
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    country = request.form.get("country", "").strip() or None
    birth_year_raw = request.form.get("birth_year", "").strip()
    birth_year = int(birth_year_raw) if birth_year_raw else None
    hand = request.form.get("hand", "").strip().upper() or None

    if not first_name or not last_name:
        flash("First name and last name are required.", "error")
        return render_template("players/new.html")

    conn = get_db()
    conn.execute(
        """
        INSERT INTO players (first_name, last_name, country, birth_year, hand)
        VALUES (?, ?, ?, ?, ?)
        """,
        (first_name, last_name, country, birth_year, hand),
    )
    conn.commit()
    conn.close()
    flash("Player created.", "success")
    return redirect(url_for("players_list"))


@app.route("/players/<int:player_id>", methods=["GET"])
def players_view(player_id):
    conn = get_db()
    player = conn.execute(
        """
        SELECT id, first_name, last_name, country, birth_year, hand
        FROM players
        WHERE id = ?
        """,
        (player_id,),
    ).fetchone()
    conn.close()
    return render_template("players/view.html", player=player)


@app.route("/players/<int:player_id>/edit", methods=["GET"])
def players_edit(player_id):
    conn = get_db()
    player = conn.execute(
        """
        SELECT id, first_name, last_name, country, birth_year, hand
        FROM players
        WHERE id = ?
        """,
        (player_id,),
    ).fetchone()
    conn.close()
    return render_template("players/edit.html", player=player)


@app.route("/players/<int:player_id>", methods=["POST"])
def players_update(player_id):
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    country = request.form.get("country", "").strip() or None
    birth_year_raw = request.form.get("birth_year", "").strip()
    birth_year = int(birth_year_raw) if birth_year_raw else None
    hand = request.form.get("hand", "").strip().upper() or None

    conn = get_db()
    conn.execute(
        """
        UPDATE players
        SET first_name = ?, last_name = ?, country = ?, birth_year = ?, hand = ?
        WHERE id = ?
        """,
        (first_name, last_name, country, birth_year, hand, player_id),
    )
    conn.commit()
    conn.close()

    flash("Player updated.", "success")
    return redirect(url_for("players_view", player_id=player_id))


@app.route("/players/<int:player_id>/delete", methods=["POST"])
def players_delete(player_id):
    conn = get_db()
    conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
    conn.commit()
    conn.close()

    flash("Player deleted.", "success")
    return redirect(url_for("players_list"))


if __name__ == "__main__":
    app.run(debug=True)
