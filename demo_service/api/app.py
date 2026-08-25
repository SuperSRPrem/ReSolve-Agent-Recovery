import os
from datetime import datetime, timezone

import psycopg2
from flask import Flask, jsonify


app = Flask(__name__)


DB_HOST = os.getenv(
    "DB_HOST",
    "db"
)

DB_PORT = int(
    os.getenv(
        "DB_PORT",
        "5432"
    )
)

DB_NAME = os.getenv(
    "DB_NAME",
    "resolve_demo"
)

DB_USER = os.getenv(
    "DB_USER",
    "resolve_user"
)

DB_PASSWORD = os.getenv(
    "DB_PASSWORD",
    "resolve_password"
)


def checkDatabase():
    """
    Performs a real connection to PostgreSQL.

    This is intentionally not based on Docker container status.

    A container may be running while the database itself is
    unavailable, so ReSolve should eventually verify actual
    service behavior rather than only process state.
    """

    connection = None

    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=2,
        )

        cursor = connection.cursor()

        cursor.execute(
            "SELECT 1;"
        )

        result = cursor.fetchone()

        cursor.close()

        return (
            result is not None
            and result[0] == 1
        )

    except Exception:
        return False

    finally:
        if connection is not None:
            connection.close()


@app.get("/")
def index():
    return jsonify({
        "service": "ReSolve Demo API",
        "status": "running",
    })


@app.get("/health")
def health():
    """
    Real dependency-aware health endpoint.

    API process running + database unavailable
    does NOT equal a healthy service.
    """

    databaseHealthy = (
        checkDatabase()
    )

    response = {
        "service": "resolve-demo-api",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "apiRunning": True,
        "databaseHealthy": (
            databaseHealthy
        ),
        "healthy": (
            databaseHealthy
        ),
    }

    if databaseHealthy:
        return jsonify(
            response
        ), 200

    return jsonify(
        response
    ), 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False,
    )
