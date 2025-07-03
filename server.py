# server.py
from flask import Flask, request, make_response

app = Flask(__name__)

# 🔹 Used by the invisible <img>; no CORS required to prove the point
@app.route("/img")
def img():
    print("IMG hit with", dict(request.args))
    tiny_gif = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
        b"\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
        b"\x00\x00\x02\x02D\x01\x00;"
    )
    r = make_response(tiny_gif)
    r.headers["Content-Type"] = "image/gif"
    return r

# 🔹 Demonstrates full CORS & Private-Network-Access round-trip
@app.route("/hello", methods=["POST", "OPTIONS"])
def hello():
    # Pre-flight
    if request.method == "OPTIONS":
        r = make_response("", 204)
        r.headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
        return r

    print("POST /hello", request.get_json(silent=True))
    r = make_response({"msg": "hi from localhost"}, 200)
    r.headers.update({
        "Access-Control-Allow-Origin": "*",
    })
    return r

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000)
