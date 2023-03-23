DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS posts;

CREATE TABLE users (
	user_id INTEGER PRIMARY KEY,
	user_name TEXT UNIQUE NOT NULL,
	user_token INTEGER NOT NULL
);

CREATE TABLE posts (
	post_id INTEGER PRIMARY KEY,
	post_user_id INTEGER NOT NULL,
	post_body TEXT,
	FOREIGN KEY(post_user_id) REFERENCES users(user_id)
);

INSERT INTO users(user_name, user_token) VALUES 
	('Bruker En', 1111111111),
	('Bruker To', 2222222222),
	('Bruker Tre', 3333333333);

INSERT INTO posts(post_user_id, post_body) VALUES
	(1, 'Innlegg nummer en'),
	(2, 'Innlegg nummer to'),
	(3, 'Innlegg nummer tre');