import sqlite3

from flask import Flask, flash, abort, redirect, render_template, request, url_for
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

app.config["SECRET_KEY"] = "test"


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


@app.route("/tournaments", methods=["GET"])
def tournaments_list():
    conn = get_db()
    tournaments = conn.execute(
        """
        SELECT id, name, level, location, surface
        FROM tournaments
        ORDER BY name, id
        """
    ).fetchall()
    conn.close()
    return render_template("tournaments/list.html", tournaments=tournaments)


@app.route("/tournaments/new", methods=["GET"])
def tournaments_new():
    return render_template("tournaments/new.html")


@app.route("/tournaments", methods=["POST"])
def tournaments_create():
    name = request.form.get("name", "").strip()
    level = request.form.get("level", "").strip() or None
    location = request.form.get("location", "").strip() or None
    surface = request.form.get("surface", "").strip() or None
    if not name:
        flash("Tournament name is required.", "error")
        return render_template("tournaments/new.html")

    conn = get_db()
    conn.execute(
        """
        INSERT INTO tournaments (name, level, location, surface)
        VALUES (?, ?, ?, ?)
        """,
        (name, level, location, surface),
    )
    conn.commit()
    conn.close()

    flash("Tournament created.", "success")
    return redirect(url_for("tournaments_list"))


@app.route("/tournaments/<int:tournament_id>", methods=["GET"])
def tournaments_view(tournament_id):
    conn = get_db()
    tournament = conn.execute(
        "SELECT id, name, level, location, surface FROM tournaments WHERE id = ?",
        (tournament_id,),
    ).fetchone()
    conn.close()

    return render_template("tournaments/view.html", tournament=tournament)


@app.route("/tournaments/<int:tournament_id>/edit", methods=["GET"])
def tournaments_edit(tournament_id):
    conn = get_db()
    tournament = conn.execute(
        "SELECT id, name, level, location, surface FROM tournaments WHERE id = ?",
        (tournament_id,),
    ).fetchone()
    conn.close()

    return render_template("tournaments/edit.html", tournament=tournament)


@app.route("/tournaments/<int:tournament_id>", methods=["POST"])
def tournaments_update(tournament_id):
    name = request.form.get("name", "").strip()
    level = request.form.get("level", "").strip() or None
    location = request.form.get("location", "").strip() or None
    surface = request.form.get("surface", "").strip() or None

    conn = get_db()
    conn.execute(
        """
        UPDATE tournaments
        SET name = ?, level = ?, location = ?, surface = ?
        WHERE id = ?
        """,
        (name, level, location, surface, tournament_id),
    )
    conn.commit()
    conn.close()

    flash("Tournament updated.", "success")
    return redirect(url_for("tournaments_view", tournament_id=tournament_id))


@app.route("/tournaments/<int:tournament_id>/delete", methods=["POST"])
def tournaments_delete(tournament_id):
    conn = get_db()

    match_count = conn.execute(
        "SELECT COUNT(*) AS c FROM matches WHERE tournament_id = ?",
        (tournament_id,),
    ).fetchone()["c"]

    if int(match_count) > 0:
        conn.close()
        flash(
            "Cannot delete this tournament because it has matches. Delete those matches first.",
            "error",
        )
        return redirect(url_for("tournaments_view", tournament_id=tournament_id))

    cur = conn.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        abort(404)

    flash("Tournament deleted.", "success")
    return redirect(url_for("tournaments_list"))


@app.route("/matches", methods=["GET"])
def matches_list():
    conn = get_db()
    matches = conn.execute(
        """
        SELECT
            m.id,
            m.match_date,
            m.round,
            m.best_of,
            m.score,
            t.name AS tournament_name,
            wp.first_name AS winner_first,
            wp.last_name AS winner_last,
            lp.first_name AS loser_first,
            lp.last_name AS loser_last
        FROM matches m
        JOIN tournaments t ON t.id = m.tournament_id
        JOIN players wp ON wp.id = m.winner_player_id
        JOIN players lp ON lp.id = m.loser_player_id
        ORDER BY m.match_date DESC, m.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("matches/list.html", matches=matches)


@app.route("/matches/new", methods=["GET"])
def matches_new():
    conn = get_db()
    tournaments = conn.execute(
        "SELECT id, name, surface FROM tournaments ORDER BY name, id"
    ).fetchall()
    players = conn.execute(
        "SELECT id, first_name, last_name FROM players ORDER BY last_name, first_name, id"
    ).fetchall()
    conn.close()
    return render_template("matches/new.html", tournaments=tournaments, players=players)


@app.route("/matches", methods=["POST"])
def matches_create():
    tournament_id = to_int(request.form.get("tournament_id", ""), 0)
    match_date = request.form.get("match_date", "").strip()
    round_ = request.form.get("round", "").strip() or None
    best_of = to_int(request.form.get("best_of", "3"), 3)
    winner_player_id = to_int(request.form.get("winner_player_id", ""), 0)
    loser_player_id = to_int(request.form.get("loser_player_id", ""), 0)
    score = request.form.get("score", "").strip() or None

    if (
        not tournament_id
        or not match_date
        or not winner_player_id
        or not loser_player_id
    ):
        flash("Tournament, date, winner, and loser are required.", "error")
        return redirect(url_for("matches_new"))

    conn = get_db()
    conn.execute(
        """
        INSERT INTO matches (
            tournament_id, match_date, round, best_of,
            winner_player_id, loser_player_id, score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tournament_id,
            match_date,
            round_,
            best_of,
            winner_player_id,
            loser_player_id,
            score,
        ),
    )
    conn.commit()
    conn.close()

    flash("Match created.", "success")
    return redirect(url_for("matches_list"))


