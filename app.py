from flask import Flask, request
import requests

app = Flask(__name__)

import os

MX_API_KEY = os.getenv("MX_API_KEY")
active_workorders = {}

users_cache = {}
assets_cache = {}


def mx_headers():
    return {
        "Authorization": f"Bearer {MX_API_KEY}",
        "Accept": "application/json"
    }


def get_workorder(workorder_id):

    try:

        response = requests.get(
            f"https://api.getmaintainx.com/v1/workorders/{workorder_id}",
            headers=mx_headers(),
            timeout=10
        )

        print(f"WORKORDER STATUS: {response.status_code}")

        if response.status_code == 200:
            return response.json()

    except Exception as e:
        print(e)

    return None


def get_user_name(user_id):

    if user_id in users_cache:
        return users_cache[user_id]

    try:

        response = requests.get(
            f"https://api.getmaintainx.com/v1/users/{user_id}",
            headers=mx_headers(),
            timeout=10
        )

        if response.status_code == 200:

            data = response.json()

            user = data.get("user", {})

            full_name = (
                f"{user.get('firstName', '')} "
                f"{user.get('lastName', '')}"
            ).strip()

            users_cache[user_id] = full_name

            return full_name

    except Exception as e:
        print(e)

    return str(user_id)


def get_asset_name(asset_id):

    if asset_id in assets_cache:
        return assets_cache[asset_id]

    try:

        response = requests.get(
            f"https://api.getmaintainx.com/v1/assets/{asset_id}",
            headers=mx_headers(),
            timeout=10
        )

        if response.status_code == 200:

            data = response.json()

            asset = data.get("asset", {})

            name = asset.get("name", str(asset_id))

            assets_cache[asset_id] = name

            return name

    except Exception as e:
        print(e)

    return str(asset_id)


@app.route("/")
def dashboard():

    open_count = 0
    progress_count = 0
    hold_count = 0

    for wo in active_workorders.values():

        status = wo.get("status")

        if status == "OPEN":
            open_count += 1

        elif status == "IN_PROGRESS":
            progress_count += 1

        elif status == "ON_HOLD":
            hold_count += 1

    html = f"""
    <html>

    <head>

        <title>MaintainX Live Dashboard</title>

        <meta http-equiv="refresh" content="5">

        <style>

        body {{
            font-family: Arial;
            background:#111;
            color:white;
            padding:20px;
        }}

        h1 {{
            color:#00ccff;
        }}

        .cards {{
            display:flex;
            gap:20px;
            margin-bottom:30px;
        }}

        .card {{
            background:#222;
            padding:20px;
            border-radius:10px;
            min-width:150px;
            text-align:center;
        }}

        .count {{
            font-size:42px;
            font-weight:bold;
        }}

        table {{
            width:100%;
            border-collapse:collapse;
        }}

        th {{
            background:#333;
            padding:12px;
            text-align:left;
        }}

        td {{
            padding:12px;
            border-bottom:1px solid #444;
        }}

        .OPEN {{
            color:#4da6ff;
            font-weight:bold;
        }}

        .IN_PROGRESS {{
            color:orange;
            font-weight:bold;
        }}

        .ON_HOLD {{
            color:red;
            font-weight:bold;
        }}

        </style>

    </head>

    <body>

    <h1>MaintainX Live Dashboard</h1>

    <div class="cards">

        <div class="card">
            <div>OPEN</div>
            <div class="count">{open_count}</div>
        </div>

        <div class="card">
            <div>IN PROGRESS</div>
            <div class="count">{progress_count}</div>
        </div>

        <div class="card">
            <div>ON HOLD</div>
            <div class="count">{hold_count}</div>
        </div>

    </div>

    <table>

        <tr>
            <th>WO #</th>
            <th>Title</th>
            <th>Asset</th>
            <th>Assigned</th>
            <th>Priority</th>
            <th>Status</th>
        </tr>
    """

    for wo_id, wo in active_workorders.items():

        html += f"""
        <tr>

           <td>{wo.get('wo_number','')}</td>

            <td>{wo.get("title","")}</td>

            <td>{wo.get("asset","")}</td>

            <td>{wo.get("assigned","")}</td>

            <td>{wo.get("priority","")}</td>

            <td class="{wo.get("status","")}">
                {wo.get("status","")}
            </td>

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
        return "Webhook endpoint online"

    payload = request.json

    print("WEBHOOK RECEIVED")
    print(payload)

    workorder_id = payload.get("workOrderId")

    if not workorder_id:
        return {"status": "ignored"}, 200

    response = get_workorder(workorder_id)

    if not response:
        return {"status": "api lookup failed"}, 200

    wo = response.get("workOrder", {})

    status = wo.get("status", "")

    assignees = wo.get("assigneeIds", [])

    assigned_names = []

    for user_id in assignees:

        assigned_names.append(
            get_user_name(user_id)
        )

    assigned_name = ", ".join(assigned_names)

    asset_name = ""

    asset_id = wo.get("assetId")

    if asset_id:
        asset_name = get_asset_name(asset_id)

    active_workorders[workorder_id] = {

        "wo_number": wo.get("sequentialId", workorder_id),

        "title": wo.get("title", ""),
        "status": status,
        "priority": wo.get("priority", ""),
        "assigned": assigned_name,
        "asset": asset_name
    }

    if status == "DONE":
        active_workorders.pop(workorder_id, None)

    print(active_workorders)

    return {"status": "received"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
