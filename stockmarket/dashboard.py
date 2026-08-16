from flask import Flask,jsonify,render_template_string
from .db import Database
HTML='''<!doctype html><title>StockMarket Robot</title><h1>StockMarket Robot</h1><table border=1 cellpadding=6><tr><th>Ticker</th><th>Price</th><th>Fair Value</th><th>Upside</th><th>Score</th><th>Signal</th></tr>{% for x in analyses %}<tr><td>{{x.ticker}}</td><td>{{"%.2f"|format(x.price)}}</td><td>{{"%.2f"|format(x.fair_value) if x.fair_value else "N/A"}}</td><td>{{"%.1f%%"|format(x.upside*100) if x.upside is not none else "N/A"}}</td><td>{{"%.1f"|format(x.master_score)}}</td><td>{{x.signal}}</td></tr>{% endfor %}</table>'''
def create_app(db_path):
    app=Flask(__name__); db=Database(db_path)
    @app.get('/')
    def home(): return render_template_string(HTML,analyses=db.latest_analyses())
    @app.get('/api/analyses')
    def analyses(): return jsonify(db.latest_analyses())
    return app
