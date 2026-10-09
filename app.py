"""FindIt ML: a small lost-and-found demo using TF-IDF text similarity."""
from __future__ import annotations

import os
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("FINDIT_DATABASE", BASE_DIR / "findit.db"))
app = Flask(__name__)
app.secret_key = os.environ.get("FINDIT_SECRET_KEY", "dev-only-change-me")
PUBLIC_DEMO = os.environ.get("FINDIT_PUBLIC_DEMO", "0").lower() in {"1", "true", "yes"}


def connect_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL CHECK(status IN ('lost', 'found')),
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            event_date TEXT NOT NULL,
            contact TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")


def item_text(item):
    # Repeating important fields gives their terms more influence in TF-IDF.
    return " ".join([
        item["item_name"], item["item_name"], item["category"],
        item["category"], item["description"], item["location"],
    ])


def find_matches(item, limit=5):
    """Rank opposite-status reports with unsupervised TF-IDF cosine similarity."""
    with connect_db() as db:
        candidates = db.execute(
            "SELECT * FROM items WHERE status != ? AND id != ? ORDER BY id DESC",
            (item["status"], item["id"]),
        ).fetchall()
    if not candidates:
        return []

    corpus = [item_text(item)] + [item_text(candidate) for candidate in candidates]
    # With very short inputs the vocabulary can be empty (for example punctuation only).
    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(corpus)
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    except ValueError:
        similarities = [0.0] * len(candidates)

    ranked = []
    for candidate, similarity in zip(candidates, similarities):
        score = float(similarity)
        reasons = ["description and item details"]
        if item["category"].casefold() == candidate["category"].casefold():
            score = min(1.0, score + 0.15)
            reasons.insert(0, "same category")
        if item["location"].casefold() == candidate["location"].casefold():
            score = min(1.0, score + 0.10)
            reasons.insert(0, "same location")
        ranked.append({"item": candidate, "score": score, "reasons": reasons})
    ranked.sort(key=lambda match: match["score"], reverse=True)
    return [match for match in ranked[:limit] if match["score"] > 0]


@app.route("/")
def home():
    with connect_db() as db:
        items = db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    return render_template("index.html", items=items, public_demo=PUBLIC_DEMO)


@app.route("/report", methods=["POST"])
def report():
    fields = ["status", "item_name", "category", "description", "location", "event_date", "contact"]
    values = {field: request.form.get(field, "").strip() for field in fields}
    if values["status"] not in ("lost", "found"):
        flash("Choose whether the item was lost or found.", "error")
        return redirect(url_for("home"))
    required_fields = fields if not PUBLIC_DEMO else [field for field in fields if field != "contact"]
    if any(not values[field] for field in required_fields):
        flash("Please complete every field.", "error")
        return redirect(url_for("home"))
    if PUBLIC_DEMO:
        # Never retain personal contact details in the public classroom demo.
        values["contact"] = ""
    try:
        date.fromisoformat(values["event_date"])
    except ValueError:
        flash("Enter a valid date.", "error")
        return redirect(url_for("home"))
    with connect_db() as db:
        cursor = db.execute("""INSERT INTO items
            (status, item_name, category, description, location, event_date, contact)
            VALUES (:status, :item_name, :category, :description, :location, :event_date, :contact)""", values)
        new_id = cursor.lastrowid
        new_item = db.execute("SELECT * FROM items WHERE id = ?", (new_id,)).fetchone()
    matches = find_matches(new_item)
    return render_template("matches.html", item=new_item, matches=matches, public_demo=PUBLIC_DEMO)


@app.post("/delete/<int:item_id>")
def delete_item(item_id):
    if PUBLIC_DEMO:
        return "Report deletion is disabled in the public demo.", 404
    with connect_db() as db:
        db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    flash("Report removed.", "success")
    return redirect(url_for("home"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
