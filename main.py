from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from dotenv import load_dotenv
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Flask (rendering off-screen)
import matplotlib.pyplot as plt

load_dotenv()

app = Flask(__name__)

def check_connectivity():
    """ Check connection to postgres. """
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

def init_db():
    """ Initialize the feedback table in PostgreSQL. """
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    cur = conn.cursor()
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS feedback_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        department VARCHAR(50) NOT NULL,
        work_environment INT CHECK (work_environment BETWEEN 1 AND 5),
        management INT CHECK (management BETWEEN 1 AND 5),
        work_life_balance INT CHECK (work_life_balance BETWEEN 1 AND 5),
        development_potential INT CHECK (development_potential BETWEEN 1 AND 5),
        overall INT CHECK (overall BETWEEN 1 AND 5)
    );
    """
    
    cur.execute(create_table_query)
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized and table ready.")

@app.route('/')
def home():
    """ Show main page. """
    return render_template('index.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """ Feedback page logic. """
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('department')
        work_env = request.form.get('work_environment')
        management = request.form.get('management')
        work_life = request.form.get('work_life_balance')
        development = request.form.get('development_potential')
        overall = request.form.get('overall')

        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO feedback_table
                (name, department, work_environment, management, work_life_balance, development_potential, overall)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, department, work_env, management, work_life, development, overall))
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            cur.close()
            conn.close()
            return "<h2>You have already submitted feedback.</h2><p><a href='/'>Back to home</a></p>"
        
        cur.close()
        conn.close()
        return redirect(url_for('feedback_submitted'))

    return render_template('feedback.html')


@app.route('/feedback_submitted')
def feedback_submitted():
    """ Show that feedback is submitted. """
    return render_template('feedback_submitted.html')

@app.route('/stats')
def stats():
    """ Display statistics from feedback database. """
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    cur = conn.cursor()

    # Overall company ranking is displayed as average
    cur.execute("SELECT AVG(overall) FROM feedback_table")
    overall_avg = cur.fetchone()[0]
    overall_avg = round(overall_avg, 2) if overall_avg else 0

    # And an emoji will be displayed next to the score based on the value
    if overall_avg < 2.5:
        overall_emoji = "😞"
    elif overall_avg < 3.5:
        overall_emoji = "😐"
    else:
        overall_emoji = "😄"

    # Department-wise ratings for each category
    categories = ["work_environment", "management", "work_life_balance", "development_potential"]
    department_data = {}

    department_colors = {
    "Marketing": "#DC647E",
    "Sales": "#36A2EB",
    "Engineering": "#19513C",
    "HR": "#C0B44B",
    "Support": "#9637EF"
    }

    for cat in categories:
        cur.execute(f"""
            SELECT department, AVG({cat})
            FROM feedback_table
            GROUP BY department
            ORDER BY department
        """)
        data = cur.fetchall()  # List of (department, avg)
        
        # Prepare data for plotting
        departments = [row[0] for row in data]
        averages = [round(row[1],2) for row in data]
        colors = [department_colors[dep] for dep in departments]

        # Create simple bar plot - can add more advanced later
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(departments, averages, color=colors, edgecolor='black', linewidth=1)
        ax.set_ylim(0,5)
        ax.set_ylabel('Average Rating')
        ax.set_title(cat.replace('_',' ').title())
        plt.xticks(rotation=45)

        # Save plot to PNG in memory
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plot_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        plt.close(fig)

        department_data[cat] = plot_data

    cur.close()
    conn.close()

    return render_template("stats.html",
                           overall_avg=overall_avg,
                           overall_emoji=overall_emoji,
                           department_data=department_data)

if __name__ == "__main__":
    init_db() # If feedback_db table is not created, creating it
    app.run(host="0.0.0.0", port=5000, debug=True)