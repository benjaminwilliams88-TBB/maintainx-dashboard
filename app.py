from flask import Flask, request
import requests

app = Flask(__name__)

MX_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNzM2MTMsIm9yZ2FuaXphdGlvbklkIjo1MzEyODMsImlhdCI6MTc4OTY5MzMwMiwic3ViIjoiUkVTVF9BUElfQVVUSCIsImp0aSI6ImJlOWY2MGI2LWRmMGItNDNiMS05MTAyLTYyZDE1YjU0NTdlNiJ9.P7jYpIA63ngmwKkXM2HjLRA_pgW3vLPy54WZNnZrIlk"

# Stores currently active work orders
active_workorders = {}


def get_workorder(workorder_id):
    headers = {
        "Authorization": f"Bearer {MX_API_KEY}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            f"https://api.getmaintainx.com/v1/workorders/{workorder_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

        print(f"API Error: {response.status_code}")
        print(response.text)
        return None

    except Exception as e:
        print(f"API Exception: {e}")
        return None


@app.route("/")
def dashboard():

    html = """
    <html>
    <head>
        <title>MaintainX Live Dashboard</title>

        <meta http-equiv="refresh" content="15">

        <style>
            body {
                font-family: Arial, sans-serif;
                background: #111;
                color: white;
                padding: 20px;
            }

            h1 {
                color: #00ccff;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }

            th {
                background: #333;
                padding: 10px;
                text-align: left;
            }

            td {
                padding: 10px;
                border-bottom: 1px solid #444;
            }

            .open {
                color: #4da6ff;
                font-weight: bold;
            }

            .progress {
                color: orange;
                font-weight: bold;
            }

            .hold {
                color: red;
                font-weight: bold;
            }
        </style>
    </head>
    <body>

    <h1>MaintainX Live Dashboard</h1>

    <h2>Active Work Orders: {}</h2>

    <table>
        <tr>
            <th>WO ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Assigned</th>
            <th>Priority</th>
        </tr>
    """.format(len(active_workorders))

    for wo_id, wo in active_workorders.items():

        status = wo.get("status", "UNKNOWN")

        status_class = ""

        if status == "OPEN":
            status_class = "open"

        elif status == "IN_PROGRESS":
            status_class = "progress"

        elif status == "ON_HOLD":
            status_class = "hold"

        html += f"""
        <tr>
            <td>{wo_id}</td>
            <td>{wo.get('title','')}</td>
            <td class='{status_class}'>{status}</td>
            <td>{wo.get('assigned','')}</td>
            <td>{wo.get('priority','')}</td>
        </tr>
        """

    html += """
    </table>
    </body>
    </html>
    """

    return html


@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        return "Webhook endpoint is online"

    payload = request.json

    print("WEBHOOK RECEIVED")
    print(payload)

    workorder_id = payload.get("workOrderId")

    if not workorder_id:
        return {"status": "ignored"}, 200

    wo = get_workorder(workorder_id)

    if wo:

        status = str(
            wo.get("status")
            or wo.get("newStatus")
            or ""
        )

        assigned = ""

        try:
            assignees = wo.get("assignees", [])

            if assignees:
                first_assignee = assignees[0]

                assigned = (
                    first_assignee.get("name")
                    or first_assignee.get("fullName")
                    or ""
                )

        except Exception:
            pass

        active_workorders[workorder_id] = {
            "title": wo.get("title", ""),
            "status": status,
            "assigned": assigned,
            "priority": wo.get("priority", "")
        }

        # Remove completed work orders
        if status == "DONE":
            active_workorders.pop(workorder_id, None)

        print("ACTIVE WORK ORDERS")
        print(active_workorders)

    return {"status": "received"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
