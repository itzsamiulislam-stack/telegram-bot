from flask import Flask, request, jsonify
import time

app = Flask(__name__)

data = {}

@app.route("/go")
def go():
    user = request.args.get("user")
    data[user] = time.time()
    return "OK"

@app.route("/verify")
def verify():
    user = request.args.get("user")

    if user in data:
        return jsonify({"status": "ok"})
    return jsonify({"status": "fail"})

app.run(host="0.0.0.0", port=10000)
