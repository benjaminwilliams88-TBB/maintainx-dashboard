from flask import Flask, request

app = Flask(__name__)

events = []

@app.route("/")
def dashboard():
    return f"""
    <h1>MaintainX Dashboard</h1>
    <h2>Recent Events: {len(events)}</h2>
    <pre>{events[-10:]}</pre>
    """

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.json
    events.append(payload)
    return {"status": "received"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
