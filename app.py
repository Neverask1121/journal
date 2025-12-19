from flask import send_from_directory
from flask import Flask, render_template, request, redirect, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils  import secure_filename
import sqlite3, os

app = Flask(__name__)
app.secret_key = "secret"
DB =  "journal.db"

def query(sql, args=(), one=False):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.execute(sql, args)
    rv = cur.fetchall()
    con.commit()
    con.close()
    return (rv[0] if rv else None) if one else rv

@app.route("/")
def index():
    entries = query("SELECT * FROM entries ORDER BY date DESC")

    data = []
    for e in entries:
        images = query("SELECT * FROM images WHERE entry_id=?", (e["id"],))
        data.append({
            "entry": e,
            "images": images
        })

    return render_template("index.html", data=data)


@app.route("/comment/<int:id>", methods=["POST"])
def comment(id):
    name = request.form["name"]
    comment = request.form["comment"]
    query("INSERT INTO comments (entry_id, name, caomment) VALUES (?, ?, ?)",
    (id, name, comment))
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        user = query("SELECT * FROM users WHERE username=?", (u,), one = True)
        if user and check_password_hash(user["password_hash"], p):
            session["admin"] = True
            return redirect("/admin")
        abort(404)
    return render_template("login.html")

@app.route("/admin")
def admin():
    if not session.get("admin"):
        abort(404)
    return render_template("admin.html")

@app.route("/admin/save", methods=["POST"])
def save():
    if not session.get("admin"):
        abort(404)

    date = request.form["date"]
    content = request.form["content"]
    query("INSERT OR REPLACE INTO ENTRIES (date, content) VALUES(?, ?)", (date, content))

    entry = query("SELECT id FROM entries WHERE date=?", (date,), one=True)

    for img in request.files.getlist("image"):
        if img.filename:
            name = secure_filename(img.filename)
            img.save(os.path.join("uploads", name))
            query("INSERT INTO images (entry_id, filename) VALUES (?, ?)", (entry["id"], name))

    return redirect("/")

if __name__ == "__main__":
    app.run()

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory("uploads", filename)
