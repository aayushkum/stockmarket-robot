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

    @app.get('/portfolio')
    def portfolio() -> str:
        """Render current paper cash, positions, and unrealized P&L."""
        from .config import Settings

        state = db.load_portfolio(Settings(db_path=db_path))
        analyses = {item["ticker"]: item for item in db.latest_analyses()}
        rows = []
        for ticker, position in state.positions.items():
            price = analyses.get(ticker, {}).get("price", position.avg_cost)
            rows.append({
                "ticker": ticker,
                "shares": position.shares,
                "avg_cost": position.avg_cost,
                "price": price,
                "pnl": (price - position.avg_cost) * position.shares,
            })
        return render_template_string(
            """<!doctype html><title>Paper Portfolio</title>
            <h1>Paper Portfolio</h1><p>Cash: ${{ '%.2f'|format(cash) }}</p>
            <table><tr><th>Ticker</th><th>Shares</th><th>Average cost</th>
            <th>Price</th><th>Unrealized P&amp;L</th></tr>
            {% for row in rows %}<tr><td>{{ row.ticker }}</td>
            <td>{{ '%.4f'|format(row.shares) }}</td>
            <td>${{ '%.2f'|format(row.avg_cost) }}</td>
            <td>${{ '%.2f'|format(row.price) }}</td>
            <td>${{ '%.2f'|format(row.pnl) }}</td></tr>{% endfor %}</table>""",
            cash=state.cash, rows=rows,
        )
    
    return app
