from flask import Flask, request
import requests

app = Flask(__name__)

MX_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNzM2MTMsIm9yZ2FuaXphdGlvbklkIjo1MzEyODMsImlhdCI6MTc4OTY5MzMwMiwic3ViIjoiUkVTVF9BUElfQVVUSCIsImp0aSI6ImJlOWY2MGI2LWRmMGItNDNiMS05MTAyLTYyZDE1YjU0NTdlNiJ9.P7jYpIA63ngmwKkXM2HjLRA_pgW3vLPy54WZNnZrIlk"

# Active work orders shown on dashboard
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

        print(f"API Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print("WORK ORDER DETAILS:")
            print(data)

            return data

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
                background-color: #111;
                color: white;
                padding: 20px;
            }

            h1 {
                color: #00ccff;
            }

            .summary {
                font-size: 22px;
                margin-bottom: 20px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            th {
                background-color: #333;
                padding: 12px;
                text-align: left;
            }

            td {
                padding: 12px;
                border-bottom: 1px solid #444;
            }

            .OPEN {
                color: #4da6ff;
                font-weight: bold;
            }

            .IN_PROGRESS {
                color: orange;
                font-weight: bold;
            }

            .ON_HOLD {
                color: red;
                font-weight: bold;
            }

            .DONE {
                color: #66ff66;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
    """

    html += f"""
    <h1>MaintainX Live Dashboard</h1>
    <div class="summary">
        Active Work Orders: {len(active_workorders)}
    </div>

    <table>
<tr>
<th>WO #</th>
<th>Title</th>
<th>Status</th>
<th>Priority</th>
<th>Assigned</th>
<th>Asset</th>
</tr>
    """

    for wo_id, wo in active_workorders.items():

        status = wo.get("status", "")

        html += f"""
<tr>
    <td>{wo_id}</td>
    <td>{wo.get('title','')}</td>
    <td class="{status}">{status}</td>
    <td>{wo.get('priority','')}</td>
    <td>{wo.get('assigned','')}</td>
    <td>{wo.get('asset','')}</td>
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

    print("===================================")
    print("WEBHOOK RECEIVED")
    print(payload)
    print("===================================")

    workorder_id = payload.get("workOrderId")

    if not workorder_id:
        return {"status": "ignored"}, 200

    response = get_workorder(workorder_id)

    if not response:
        return {"status": "api lookup failed"}, 200

    wo = response.get("workOrder", {})

    status = wo.get("status", "")

    active_workorders[workorder_id] = {
        "title": wo.get("title", ""),
        "status": status,
        "priority": wo.get("priority", ""),
        "assigned": ",".join(
            [str(x) for x in wo.get("assigneeIds", [])]
        ),
        "asset": wo.get("assetId", "")
    }

    # Remove completed work orders
    if status == "DONE":
        active_workorders.pop(workorder_id, None)

    print("ACTIVE WORK ORDERS")
    print(active_workorders)

    return {"status": "received"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
