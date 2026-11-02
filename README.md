# Kolaar Connect

Graph-powered social networking application built with Flask, Neo4j, HTML, CSS, JavaScript, and Cytoscape.

## Features

- Registration, login, logout, password hashing
- Profiles, profile editing, follow/unfollow
- Posts, feed, likes, comments, deleting your own posts
- User search, friend-of-friend recommendations, mutual connections
- Interactive Cytoscape social graph
- Shortest-path, degree-centrality, trending-post analytics
- Hashtags, hashtag search, trending hashtags
- Follow, like, and comment notifications; mark read / mark all read
- Responsive dark UI

## Requirements

- Python 3.10+
- Neo4j 5.x (local Desktop or server)
- A Neo4j database with the schema below

## Setup (Windows PowerShell)

```powershell
# Activate your Conda environment first
cd U:\ACADEMICS\dbms\kolaar_connect

python -m pip install -r requirements.txt

Copy-Item .env.example .env
# Edit .env and set your actual Neo4j credentials and SECRET_KEY

python app.py
```

Open http://127.0.0.1:5000

## Neo4j schema

Run the statements in `database/schema.cypher` in Neo4j Browser.

## Optional PageRank

The `/pagerank` endpoint requires Neo4j Graph Data Science (GDS) and the named projection `kolaar-social`. Create it once:

```cypher
CALL gds.graph.project(
  'kolaar-social',
  'User',
  {FOLLOWS: {orientation: 'NATURAL'}}
);
```

If GDS is not installed/projected, PageRank will not work; the other analytics routes do not require GDS.

## Routes

| Feature | Route |
|---|---|
| Feed | `/feed` |
| Profile | `/profile/<username>` |
| Edit profile | `/profile/edit` |
| Search users | `/search?q=...` |
| Recommendations | `/recommendations` |
| Mutual connections | `/mutual/<username>` |
| Social graph | `/graph` |
| Analytics | `/analytics` |
| Shortest path | `/shortest-path` (POST) |
| Degree centrality | `/degree-centrality` |
| Trending posts | `/trending` |
| PageRank | `/pagerank` |
| Hashtag | `/hashtag/<tag>` |
| Trending hashtags | `/hashtags/trending` |
| Hashtag search | `/hashtags/search?q=...` |
| Notifications | `/notifications` |

## Security notes

- Never commit `.env` or real database credentials.
- Change `SECRET_KEY` to a strong random value.
- For production, disable Flask debug mode and add CSRF protection (e.g. Flask-WTF).
- Use HTTPS and a production WSGI server.
