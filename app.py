import secrets
import string
from urllib.parse import urlparse

from flask import Flask, jsonify, redirect, request

from database import get_connection, init_db


app = Flask(__name__)

CODE_LENGTH = 6


def is_valid_url(value):
    if not isinstance(value, str) or not value.strip():
        return False

    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def generate_code():
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(CODE_LENGTH))


@app.route("/links", methods=["POST"])
def create_link():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "request body must be a JSON object"
        }), 400

    target_url = data.get("url")

    if not is_valid_url(target_url):
        return jsonify({
            "error": "url must be a valid HTTP or HTTPS URL"
        }), 400

    target_url = target_url.strip()

    connection = get_connection()

    existing = connection.execute(
        "SELECT code, target_url FROM links WHERE target_url = ?",
        (target_url,)
    ).fetchone()

    if existing:
        connection.close()

        return jsonify({
            "code": existing["code"],
            "url": existing["target_url"],
            "created": False
        }), 200

    for _ in range(10):
        code = generate_code()

        try:
            connection.execute(
                """
                INSERT INTO links (code, target_url)
                VALUES (?, ?)
                """,
                (code, target_url)
            )

            connection.commit()
            connection.close()

            return jsonify({
                "code": code,
                "url": target_url,
                "created": True
            }), 201

        except Exception:
            existing = connection.execute(
                "SELECT code, target_url FROM links WHERE target_url = ?",
                (target_url,)
            ).fetchone()

            if existing:
                connection.close()

                return jsonify({
                    "code": existing["code"],
                    "url": existing["target_url"],
                    "created": False
                }), 200

    connection.close()

    return jsonify({
        "error": "could not generate a unique short code"
    }), 500


@app.route("/links/<code>", methods=["GET"])
def follow_link(code):
    connection = get_connection()

    link = connection.execute(
        """
        SELECT target_url
        FROM links
        WHERE code = ?
        """,
        (code,)
    ).fetchone()

    if link is None:
        connection.close()

        return jsonify({
            "error": "link code not found"
        }), 404

    connection.execute(
        """
        UPDATE links
        SET click_count = click_count + 1
        WHERE code = ?
        """,
        (code,)
    )

    connection.commit()
    connection.close()

    return redirect(link["target_url"], code=302)


@app.route("/links/<code>/stats", methods=["GET"])
def link_stats(code):
    connection = get_connection()

    link = connection.execute(
        """
        SELECT code, target_url, click_count
        FROM links
        WHERE code = ?
        """,
        (code,)
    ).fetchone()

    connection.close()

    if link is None:
        return jsonify({
            "error": "link code not found"
        }), 404

    return jsonify({
        "code": link["code"],
        "url": link["target_url"],
        "clicks": link["click_count"]
    }), 200


@app.errorhandler(404)
def handle_route_not_found(error):
    return jsonify({
        "error": "endpoint not found"
    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(error):
    return jsonify({
        "error": "method not allowed"
    }), 405


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)