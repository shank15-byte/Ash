import os

from flask import Flask, jsonify, request, send_from_directory
import numpy as np

app = Flask(__name__, static_folder='.')

REGIONS = [
    {'id': 'atlantic', 'name': 'Atlantic Forest, Brazil', 'lat': -22.5, 'lng': -43.2, 'degradation_percentage': 72, 'current_tree_cover': 28, 'biodiversity_score': 41, 'water_availability': 52, 'carbon_potential': 8.4},
    {'id': 'ghats', 'name': 'Western Ghats, India', 'lat': 11.4, 'lng': 76.8, 'degradation_percentage': 48, 'current_tree_cover': 43, 'biodiversity_score': 58, 'water_availability': 61, 'carbon_potential': 7.8},
    {'id': 'maasai', 'name': 'Maasai Steppe, Tanzania', 'lat': -5.8, 'lng': 35.4, 'degradation_percentage': 68, 'current_tree_cover': 19, 'biodiversity_score': 35, 'water_availability': 39, 'carbon_potential': 6.2},
    {'id': 'mekong', 'name': 'Lower Mekong, Cambodia', 'lat': 12.3, 'lng': 105.3, 'degradation_percentage': 57, 'current_tree_cover': 34, 'biodiversity_score': 46, 'water_availability': 48, 'carbon_potential': 7.1},
    {'id': 'appalachia', 'name': 'Appalachian Foothills, USA', 'lat': 36.4, 'lng': -82.7, 'degradation_percentage': 39, 'current_tree_cover': 51, 'biodiversity_score': 63, 'water_availability': 68, 'carbon_potential': 6.8},
]
STRATEGIES = {'reforestation': {'cover': 94, 'rate': .20, 'carbon': 1.0, 'water': 23, 'cost': 3100, 'bio': 1.0}, 'natural_regrowth': {'cover': 87, 'rate': .13, 'carbon': .76, 'water': 18, 'cost': 1150, 'bio': 1.12}, 'agroforestry': {'cover': 85, 'rate': .16, 'carbon': .84, 'water': 20, 'cost': 2200, 'bio': .92}}
SOIL = {'loamy': 1.0, 'sandy': .83, 'clay': .92}

@app.get('/')
def index(): return send_from_directory('.', 'index.html')

@app.get('/<path:filename>')
def public_asset(filename):
    """Serve the single-page application's root-level public assets."""
    if filename not in {'style.css', 'script.js'}:
        return jsonify(error='Not found'), 404
    return send_from_directory('.', filename)

@app.get('/api/regions')
def regions(): return jsonify(REGIONS)

@app.post('/api/restoration-cost')
def restoration_cost():
    data = request.get_json(force=True); area = max(1, int(data.get('area_hectares', 1))); strategy = STRATEGIES.get(data.get('strategy'), STRATEGIES['reforestation'])
    base = area * strategy['cost']; return jsonify(cost_breakdown={'Site preparation': round(base*.23), 'Planting & materials': round(base*.41), 'Community stewardship': round(base*.19), 'Monitoring & maintenance': round(base*.17)}, total_cost=round(base))

@app.post('/api/simulate')
def simulate():
    data = request.get_json(force=True); required = ['area_hectares','strategy','soil_type','latitude','longitude','years']
    if any(key not in data for key in required): return jsonify(error='Missing simulation inputs'), 400
    try: area, years = int(data['area_hectares']), int(data['years']); strategy = STRATEGIES[data['strategy']]; soil = SOIL[data['soil_type']]
    except (ValueError, KeyError, TypeError): return jsonify(error='Invalid simulation inputs'), 400
    if not 10 <= area <= 100000 or not 1 <= years <= 100: return jsonify(error='Inputs outside supported range'), 400
    t = np.arange(0, years + 1); start, maximum = 30, strategy['cover']
    logistic = 1 / (1 + np.exp(-strategy['rate'] * soil * (t - years*.36)))
    cover = start + (maximum-start) * (logistic-logistic[0])/(logistic[-1]-logistic[0])
    annual_carbon = (cover/100)**1.55 * 8.2 * soil * strategy['carbon'] * area
    carbon = np.cumsum(annual_carbon); biodiversity = 32 + 61 * strategy['bio'] * (1/(1+np.exp(-.19*soil*(t-years*.40))))
    biodiversity = np.minimum(98, biodiversity); water = 48 + strategy['water'] * (cover-start)/(maximum-start); temperature = 1.85 * (cover-start)/(maximum-start) * soil
    base = area * strategy['cost']; risks = {'Flood risk': (66, 66 - int(24*strategy['water']/23)), 'Drought risk': (62, 62 - int(20*strategy['water']/23)), 'Wildfire risk': (54, 54 - int(18*soil))}
    risk_results = {name: {'current': current, 'projected': max(12, projected), 'reduction': round((current-max(12,projected))/current*100)} for name,(current,projected) in risks.items()}
    breakdown = {'Site preparation': round(base*.23), 'Planting & materials': round(base*.41), 'Community stewardship': round(base*.19), 'Monitoring & maintenance': round(base*.17)}
    return jsonify(input={'years':years,'strategy':data['strategy']}, timeline={'years':t.tolist(),'tree_cover':np.round(cover,1).tolist(),'carbon':np.round(carbon,0).tolist(),'biodiversity':np.round(biodiversity,1).tolist(),'water':np.round(water,1).tolist(),'temperature':np.round(temperature,2).tolist()}, summary={'tree_cover':round(float(cover[-1]),1),'carbon_sequestered':round(float(carbon[-1])),'biodiversity_index':round(float(biodiversity[-1])),'water_availability':round(float(water[-1])),'temperature_reduction':round(float(temperature[-1]),2),'total_cost':round(base)}, cost_breakdown=breakdown, risks=risk_results)

if __name__ == '__main__':
    # Render supplies PORT at runtime; Gunicorn uses the `app:app` entry point
    # in production, while this remains convenient for local development.
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', '').lower() == 'true',
    )
