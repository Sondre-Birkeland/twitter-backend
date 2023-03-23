from flask import Flask, request, Response, g
import json
import sqlite3
import base64
from functools import lru_cache

app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("twitter.db")
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def authenticate(id=None):
	token_64 = str(request.headers["Authorization"].split()[1])
	token_64_bytes = token_64.encode("ascii")
	token_bytes = base64.b64decode(token_64_bytes)
	token = token_bytes.decode("ascii")
	db = get_db()
	user = db.execute("SELECT * FROM users WHERE user_token IS ?", (token,)).fetchone()
	if user is None:
		return Response(json.dumps({"message": "Ikke gyldig bruker"}), 401, content_type="application/json")
	elif id is not None:
		post = db.execute("SELECT * FROM posts where post_id IS ?", (id,)).fetchone()
		if user["user_id"] != post["post_user_id"]:
			return Response(json.dumps({"message": "Du har ikke tilgang til det innlegget"}), 403, content_type="application/json")
	return user["user_id"]

@lru_cache
def get_user_name(user_id):
	db = get_db()
	return db.execute("SELECT user_name FROM users WHERE user_id IS ?", (user_id,)).fetchone()["user_name"]

def fix_post(post):
	return {
		"post_id": post["post_id"],
		"post_user_id": post["post_user_id"],
		"user_name": get_user_name(post["post_user_id"]),
		"post_body": post["post_body"]
	}

@app.get("/api/v1/posts/all")
def list_posts():
	db = get_db()
	posts = db.execute("SELECT * FROM posts ORDER BY post_id DESC").fetchall()
	posts_return = [fix_post(post) for post in posts]
	close_db()
	return Response(json.dumps(posts_return), 200, content_type="application/json")

@app.get("/api/v1/posts/<int:id>")
def get_post(id):
	db = get_db()
	post = db.execute("SELECT * FROM posts WHERE post_id IS ?", (id,)).fetchone()
	#post is a Row object, which acts like dict
	if post == None:
		return Response(status=404, response=json.dumps({"message":"post not found"}), content_type="application/json")
	fixed_post = fix_post(post)
	close_db()
	return Response(json.dumps(fixed_post), 200, content_type="application/json")
	
@app.post("/api/v1/posts/create")
def create_post():
	post_body = request.get_json()["post_body"]
	#the only way I have found to deliver proper json is (curl --json @jsontest.json --url localhost:5000/posts/create) and postman
	auth = authenticate() #auth er bruker-id hvis brukeren er gyldig og har tilgang, ellers er det en feilmelding
	if type(auth) is not int:
		close_db()
		return auth
	db = get_db()
	db.execute("INSERT INTO posts(post_user_id, post_body) VALUES(?,?)", (auth, post_body))
	db.commit()
	id = db.execute("SELECT post_id FROM posts ORDER BY post_id DESC LIMIT 1").fetchone()[0]
	close_db()
	return Response(json.dumps({"message": "Nytt innlegg ble opprettet"}), 201, {"Location": f"/posts/{id}"}, content_type="application/json")
	
@app.put("/api/v1/posts/edit/<int:id>")
def edit_post(id):
	new_body = request.get_json()["new_body"]
	auth = authenticate(id)
	if type(auth) is not int:
		close_db()
		return auth
	db = get_db()
	db.execute("UPDATE posts SET post_body = ? WHERE post_id IS ?", (new_body, id))
	db.commit()
	post = db.execute("SELECT * FROM posts where post_id IS ?", (id,)).fetchone()
	close_db()
	return Response(json.dumps({
		"post_id": post["post_id"],
		"post_user_id": post["post_user_id"],
		"post_body": post["post_body"]
	}),
	204,
	content_type="application/json")
	
@app.delete("/api/v1/posts/delete/<int:id>")
def delete_post(id):
	auth = authenticate(id)
	if type(auth) is not int:
		close_db()
		return auth
	db = get_db()
	db.execute("DELETE FROM posts WHERE post_id IS ?", (id,))
	db.commit()
	close_db()
	return Response(json.dumps({"message": "Innlegget ble slettet"}), 204, content_type="application/json")

@app.get("/api/v1/users/all")
def list_users():
	db = get_db()
	users = db.execute("SELECT * FROM users ORDER BY user_id DESC").fetchall()
	users_return = []
	for user in users:
		user_id = user["user_id"]
		user_posts = db.execute("SELECT post_id FROM posts WHERE post_user_id IS ?", (user_id,)).fetchall()
		user_return = {
			"user_id": user["user_id"],
			"user_name": user["user_name"],
			"user_posts": [row["post_id"] for row in user_posts]
			}
		users_return.append(user_return)
	close_db()
	return Response(json.dumps(users_return), 200, content_type="application/json")
	
@app.get("/api/v1/users/<int:id>")
def get_user(id):
	db = get_db()
	user = db.execute("SELECT * FROM users WHERE user_id IS ?", (id,)).fetchone()
	if user == None:
		return Response(status=404, response=json.dumps({"message":"user not found"}), content_type="application/json")
	user_posts = db.execute(f"SELECT post_id FROM posts WHERE post_user_id IS ?", (id,)).fetchall()
	close_db()
	return Response(json.dumps({
		"user_id": id,
		"user_name": user["user_name"],
		"user_posts": [row["post_id"] for row in user_posts]
	}),
	200,
	content_type="application/json")

@app.get("/api/v1/users/<int:id>/posts")
def list_user_posts(id):
	db = get_db()
	posts = db.execute(f"SELECT * FROM posts WHERE post_user_id IS ? ORDER BY post_id DESC", (id,)).fetchall()
	posts_return = [fix_post(post) for post in posts]
	close_db()
	return Response(json.dumps(posts_return), 200, content_type="application/json")

@app.post("/api/v1/users/register")
def register_user():
	new_user = request.get_json()
	user_name, user_token = new_user.values()
	db = get_db()
	db.execute("INSERT INTO users(user_name, user_token) VALUES (?,?)", (user_name, user_token))
	db.commit()
	id = db.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1").fetchone()[0]
	close_db()
	return Response(json.dumps({"message": "Ny bruker ble registrert"}), 201, {"Location": f"/users/{id}"}, content_type="application/json")