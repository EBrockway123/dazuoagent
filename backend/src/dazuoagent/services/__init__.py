"""Business-logic layer.

Routes call into services; services own transactions and orchestrate
ORM ↔ schema conversion. Keep routers thin.
"""