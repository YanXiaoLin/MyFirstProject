from flask import Flask, request, jsonify
from risk_assessment import risk_by_code, risk_by_coord, risk_by_polygon

app = Flask(__name__)

@app.route('/risk/by_code', methods=['GET'])
def api_risk_by_code():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Missing code'}), 400
    risk = risk_by_code(code)
    return jsonify({'code': code, 'risk': risk})

@app.route('/risk/by_coord', methods=['GET'])
def api_risk_by_coord():
    try:
        lon = float(request.args.get('lon'))
        lat = float(request.args.get('lat'))
        alt = float(request.args.get('alt', 0))
    except Exception:
        return jsonify({'error': 'Invalid or missing lon/lat/alt'}), 400
    code, risk = risk_by_coord(lon, lat, alt)
    return jsonify({'code': code, 'risk': risk})

@app.route('/risk/by_polygon', methods=['POST'])
def api_risk_by_polygon():
    data = request.get_json()
    polygon = data.get('polygon')
    if not polygon or not isinstance(polygon, list):
        return jsonify({'error': 'Missing or invalid polygon'}), 400
    results = risk_by_polygon(polygon)
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9010, debug=True)
