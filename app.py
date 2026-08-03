from flask import Flask
from models import db, User
from routes import configure_routes
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

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
    db.create_all()
    
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
    app.run(debug=True)
