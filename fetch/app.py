from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Dictionary to store transactions of each payer
transactions = {}
# Dictionary to store balance of each payer
balance = {}


@app.route('/add', methods=['POST'])
def add_points():
    """
    Endpoint to add points to a payer.
    Expects a JSON object with payer, points, and timestamp.
    Updates both transactions and balance of the payer.

    Example JSON object:
    { "payer": "DANNON", "points": 300, "timestamp": "2022-10-31T 10:00:00 Z" }
    """
    data = request.get_json()
    payer = data['payer']
    points = data['points']
    timestamp = data['timestamp']

    # Create a new entry for payer if not already present
    if payer not in transactions:
        transactions[payer] = []

    # Append new transaction and update balance
    transactions[payer].append(
        {'points': points, 'timestamp': datetime.strptime(timestamp, '%Y-%m-%dT %H:%M:%S Z'), 'payer': payer})
    balance[payer] = balance.get(payer, 0) + points

    return '', 200


@app.route('/spend', methods=['POST'])
def spend():
    """
    Endpoint to spend points. Spends the oldest points first and does not allow any payer's points to go negative.
    Expects a JSON object with points to be spent.
    Returns a list of payers and the points deducted from each.

    Example JSON object:
    { "points": 5000 }
    """
    data = request.get_json()
    points = data['points']

    # Check if enough points are available to spend
    total_points = sum(balance.values())
    if points > total_points:
        return "The user doesn't have enough points", 400

    # Calculate points to be deducted from each payer and return the list
    spent = spend_points(points)
    return jsonify(spent), 200


def spend_points(points):
    """
    Helper function to calculate points to be deducted from each payer.
    Deducts the oldest points first and does not allow any payer's points to go negative.
    Returns a list of payers and the points deducted from each.
    """
    spent = []

    # Sort all transactions by timestamp
    sorted_transactions = sorted((trans for payer_trans in transactions.values() for trans in payer_trans),
                                 key=lambda x: x['timestamp'])

    # Iterate over sorted transactions and deduct points
    for transaction in sorted_transactions:
        payer = transaction['payer']
        available_points = transaction['points']

        if points <= 0:
            break

        points_to_deduct = min(points, available_points)
        transaction['points'] -= points_to_deduct
        points -= points_to_deduct

        # Update balance and prepare the response
        balance[payer] = max(0, balance.get(payer, 0) - points_to_deduct)

        for s in spent:
            if s['payer'] == payer:
                s['points'] -= points_to_deduct
                break
        else:
            spent.append({'payer': payer, 'points': -points_to_deduct})

    return spent


@app.route('/balance', methods=['GET'])
def get_balance():
    """
    Endpoint to get the balance of points for each payer.
    Returns a JSON object with payers and their respective point balances.
    """
    return jsonify(balance), 200


if __name__ == '__main__':
    app.run(port=8000)
