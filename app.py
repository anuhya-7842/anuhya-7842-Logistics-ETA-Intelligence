
from flask import Flask, jsonify, request
from src.eta_engine import estimate_shipment_eta

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "project": "Logistics ETA Intelligence Platform",
        "status": "running",
        "message": "Shipment ETA API is available"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/api/shipments/<shipment_id>/eta", methods=["GET"])
def get_shipment_eta(shipment_id):
    as_of = request.args.get("as_of")

    try:
        result = estimate_shipment_eta(shipment_id, as_of)
        return jsonify(result), 200

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 404

    except Exception as error:
        return jsonify({
            "error": "Unable to calculate shipment ETA",
            "details": str(error)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
