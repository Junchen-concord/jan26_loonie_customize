from flask import Flask

from api.income_analysis.routes import income_analysis_blueprint
from api.label.routes import label_blueprint
from api.transactions.routes import transactions_blueprint


def register_blueprints(app: Flask):
    """
    Registers all blueprints to the Flask app.

    Args:
        app (Flask): The Flask application instance.
    """
    app.register_blueprint(label_blueprint)
    app.register_blueprint(income_analysis_blueprint)
    app.register_blueprint(transactions_blueprint)