@app.route("/matches/<int:match_id>", methods=["GET"])
def matches_view(match_id):
    conn = get_db()
    match = conn.execute(
        """
        SELECT
            m.id,
            m.match_date,
            m.round,
            m.best_of,
            m.score,
            t.name AS tournament_name,
            t.surface AS tournament_surface,
            wp.first_name AS winner_first,
            wp.last_name AS winner_last,
            lp.first_name AS loser_first,
            lp.last_name AS loser_last
        FROM matches m
        JOIN tournaments t ON t.id = m.tournament_id
        JOIN players wp ON wp.id = m.winner_player_id
        JOIN players lp ON lp.id = m.loser_player_id
        WHERE m.id = ?
        """,
        (match_id,),
    ).fetchone()
    stats = conn.execute(
        """
        SELECT
            ms.id,
            ms.player_id,
            p.first_name,
            p.last_name,
            ms.aces,
            ms.double_faults,
            ms.first_serve_in,
            ms.first_serve_total,
            ms.winners,
            ms.unforced_errors,
            ms.break_points_won,
            ms.break_points_total
        FROM match_stats ms
        JOIN players p ON p.id = ms.player_id
        WHERE ms.match_id = ?
        ORDER BY p.last_name, p.first_name
        """,
        (match_id,),
    ).fetchall()
    conn.close()
    return render_template("matches/view.html", match=match, stats=stats)


@app.route("/matches/<int:match_id>/edit", methods=["GET"])
def matches_edit(match_id):
    conn = get_db()
    match = conn.execute(
        """
        SELECT id, tournament_id, match_date, round, best_of, winner_player_id, loser_player_id, score
        FROM matches
        WHERE id = ?
        """,
        (match_id,),
    ).fetchone()
    tournaments = conn.execute(
        "SELECT id, name, surface FROM tournaments ORDER BY name, id"
    ).fetchall()
    players = conn.execute(
        "SELECT id, first_name, last_name FROM players ORDER BY last_name, first_name, id"
    ).fetchall()
    conn.close()

    return render_template(
        "matches/edit.html",
        match=match,
        tournaments=tournaments,
        players=players,
    )


@app.route("/matches/<int:match_id>", methods=["POST"])
def matches_update(match_id):
    tournament_id = to_int(request.form.get("tournament_id", ""), 0)
    match_date = request.form.get("match_date", "").strip()
    round_ = request.form.get("round", "").strip() or None
    best_of = to_int(request.form.get("best_of", ""), 3)
    winner_player_id = to_int(request.form.get("winner_player_id", ""), 0)
    loser_player_id = to_int(request.form.get("loser_player_id", ""), 0)
    score = request.form.get("score", "").strip() or None

    conn = get_db()
    conn.execute(
        """
        UPDATE matches
        SET tournament_id = ?, match_date = ?, round = ?, best_of = ?,
            winner_player_id = ?, loser_player_id = ?, score = ?
        WHERE id = ?
        """,
        (
            tournament_id,
            match_date,
            round_,
            best_of,
            winner_player_id,
            loser_player_id,
            score,
            match_id,
        ),
    )
    conn.commit()
    conn.close()

    flash("Match updated.", "success")
    return redirect(url_for("matches_view", match_id=match_id))


@app.route("/matches/<int:match_id>/delete", methods=["POST"])
def matches_delete(match_id):
    conn = get_db()
    conn.execute("DELETE FROM matches WHERE id = ?", (match_id,))
    conn.commit()
    conn.close()

    flash("Match deleted.", "success")
    return redirect(url_for("matches_list"))


