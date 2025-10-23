from flask import Flask
import psycopg2
import os

app = Flask(__name__)

@app.route('/')
def home():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
        )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    cur.close()
    conn.close()
    return f"Connected to PostgreSQL version: {version}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)