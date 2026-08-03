from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from models import db, User, Trek, Booking

def init_routes(app):
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user)
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'staff':
                    return redirect(url_for('staff_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            flash('Invalid email or password', 'danger')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'user') # Allow selection for demo purposes.
            
            if User.query.filter_by(email=email).first():
                flash('Email address already exists', 'warning')
                return redirect(url_for('register'))
            
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/admin_dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            flash('Unauthorized access!', 'danger')
            return redirect(url_for('index'))
        users = User.query.all()
        treks = Trek.query.all()
        bookings = Booking.query.all()
        return render_template('admin_dashboard.html', users=users, treks=treks, bookings=bookings)

    @app.route('/staff_dashboard')
    @login_required
    def staff_dashboard():
        if current_user.role not in ['staff', 'admin']:
            flash('Unauthorized access!', 'danger')
            return redirect(url_for('index'))
        treks = Trek.query.all()
        bookings = Booking.query.all()
        return render_template('staff_dashboard.html', treks=treks, bookings=bookings)

    @app.route('/user_dashboard')
    @login_required
    def user_dashboard():
        treks = Trek.query.all()
        bookings = Booking.query.filter_by(user_id=current_user.id).all()
        return render_template('user_dashboard.html', treks=treks, bookings=bookings)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