@app.route("/match-stats", methods=["GET"])
def match_stats_list():
    conn = get_db()
    stats = conn.execute(
        """
        SELECT
            ms.id,
            ms.match_id,
            ms.player_id,
            ms.aces,
            ms.double_faults,
            ms.first_serve_in,
            ms.first_serve_total,
            ms.winners,
            ms.unforced_errors,
            ms.break_points_won,
            ms.break_points_total,
            m.match_date,
            t.name AS tournament_name,
            p.first_name,
            p.last_name
        FROM match_stats ms
        JOIN matches m ON m.id = ms.match_id
        JOIN tournaments t ON t.id = m.tournament_id
        JOIN players p ON p.id = ms.player_id
        ORDER BY m.match_date DESC, ms.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("match_stats/list.html", stats=stats)


@app.route("/match-stats/new", methods=["GET"])
def match_stats_new():
    conn = get_db()
    matches = conn.execute(
        """
        SELECT
            m.id,
            m.match_date,
            t.name AS tournament_name,
            wp.last_name AS winner_last,
            lp.last_name AS loser_last
        FROM matches m
        JOIN tournaments t ON t.id = m.tournament_id
        JOIN players wp ON wp.id = m.winner_player_id
        JOIN players lp ON lp.id = m.loser_player_id
        ORDER BY m.match_date DESC, m.id DESC
        """
    ).fetchall()
    players = conn.execute(
        "SELECT id, first_name, last_name FROM players ORDER BY last_name, first_name, id"
    ).fetchall()
    conn.close()
    return render_template("match_stats/new.html", matches=matches, players=players)


@app.route("/match-stats", methods=["POST"])
def match_stats_create():
    match_id = to_int(request.form.get("match_id", ""), 0)
    player_id = to_int(request.form.get("player_id", ""), 0)
    if not match_id or not player_id:
        flash("Match and player are required.", "error")
        return redirect(url_for("match_stats_new"))

    conn = get_db()
    conn.execute(
        """
        INSERT INTO match_stats (
            match_id, player_id,
            aces, double_faults,
            first_serve_in, first_serve_total,
            winners, unforced_errors,
            break_points_won, break_points_total
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            match_id,
            player_id,
            to_int(request.form.get("aces", "0"), 0),
            to_int(request.form.get("double_faults", "0"), 0),
            to_int(request.form.get("first_serve_in", "0"), 0),
            to_int(request.form.get("first_serve_total", "0"), 0),
            to_int(request.form.get("winners", "0"), 0),
            to_int(request.form.get("unforced_errors", "0"), 0),
            to_int(request.form.get("break_points_won", "0"), 0),
            to_int(request.form.get("break_points_total", "0"), 0),
        ),
    )
    conn.commit()
    conn.close()

    flash("Match stat created.", "success")
    return redirect(url_for("match_stats_list"))


@app.route("/match-stats/<int:stat_id>", methods=["GET"])
def match_stats_view(stat_id):
    conn = get_db()
    stat = conn.execute(
        """
        SELECT
            ms.id,
            ms.match_id,
            ms.player_id,
            ms.aces,
            ms.double_faults,
            ms.first_serve_in,
            ms.first_serve_total,
            ms.winners,
            ms.unforced_errors,
            ms.break_points_won,
            ms.break_points_total,
            m.match_date,
            t.name AS tournament_name,
            p.first_name,
            p.last_name
        FROM match_stats ms
        JOIN matches m ON m.id = ms.match_id
        JOIN tournaments t ON t.id = m.tournament_id
        JOIN players p ON p.id = ms.player_id
        WHERE ms.id = ?
        """,
        (stat_id,),
    ).fetchone()
    conn.close()
    return render_template("match_stats/view.html", stat=stat)


@app.route("/match-stats/<int:stat_id>/edit", methods=["GET"])
def match_stats_edit(stat_id):
    conn = get_db()
    stat = conn.execute(
        """
        SELECT
            id, match_id, player_id,
            aces, double_faults, first_serve_in, first_serve_total,
            winners, unforced_errors, break_points_won, break_points_total
        FROM match_stats
        WHERE id = ?
        """,
        (stat_id,),
    ).fetchone()
    conn.close()
    return render_template("match_stats/edit.html", stat=stat)


@app.route("/match-stats/<int:stat_id>", methods=["POST"])
def match_stats_update(stat_id):
    conn = get_db()
    conn.execute(
        """
        UPDATE match_stats
        SET aces = ?, double_faults = ?, first_serve_in = ?, first_serve_total = ?,
            winners = ?, unforced_errors = ?, break_points_won = ?, break_points_total = ?
        WHERE id = ?
        """,
        (
            to_int(request.form.get("aces", "0"), 0),
            to_int(request.form.get("double_faults", "0"), 0),
            to_int(request.form.get("first_serve_in", "0"), 0),
            to_int(request.form.get("first_serve_total", "0"), 0),
            to_int(request.form.get("winners", "0"), 0),
            to_int(request.form.get("unforced_errors", "0"), 0),
            to_int(request.form.get("break_points_won", "0"), 0),
            to_int(request.form.get("break_points_total", "0"), 0),
            stat_id,
        ),
    )
    conn.commit()
    conn.close()

    flash("Match stat updated.", "success")
    return redirect(url_for("match_stats_view", stat_id=stat_id))


@app.route("/match-stats/<int:stat_id>/delete", methods=["POST"])
def match_stats_delete(stat_id):
    conn = get_db()
    conn.execute("DELETE FROM match_stats WHERE id = ?", (stat_id,))
    conn.commit()
    conn.close()

    flash("Match stat deleted.", "success")
    return redirect(url_for("match_stats_list"))


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
