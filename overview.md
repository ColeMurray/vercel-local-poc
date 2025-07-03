Below is a complete, minimal “click-once” proof-of-concept that shows a public page (hosted on Vercel) silently reaching into the user’s own machine at **127.0.0.1:9000**.
You’ll end up with:

* **A local HTTP service** that logs every hit and—if you like—returns JSON.
* **A static Vercel site** whose page loads an invisible image (side-effect only) **and** offers a button that fires a JavaScript `fetch()` so you can see the full CORS / PNA dance.

---

## 1 ▸ Local service (Flask)

> You can swap this for Node/Go/etc.; just keep the CORS + PNA headers and the `OPTIONS` handler.

```python
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
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Private-Network": "true",
        })
        return r

    print("POST /hello", request.get_json(silent=True))
    r = make_response({"msg": "hi from localhost"}, 200)
    r.headers.update({
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Private-Network": "true",
    })
    return r

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000)
```

```bash
pip install flask
python server.py   # Leave this running; watch the console for hits
```

---

## 2 ▸ Vercel front-end (static)

```
vercel-poc/
├─ public/
│  └─ index.html
└─ vercel.json        # optional but keeps it 100 % static
```

### `public/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Localhost Request PoC</title>
  <style>body{font-family:sans-serif;margin:2rem}</style>
</head>
<body>
  <h1>Localhost Request PoC</h1>

  <!-- Silent side-effect (no CORS bypass) -->
  <img src="http://127.0.0.1:9000/img?ts=<?=Date.now()?>" style="display:none">

  <button id="ping">POST /hello via fetch()</button>
  <pre id="log"></pre>

  <script>
    const log = m => document.querySelector('#log').textContent += m + '\n';

    document.getElementById('ping').onclick = async () => {
      try {
        const res = await fetch('http://127.0.0.1:9000/hello', {
          method: 'POST',
          mode: 'cors',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({t: Date.now()})
        });
        log(`Status ${res.status} — ${await res.text()}`);
      } catch (e) {
        log('Fetch failed: ' + e);
      }
    };
  </script>
</body>
</html>
```

### `vercel.json` (optional)

```json
{
  "builds": [],
  "outputDirectory": "public"
}
```

---

## 3 ▸ Deploy to Vercel

```bash
# one-time
npm i -g vercel

# inside vercel-poc/
vercel       # follow the prompts
vercel --prod  # to push a production URL
```

You now have e.g. `https://localhost-poc.vercel.app`.

---

## 4 ▸ Run the demo

1. **Start the Flask server** (`127.0.0.1:9000`).
2. **Visit the Vercel URL** in **the same desktop browser**.
3. **Watch your terminal**:

   * A GET `/img` arrives immediately (via the hidden `<img>`).
   * Click **“POST /hello via fetch()”** → an `OPTIONS` pre-flight followed by `POST /hello` show up.
4. Peek at the **DevTools → Network** panel:

   * You’ll see the PNA pre-flight and that Chrome labels the main request **“(from fetch)”** with **`Private Network Access`**.

---

## What this proves

* A public origin can **cause** arbitrary HTTP traffic to loop-back services.
* Without the CORS + `Access-Control-Allow-Private-Network: true` headers you **still get the hit** (pre-flight), but JS can’t read the body—useful for CSRF-style attacks.
* The invisible-image trick works even if the target never handles CORS or PNA; browsers treat `<img>`/`<script>`/`<link>` loads as “simple” and happily deliver them.

---

### Common tweaks

| Goal                       | What to change                                                                                                                                             |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Test with **Node** server  | Replace Flask with Express; keep headers identical.                                                                                                        |
| Break the fetch on purpose | Comment out the `OPTIONS` handler or the `Access-Control-Allow-Private-Network` header; the POST is blocked (but GET-side effects via `<img>` still land). |
| Use HTTPS on localhost     | Generate a self-signed cert and run Flask with `ssl_context`; browsers still treat `https://127.0.0.1` as trustworthy.                                     |

That’s it—copy-paste, deploy, and you’ve got a concrete demonstration that a live website can poke your localhost.

