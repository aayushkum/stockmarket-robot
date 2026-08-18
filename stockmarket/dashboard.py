"""Flask web dashboard for viewing analysis results."""
from typing import Any
from flask import Flask, jsonify, render_template_string

from .db import Database


# HTML template for dashboard
HTML_TEMPLATE = '''<!doctype html>
<html>
<head>
    <title>StockMarket Robot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr:hover { background-color: #e0e0e0; }
        .buy { color: green; font-weight: bold; }
        .sell { color: red; font-weight: bold; }
        .hold { color: orange; font-weight: bold; }
    </style>
</head>
<body>
    <h1>StockMarket Robot</h1>
    <p>Latest stock analyses and trading signals</p>
    <table>
        <tr>
            <th>Ticker</th>
            <th>Price</th>
            <th>Fair Value</th>
            <th>Upside</th>
            <th>Score</th>
            <th>Signal</th>
        </tr>
        {% for analysis in analyses %}
        <tr>
            <td>{{ analysis.ticker }}</td>
            <td>${{ "%.2f"|format(analysis.price) }}</td>
            <td>
                {% if analysis.fair_value %}
                    ${{ "%.2f"|format(analysis.fair_value) }}
                {% else %}
                    N/A
                {% endif %}
            </td>
            <td>
                {% if analysis.upside is not none %}
                    {{ "%.1f%%"|format(analysis.upside * 100) }}
                {% else %}
                    N/A
                {% endif %}
            </td>
            <td>{{ "%.1f"|format(analysis.master_score) }}</td>
            <td class="{% if analysis.signal == 'BUY' %}buy{% elif analysis.signal == 'SELL' %}sell{% else %}hold{% endif %}">
                {{ analysis.signal }}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
'''


def create_app(db_path: str) -> Flask:
    """Create Flask app with database connection.
    
    Args:
        db_path: Path to SQLite database file.
        
    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)
    db = Database(db_path)
    
    @app.get('/')
    def home() -> str:
        """Render main dashboard page.
        
        Returns:
            Rendered HTML template with latest analyses.
        """
        analyses = db.latest_analyses()
        return render_template_string(HTML_TEMPLATE, analyses=analyses)
    
    @app.get('/api/analyses')
    def analyses() -> Any:
        """Return latest analyses as JSON.
        
        Returns:
            JSON array of analysis results.
        """
        return jsonify(db.latest_analyses())
    
    return app
