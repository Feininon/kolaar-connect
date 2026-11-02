# Kolaar Connect

A graph-powered social networking application built with **Flask**, **Neo4j**, and **Cytoscape.js**. Kolaar Connect combines familiar social features—profiles, posts, likes, comments, and notifications—with graph-based discovery and network analytics.

> **Project status:** Academic / learning project. Intended for local development and demonstration; review the security checklist before deploying publicly.

## Contents

- [Highlights](#highlights)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Neo4j setup](#neo4j-setup)
- [Configuration](#configuration)
- [Run the application](#run-the-application)
- [Application pages](#application-pages)
- [Graph analytics](#graph-analytics)
- [Troubleshooting](#troubleshooting)
- [Security checklist](#security-checklist)

## Highlights

### Social networking
- Account registration, login, and logout
- User profiles and profile editing
- Follow and unfollow users
- Feed creation and viewing
- Like and comment on posts
- Delete your own posts
- User search
- Friend-of-friend recommendations and mutual connections

### Graph features
- Interactive social graph powered by Cytoscape.js
- Click graph nodes to open user profiles
- Shortest-path exploration
- Degree-centrality analysis
- Trending-post analysis
- Optional PageRank integration through Neo4j Graph Data Science (GDS)

### Community features
- Hashtags on posts
- Hashtag search and hashtag feeds
- Trending hashtags
- Follow, like, and comment notifications
- Mark notifications as read or mark all as read

### Interface
- Responsive dark-themed interface
- Shared navigation and page layout
- Interactive graph visualization

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Authentication | Flask-Login |
| Database | Neo4j |
| Database access | Neo4j Python Driver |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| Graph visualization | Cytoscape.js |

## Project structure

```text
kolaar-connect/
├── app.py                      # Flask application and blueprint registration
├── config.py                   # Application configuration
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variable template
├── database/
│   ├── neo4j_connection.py     # Neo4j driver and connection verification
│   └── schema.cypher           # Database schema setup (if populated)
├── models/
│   └── user.py                 # Flask-Login user model
├── routes/
│   ├── auth.py                 # Registration and authentication
│   ├── posts.py                # Feed, posts, likes, comments
│   ├── profile.py              # Profiles and follow actions
│   ├── discovery.py             # Search and recommendations
│   ├── graph.py                 # Social graph page and graph data
│   ├── analytics.py             # Network analytics
│   ├── hashtags.py               # Hashtag features
│   └── notifications.py          # Notifications
├── templates/                    # Jinja2 HTML templates
└── static/
    └── css/
        └── style.css              # Main stylesheet
```

## Prerequisites

- **Python 3.10 or newer**
- **Neo4j 5.x** (Neo4j Desktop or a running Neo4j server)
- A Neo4j database and its connection credentials
- Internet access in the browser for the Cytoscape.js CDN (unless you host Cytoscape locally)

## Installation

### 1. Clone or download the project

```bash
git clone <repository-url>
cd kolaar-connect
```

If you downloaded the ZIP instead, extract it and open the extracted project folder in your terminal or VS Code.

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Conda (optional):**

```powershell
conda create -n kolaar-connect python=3.12
conda activate kolaar-connect
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Create your environment file

```powershell
Copy-Item .env.example .env
```

Edit `.env` and enter your actual Neo4j credentials. **Do not commit `.env`.**

## Neo4j setup

1. Start your Neo4j DBMS in Neo4j Desktop or start your Neo4j server.
2. Open Neo4j Browser for the database.
3. Ensure the database name in `.env` matches the database you are using (usually `neo4j`).
4. Create the constraints below once. If `database/schema.cypher` contains the schema for your copy, you can run that file's statements instead.

```cypher
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

CREATE CONSTRAINT username_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS UNIQUE;

CREATE CONSTRAINT email_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.email IS UNIQUE;

CREATE CONSTRAINT post_id_unique IF NOT EXISTS
FOR (p:Post) REQUIRE p.post_id IS UNIQUE;

CREATE CONSTRAINT comment_id_unique IF NOT EXISTS
FOR (c:Comment) REQUIRE c.comment_id IS UNIQUE;

CREATE CONSTRAINT hashtag_name_unique IF NOT EXISTS
FOR (h:Hashtag) REQUIRE h.name IS UNIQUE;
```

The application uses `User` nodes and relationships such as `FOLLOWS`, `CREATED`, `LIKES`, `WROTE`, `HAS_COMMENT`, and `HAS_TAG`. The exact properties and relationship directions should match the Cypher queries in `routes/`.

## Configuration

Example `.env`:

```dotenv
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j
SECRET_KEY=replace_with_a_long_random_secret
```

| Variable | Description |
|---|---|
| `NEO4J_URI` | Neo4j Bolt/Neo4j connection URI |
| `NEO4J_USERNAME` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |
| `NEO4J_DATABASE` | Database name |
| `SECRET_KEY` | Flask session-signing secret |

Use the URI provided by your Neo4j instance. Common local values include `neo4j://localhost:7687` or `bolt://localhost:7687`; cloud instances require their provided URI and TLS settings.

## Run the application

From the project root, with your virtual environment active:

```powershell
python app.py
```

Then open:

**http://127.0.0.1:5000**

Register an account and sign in. Keep the terminal open while using the development server.

## Application pages

| Page / feature | Route |
|---|---|
| Feed | `/feed` |
| User profile | `/profile/<username>` |
| Edit profile | `/profile/edit` |
| User search | `/search?q=<query>` |
| Recommendations | `/recommendations` |
| Mutual connections | `/mutual/<username>` |
| Social graph | `/graph` |
| Graph data endpoint | `/api/graph` |
| Analytics dashboard | `/analytics` |
| Shortest path | `/shortest-path` (POST) |
| Degree centrality | `/degree-centrality` |
| Trending posts | `/trending` |
| PageRank | `/pagerank` |
| Hashtag feed | `/hashtag/<tag>` |
| Trending hashtags | `/hashtags/trending` |
| Hashtag search | `/hashtags/search?q=<query>` |
| Notifications | `/notifications` |

Some routes require an authenticated session. Use the application UI rather than opening POST endpoints directly in the browser.

## Graph analytics

### Shortest path, degree centrality, and trending
These features use Cypher queries through the Neo4j driver. They do not require the GDS plugin unless the implementation in your copy explicitly uses it.

### PageRank (optional)

The `/pagerank` feature requires **Neo4j Graph Data Science (GDS)** and a graph projection named `kolaar-social`. If GDS is installed, create the projection once:

```cypher
CALL gds.graph.project(
  'kolaar-social',
  'User',
  {FOLLOWS: {orientation: 'NATURAL'}}
);
```

If the projection already exists, do not create it again; drop/recreate it only when you intentionally need to refresh its definition. If GDS is unavailable, PageRank may fail while the other features continue to work.

## Troubleshooting

### `URI scheme b'' is not supported`
- Check that `.env` exists in the project root.
- Confirm `NEO4J_URI` is present and not blank.
- Confirm `python-dotenv` is installed and the application loads `.env`.
- Restart Flask after editing `.env`.

### Neo4j connection refused / unable to connect
- Start the Neo4j DBMS.
- Verify the URI, port, username, password, and database.
- Confirm the DBMS is listening on the configured port (commonly `7687`).

### Authentication or database errors
- Verify the credentials in `.env`.
- Check that the database name is correct and online.
- Run the schema constraints in Neo4j Browser.

### `/graph` opens but the visualization is blank
- Make sure the browser can load Cytoscape.js from its CDN.
- Open `/api/graph` while logged in and check that it returns JSON containing `nodes` and `edges`.
- Open browser Developer Tools (**F12 → Console** and **Network**) to inspect JavaScript errors or failed requests.
- Ensure the graph container has a non-zero height; the supplied graph template sets one.

## Security checklist

Before any public deployment:

- [ ] Set a long, random `SECRET_KEY`.
- [ ] Never commit `.env`, credentials, or database dumps.
- [ ] Disable Flask debug mode.
- [ ] Add CSRF protection to forms.
- [ ] Use HTTPS.
- [ ] Run behind a production WSGI server (for example, Waitress on Windows or Gunicorn on Linux).
- [ ] Restrict database network access and use a least-privilege Neo4j account.
- [ ] Validate and limit user-generated content and uploads (if uploads are added).
- [ ] Review authentication, authorization, and rate limiting.

## License

No license is specified yet. Add a `LICENSE` file before distributing the project if you want to grant others explicit reuse permissions.
