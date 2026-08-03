from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Trek, Booking
from datetime import datetime

def configure_routes(app, db):

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'staff':
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                if user.status == 'pending':
                    flash('Your account is pending admin approval.', 'warning')
                    return redirect(url_for('login'))
                if user.status == 'blacklisted':
                    flash('Your account has been blacklisted.', 'danger')
                    return redirect(url_for('login'))
                
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials.', 'danger')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            password = generate_password_hash(request.form.get('password'))
            name = request.form.get('name')
            role = request.form.get('role')
            contact = request.form.get('contact')

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists.', 'danger')
                return redirect(url_for('register'))

            status = 'pending' if role == 'staff' else 'approved'
            
            new_user = User(username=username, password_hash=password, name=name, role=role, contact=contact, status=status)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        
        total_treks = Trek.query.count()
        total_users = User.query.filter_by(role='user').count()
        total_staff = User.query.filter_by(role='staff').count()
        total_bookings = Booking.query.count()
        
        pending_staff = User.query.filter_by(role='staff', status='pending').all()
        all_treks = Trek.query.all()
        
        return render_template('admin_dashboard.html', total_treks=total_treks, total_users=total_users, 
                               total_staff=total_staff, total_bookings=total_bookings,
                               pending_staff=pending_staff, all_treks=all_treks)

    @app.route('/admin/staff/approve/<int:user_id>')
    @login_required
    def approve_staff(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        user = User.query.get(user_id)
        if user and user.role == 'staff':
            user.status = 'approved'
            db.session.commit()
            flash('Staff approved.', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/users/blacklist/<int:user_id>')
    @login_required
    def blacklist_user(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        user = User.query.get(user_id)
        if user and user.role != 'admin':
            user.status = 'blacklisted'
            db.session.commit()
            flash('User blacklisted.', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/treks/create', methods=['GET', 'POST'])
    @login_required
    def create_trek():
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            location = request.form.get('location')
            difficulty = request.form.get('difficulty')
            duration = int(request.form.get('duration'))
            slots = int(request.form.get('available_slots'))
            start = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            
            new_trek = Trek(name=name, location=location, difficulty=difficulty, duration=duration,
                            available_slots=slots, start_date=start, end_date=end, status='Open')
            db.session.add(new_trek)
            db.session.commit()
            flash('Trek created successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        return render_template('create_trek.html')

    @app.route('/admin/treks/assign/<int:trek_id>', methods=['GET', 'POST'])
    @login_required
    def assign_staff(trek_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        trek = Trek.query.get(trek_id)
        if request.method == 'POST':
            staff_id = request.form.get('staff_id')
            trek.assigned_staff_id = staff_id
            db.session.commit()
            flash('Staff assigned successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        
        available_staff = User.query.filter_by(role='staff', status='approved').all()
        return render_template('assign_staff.html', trek=trek, available_staff=available_staff)

    @app.route('/staff/dashboard')
    @login_required
    def staff_dashboard():
        if current_user.role != 'staff':
            return redirect(url_for('index'))
        assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()
        return render_template('staff_dashboard.html', assigned_treks=assigned_treks)

    @app.route('/staff/trek/<int:trek_id>/update', methods=['POST'])
    @login_required
    def update_trek(trek_id):
        if current_user.role != 'staff':
            return redirect(url_for('index'))
        trek = Trek.query.get(trek_id)
        if trek and trek.assigned_staff_id == current_user.id:
            trek.status = request.form.get('status')
            trek.available_slots = int(request.form.get('slots'))
            db.session.commit()
            flash('Trek updated.', 'success')
        return redirect(url_for('staff_dashboard'))

    @app.route('/user/dashboard')
    @login_required
    def user_dashboard():
        if current_user.role != 'user':
            return redirect(url_for('index'))
        
        search_query = request.args.get('search')
        if search_query:
            open_treks = Trek.query.filter(Trek.status == 'Open', Trek.name.contains(search_query)).all()
        else:
            open_treks = Trek.query.filter_by(status='Open').all()
            
        user_bookings = Booking.query.filter_by(user_id=current_user.id).all()
        return render_template('user_dashboard.html', open_treks=open_treks, user_bookings=user_bookings)

    @app.route('/user/book/<int:trek_id>')
    @login_required
    def book_trek(trek_id):
        if current_user.role != 'user':
            return redirect(url_for('index'))
            
        trek = Trek.query.get(trek_id)
        if trek and trek.status == 'Open' and trek.available_slots > 0:
            existing_booking = Booking.query.filter_by(user_id=current_user.id, trek_id=trek_id).first()
            if not existing_booking:
                new_booking = Booking(user_id=current_user.id, trek_id=trek_id)
                trek.available_slots -= 1
                if trek.available_slots == 0:
                    trek.status = 'Closed'
                db.session.add(new_booking)
                db.session.commit()
                flash('Trek booked successfully!', 'success')
            else:
                flash('You have already booked this trek.', 'info')
        else:
            flash('Trek is not available for booking.', 'danger')
            
        return redirect(url_for('user_dashboard'))
