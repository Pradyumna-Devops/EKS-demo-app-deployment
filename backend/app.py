import os
import time

from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-service"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "demoapp"),
        user=os.getenv("DB_USER", "demoapp"),
        password=os.getenv("DB_PASSWORD", "demoapp123")
    )


@app.route("/api/health", methods=["GET"])
def health():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "healthy",
            "message": "Backend and database are connected"
        })

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "message": "Database connection failed",
            "error": str(e)
        }), 500


@app.route("/api/users", methods=["GET"])
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, email FROM users ORDER BY id"
        )

        users = cursor.fetchall()

        cursor.close()
        conn.close()

        result = []

        for user in users:
            result.append({
                "id": user[0],
                "name": user[1],
                "email": user[2]
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/api/", methods=["GET"])
def api_home():
    return jsonify({
        "message": "Hello from Python Flask Backend!",
        "application": "EKS 3-Tier Demo"
    })


if __name__ == "__main__":
    # Give PostgreSQL a little time when running locally.
    time.sleep(1)

    app.run(
        host="0.0.0.0",
        port=5000
    )
