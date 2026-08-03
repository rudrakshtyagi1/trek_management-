from flask import Flask
from models import db, User
from routes import configure_routes
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trekking_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

configure_routes(app, db)

with app.app_context():
    # Create all tables that don't exist yet
    db.create_all()

    # --- Safe migrations for new columns (SQLite does not support ALTER TABLE DROP COLUMN,
    #     but ADD COLUMN is safe — it fails silently if the column already exists) ---
    with db.engine.connect() as conn:
        for stmt in [
            "ALTER TABLE user    ADD COLUMN email      VARCHAR(100)",
            "ALTER TABLE booking ADD COLUMN attendance  VARCHAR(20) DEFAULT 'Not Marked'",
        ]:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  # column already exists — that's fine

    # Seed the default admin account if one doesn't exist yet
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        hashed_password = generate_password_hash('admin123')
        new_admin = User(
            username='admin',
            password_hash=hashed_password,
            role='admin',
            name='System Admin',
            status='approved'
        )
        db.session.add(new_admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
