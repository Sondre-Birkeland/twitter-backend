from flask import Flask, request
import sqlite3

app = Flask(__name__)



@app.get("/posts")
def list_posts():
	con = sqlite3.connect("twitter.db")
	cur = con.cursor()
	posts = cur.execute("SELECT post_id FROM posts ORDER BY post_id DESC").fetchall()
	return [get_post(row[0]) for row in posts]

@app.get("/posts/<int:id>")
def get_post(id):
	con = sqlite3.connect("twitter.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	post = cur.execute(f"SELECT * FROM posts WHERE post_id IS {id}").fetchone()
	#post is a Row object, which acts like dict
	if post == None:
		return {"message": "post not found"}
	user_id = post["post_user_id"]
	user_name = cur.execute(f"SELECT user_name FROM users WHERE user_id IS {user_id}").fetchone()["user_name"]
	con.close()
	return {
		"post_id": post["post_id"],
		"post_user_id": user_id,
		"user_name": user_name,
		"post_body": post["post_body"]
	}
	
@app.post("/posts/create")
def create_post():
	new_post = request.get_json()
	#the only way I have found to deliver proper json is (curl --json @jsontest.json --url localhost:5000/posts/create) and postman
	post_user_id, post_body = new_post.values()
	con = sqlite3.connect("twitter.db")
	cur = con.cursor()
	cur.execute(f"INSERT INTO posts(post_user_id, post_body) VALUES ({post_user_id}, '{post_body}')")
	con.commit()
	con.close()
	return {"message": "Nytt innlegg ble opprettet"}
	
@app.put("/posts/edit/<int:id>")
def edit_post(id):
	new_body = request.get_json()["new_body"]
	token = str(request.headers["Authorization"].split()[1])
	con = sqlite3.connect("twitter.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	user = cur.execute(f"SELECT * FROM users WHERE user_token IS {token}").fetchone()
	if user is None:
		return {"message": "Ikke gyldig bruker"}
	post = cur.execute(f"SELECT * FROM posts where post_id IS {id}").fetchone()
	if user["user_id"] != post["post_user_id"]:
		return {"message": "Du har ikke tilgang til det innlegget"}
	cur.execute(f"UPDATE posts SET post_body = '{new_body}' WHERE post_id IS {id}")
	con.commit()
	con.close()
	return get_post(id)
	
@app.delete("/posts/delete/<int:id>")
def delete_post(id):
	token = str(request.headers["Authorization"].split()[1])
	con = sqlite3.connect("twitter.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	user = cur.execute(f"SELECT * FROM users WHERE user_token IS {token}").fetchone()
	if user is None:
		return {"message": "Ikke gyldig bruker"}
	post = cur.execute(f"SELECT * FROM posts where post_id IS {id}").fetchone()
	if user["user_id"] == post["post_user_id"]:
		cur.execute(f"DELETE FROM posts WHERE post_id IS {id}")
		con.commit()
		con.close()
		return {"message": "Innlegget ble slettet"}
	else:
		con.close()
		return {"message": "Du har ikke tilgang til det innlegget"}