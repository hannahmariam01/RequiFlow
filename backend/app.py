import os
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import boto3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

start_time = time.time()

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn

# api calls
# http://127.0.0.1:5000/
# http://127.0.0.1:5000/api/health
# http://127.0.0.1:5000/db-test
# http://127.0.0.1:5000/projects
# http://127.0.0.1:5000/projects/upload
# http://127.0.0.1:5000/projects/<project_id>

@app.route('/')
def home():
    return jsonify({"message": "welcome. you have reached the requiflow backend api."})

@app.route('/api/health')
def health():
    return jsonify({
        "status": "UP",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": time.time() - start_time
    })

@app.route('/db-test')
def db_test():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM projects;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({"projects_in_db": count})

@app.route('/projects', methods=['GET'])
def get_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, raw_text, file_url, status, created_at FROM projects ORDER BY created_at DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    projects = []
    for row in rows:
        projects.append({
            "id": row[0],
            "title": row[1],
            "raw_text": row[2],
            "file_url": row[3],
            "status": row[4],
            "created_at": row[5].isoformat()
        })
    return jsonify(projects)

@app.route('/projects/upload', methods=['POST'])
def upload_project():
    title = request.form.get('title')
    raw_text = request.form.get('raw_text')
    file = request.files.get('file')

    file_url = None
    if file:
        filename = f"{int(time.time())}_{file.filename}"
        s3_client.upload_fileobj(file, BUCKET_NAME, filename)
        file_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{filename}"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (title, raw_text, file_url) VALUES (%s, %s, %s) RETURNING id;",
        (title, raw_text, file_url)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Project created", "id": new_id, "file_url": file_url}), 201

@app.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id = %s;", (project_id,))
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()

    if deleted == 0:
        return jsonify({"message": "Project not found"}), 404
    return jsonify({"message": "Project deleted"}), 200

# Import the AI orchestrator pipeline
from orchestrator import run_pipeline
import asyncio
from user_story_agent import UserStoryAgent

user_story_agent = UserStoryAgent()

@app.route('/api/run-orchestrator', methods=['POST'])
async def run_orchestrator():
    data = request.get_json() or {}
    input_text = data.get('input_text')
    original_requirements = data.get('original_requirements')
    user_answers = data.get('user_answers')
    
    try:
        result = await run_pipeline(
            input_text=input_text,
            original_requirements=original_requirements,
            user_answers=user_answers
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Internal pipeline execution error: {str(e)}"}), 500

@app.route('/api/generate-user-stories', methods=['POST'])
async def generate_user_stories_route():
    data = request.get_json() or {}
    requirement = data.get('requirement')
    
    # Check if frontend passed detailed project context
    project_title = data.get('project_title')
    requirements = data.get('requirements')
    architecture = data.get('architecture')
    tasks = data.get('tasks')
    
    if requirements or architecture or tasks:
        context = {
            "project_title": project_title,
            "requirements": requirements,
            "architecture": architecture,
            "tasks": tasks
        }
    else:
        context = requirement

    if not context:
        return jsonify({"error": "Missing project context or requirement text"}), 400

    try:
        result = await asyncio.to_thread(user_story_agent.generate_user_stories, context)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Failed to generate user stories: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)