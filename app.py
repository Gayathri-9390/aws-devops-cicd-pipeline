from flask import Flask, jsonify
import os

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "1.0")

@app.route("/")
def home():
    return f"""
    <html>
    <head>
        <title>AWS DevOps Project</title>
    </head>
    <body style="font-family: Arial; text-align: center; margin-top: 100px;">
        <h1>Welcome to AWS DevOps Project!</h1>
        <h2>Automated CI/CD Pipeline</h2>
        <h3>Version: {APP_VERSION}</h3>
        <p>Deployed using Jenkins, Docker and AWS.</p>
        <p>Status: Application Running Successfully</p>
    </body>
    </html>
    """

@app.route("/health")
def health():
    return jsonify(status="healthy", version=APP_VERSION)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
