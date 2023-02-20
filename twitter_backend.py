from flask import Flask, request, Response
import json
import sqlite3
import base64

app = Flask(__name__)

@app.get("/api/v1/posts/all")
def list_posts():
	con = sqlite3.connect("twitter.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	posts = cur.execute("SELECT * FROM posts ORDER BY post_id DESC").fetchall()
	posts_return = []
	for post in posts:
		user_id = post["post_user_id"]
		user_name = cur.execute(f"SELECT user_name FROM users WHERE user_id IS {user_id}").fetchone()["user_name"]
		post_return = {
			"post_id": post["post_id"],
			"post_user_id": user_id,
			"user_name": user_name,
			"post_body": post["post_body"]
			}
		posts_return.append(post_return)
	con.close()
	return Response(json.dumps(posts_return), 200, content_type="application/json")

@app.get("/api/v1/posts/<int:id>")
def get_post(id):
	con = sqlite3.connect("twitter.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	post = cur.execute(f"SELECT * FROM posts WHERE post_id IS {id}").fetchone()
	#post is a Row object, which acts like dict
	if post == None:
		return Response(status=404, response=json.dumps({"message":"post not found"}), content_type="application/json")
	user_id = post["post_user_id"]
	user_name = cur.execute(f"SELECT user_name FROM users WHERE user_id IS {user_id}").fetchone()["user_name"]
	con.close()
	return Response(json.dumps({
		"post_id": post["post_id"],
		"post_user_id": user_id,
		"user_name": user_name,
		"post_body": post["post_body"]
	}),
	200,
	content_type="application/json")
	
@app.post("/api/v1/posts/create")
def create_post():
	new_post = request.get_json()
	#the only way I have found to deliver proper json is (curl --json @jsontest.json --url localhost:5000/posts/create) and postman
	post_user_id, post_body = new_post.values()
	con = sqlite3.connect("twitter.db")
	cur = con.cursor()
	cur.execute(f"INSERT INTO posts(post_user_id, post_body) VALUES ({post_user_id}, '{post_body}')")
	con.commit()
	id = cur.execute("SELECT post_id FROM posts ORDER BY post_id DESC LIMIT 1").fetchone()[0]
	con.close()
	return Response(json.dumps({"message": "Nytt innlegg ble opprettet"}), 201, {"Location": f"/posts/{id}"}, content_type="application/json")
	
@app.put("/api/v1/posts/edit/<int:id>")
def edit_post(id):
	new_body = request.get_json()["new_body"]
	token_64 = str(request.headers["Authorization"].split()[1])
	token_64_bytes = token_64.encode("ascii")
	token_bytes = base64.b64decode(token_64_bytes)
	token = token_bytes.decode("ascii")
	con = sqlite3.connect("twitter.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	user = cur.execute(f"SELECT * FROM users WHERE user_token IS {token}").fetchone()
	if user is None:
		return Response(json.dumps({"message": "Ikke gyldig bruker"}), 401, content_type="application/json")
	post = cur.execute(f"SELECT * FROM posts where post_id IS {id}").fetchone()
	if user["user_id"] != post["post_user_id"]:
		return Response(json.dumps({"message": "Du har ikke tilgang til det innlegget"}), 403, content_type="application/json")
	cur.execute(f"UPDATE posts SET post_body = '{new_body}' WHERE post_id IS {id}")
	con.commit()
	post = cur.execute(f"SELECT * FROM posts where post_id IS {id}").fetchone()
	con.close()
	return Response(json.dumps({
		"post_id": post["post_id"],
		"post_user_id": post["post_user_id"],
		"post_body": post["post_body"]
	}),
	204,
	content_type="application/json")
	
@app.delete("/api/v1/posts/delete/<int:id>")
def delete_post(id):
	token_64 = str(request.headers["Authorization"].split()[1])
	token_64_bytes = token_64.encode("ascii")
	token_bytes = base64.b64decode(token_64_bytes)
	token = token_bytes.decode("ascii")
	con = sqlite3.connect("twitter.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	user = cur.execute(f"SELECT * FROM users WHERE user_token IS {token}").fetchone()
	if user is None:
		return Response(json.dumps({"message": "Ikke gyldig bruker"}), 401, content_type="application/json")
	post = cur.execute(f"SELECT * FROM posts where post_id IS {id}").fetchone()
	if user["user_id"] == post["post_user_id"]:
		cur.execute(f"DELETE FROM posts WHERE post_id IS {id}")
		con.commit()
		con.close()
		return Response(json.dumps({"message": "Innlegget ble slettet"}), 204, content_type="application/json")
	else:
		con.close()
		return Response(json.dumps({"message": "Du har ikke tilgang til det innlegget"}), 403, content_type="application/json")