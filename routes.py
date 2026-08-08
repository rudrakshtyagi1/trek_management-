from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from models import User, Trek, Booking
from datetime import datetime


def configure_routes(app, db):

    # ========== HOME ==========
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

    # ========== LOGIN ==========
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
                    flash('Your account has been blacklisted. Contact admin.', 'danger')
                    return redirect(url_for('login'))
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
        return render_template('login.html')

    # ========== REGISTER ==========
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            password = generate_password_hash(request.form.get('password'))
            name     = request.form.get('name')
            role     = request.form.get('role')
            contact  = request.form.get('contact')
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash('Username already taken. Please choose another.', 'danger')
                return redirect(url_for('register'))
            status = 'pending' if role == 'staff' else 'approved'
            new_user = User(username=username, password_hash=password,
                            name=name, role=role, contact=contact, status=status)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    # ========== LOGOUT ==========
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    # ========== PROFILE (view + edit) ==========
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            new_name     = request.form.get('name', '').strip()
            new_contact  = request.form.get('contact', '').strip()
            new_email    = request.form.get('email', '').strip()
            new_password = request.form.get('password', '').strip()
            confirm_pw   = request.form.get('confirm_password', '').strip()

            if new_name:
                current_user.name = new_name
            if new_contact:
                current_user.contact = new_contact
            if new_email:
                current_user.email = new_email
            if new_password:
                if new_password != confirm_pw:
                    flash('Passwords do not match.', 'danger')
                    return redirect(url_for('profile'))
                current_user.password_hash = generate_password_hash(new_password)

            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('profile'))

        return render_template('profile.html')

    # ==========================================
    #              ADMIN ROUTES
    # ==========================================

    # ========== ADMIN: DASHBOARD ==========
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            return redirect(url_for('index'))

        trek_search  = request.args.get('trek_search',  '').strip()
        user_search  = request.args.get('user_search',  '').strip()
        staff_search = request.args.get('staff_search', '').strip()

        # --- Primary stats ---
        total_treks     = Trek.query.count()
        total_users     = User.query.filter_by(role='user').count()
        total_staff     = User.query.filter_by(role='staff').count()
        total_bookings  = Booking.query.count()
        pending_count   = User.query.filter_by(role='staff', status='pending').count()

        # --- Analytics stats ---
        completed_treks   = Trek.query.filter_by(status='Completed').count()
        cancelled_treks   = Trek.query.filter_by(status='Cancelled').count()
        cancelled_bookings = Booking.query.filter_by(status='Cancelled').count()

        # --- Trek list with optional search ---
        if trek_search:
            all_treks = Trek.query.filter(Trek.name.contains(trek_search)).all()
        else:
            all_treks = Trek.query.all()

        pending_staff = User.query.filter_by(role='staff', status='pending').all()

        # --- Trekkers with optional search ---
        if user_search:
            all_users = User.query.filter(
                User.role == 'user',
                or_(User.name.contains(user_search), User.username.contains(user_search))
            ).all()
        else:
            all_users = User.query.filter_by(role='user').all()

        # --- Staff with optional search ---
        if staff_search:
            all_staff = User.query.filter(
                User.role == 'staff',
                or_(User.name.contains(staff_search), User.username.contains(staff_search))
            ).all()
        else:
            all_staff = User.query.filter_by(role='staff').all()

        # Map staff_id -> trek_name for "Assigned Trek" column
        staff_trek_map = {}
        for trek in Trek.query.all():
            if trek.assigned_staff_id:
                staff_trek_map[trek.assigned_staff_id] = trek.name

        return render_template('admin_dashboard.html',
                               total_treks=total_treks,
                               total_users=total_users,
                               total_staff=total_staff,
                               total_bookings=total_bookings,
                               pending_count=pending_count,
                               completed_treks=completed_treks,
                               cancelled_treks=cancelled_treks,
                               cancelled_bookings=cancelled_bookings,
                               pending_staff=pending_staff,
                               all_treks=all_treks,
                               all_users=all_users,
                               all_staff=all_staff,
                               staff_trek_map=staff_trek_map,
                               trek_search=trek_search,
                               user_search=user_search,
                               staff_search=staff_search)

    # ========== ADMIN: APPROVE STAFF ==========
    @app.route('/admin/staff/approve/<int:user_id>')
    @login_required
    def approve_staff(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        user = User.query.get(user_id)
        if user and user.role == 'staff':
            user.status = 'approved'
            db.session.commit()
            flash(f'{user.name} has been approved.', 'success')
        return redirect(url_for('admin_dashboard'))

    # ========== ADMIN: BLACKLIST ==========
    @app.route('/admin/users/blacklist/<int:user_id>')
    @login_required
    def blacklist_user(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        user = User.query.get(user_id)
        if user and user.role != 'admin':
            user.status = 'blacklisted'
            db.session.commit()
            flash(f'{user.name} has been blacklisted.', 'warning')
        return redirect(url_for('admin_dashboard'))

    # ========== ADMIN: RESTORE ==========
    @app.route('/admin/users/restore/<int:user_id>')
    @login_required
    def unblacklist_user(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        user = User.query.get(user_id)
        if user and user.role != 'admin':
            user.status = 'approved'
            db.session.commit()
            flash(f'{user.name} has been restored.', 'success')
        return redirect(url_for('admin_dashboard'))

    # ========== ADMIN: CREATE TREK ==========
    @app.route('/admin/treks/create', methods=['GET', 'POST'])
    @login_required
    def create_trek():
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        if request.method == 'POST':
            name     = request.form.get('name')
            location = request.form.get('location')
            diff     = request.form.get('difficulty')
            duration = int(request.form.get('duration'))
            cost     = float(request.form.get('cost', 0.0))
            slots    = int(request.form.get('available_slots'))
            start    = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end      = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            new_trek = Trek(name=name, location=location, difficulty=diff,
                            duration=duration, cost=cost, available_slots=slots,
                            start_date=start, end_date=end, status='Open')
            db.session.add(new_trek)
            db.session.commit()
            flash('Trek created successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        return render_template('create_trek.html')

    # ========== ADMIN: EDIT TREK (edit details + assign staff) ==========
    @app.route('/admin/treks/edit/<int:trek_id>', methods=['GET', 'POST'])
    @login_required
    def edit_trek(trek_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        trek = Trek.query.get(trek_id)
        if not trek:
            flash('Trek not found.', 'danger')
            return redirect(url_for('admin_dashboard'))
        available_staff = User.query.filter_by(role='staff', status='approved').all()
        if request.method == 'POST':
            trek.name            = request.form.get('name')
            trek.location        = request.form.get('location')
            trek.difficulty      = request.form.get('difficulty')
            trek.duration        = int(request.form.get('duration'))
            trek.cost            = float(request.form.get('cost', 0.0))
            trek.available_slots = int(request.form.get('available_slots'))
            trek.start_date      = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            trek.end_date        = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            trek.status          = request.form.get('status')
            staff_id             = request.form.get('staff_id')
            trek.assigned_staff_id = int(staff_id) if staff_id else None
            db.session.commit()
            flash('Trek updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        return render_template('edit_trek.html', trek=trek, available_staff=available_staff)

    # ========== ADMIN: ASSIGN STAFF (redirect to edit_trek) ==========
    @app.route('/admin/treks/assign/<int:trek_id>', methods=['GET', 'POST'])
    @login_required
    def assign_staff(trek_id):
        return redirect(url_for('edit_trek', trek_id=trek_id))

    # ========== ADMIN: ALL BOOKINGS PAGE ==========
    @app.route('/admin/bookings')
    @login_required
    def admin_bookings():
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        search        = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()

        all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()

        # Filter by search text (booking ID, user name, trek name)
        if search:
            sl = search.lower()
            all_bookings = [
                b for b in all_bookings
                if sl in b.trekker.name.lower()
                or sl in b.trek.name.lower()
                or sl in ("bk-%04d" % b.id)
            ]
        # Filter by booking status
        if status_filter:
            all_bookings = [b for b in all_bookings if b.status == status_filter]

        return render_template('admin_bookings.html',
                               all_bookings=all_bookings,
                               search=search,
                               status_filter=status_filter)

    # ========== ADMIN: HISTORICAL TREK DATA PAGE ==========
    @app.route('/admin/history')
    @login_required
    def admin_history():
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        search        = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()

        treks = Trek.query.order_by(Trek.id.desc()).all()

        if search:
            sl = search.lower()
            treks = [t for t in treks if sl in t.name.lower() or sl in t.location.lower()]
        if status_filter:
            treks = [t for t in treks if t.status == status_filter]

        return render_template('admin_history.html',
                               treks=treks,
                               search=search,
                               status_filter=status_filter)

    # ==========================================
    #              STAFF ROUTES
    # ==========================================

    # ========== STAFF: DASHBOARD ==========
    @app.route('/staff/dashboard')
    @login_required
    def staff_dashboard():
        if current_user.role != 'staff':
            return redirect(url_for('index'))

        assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()

        # Summary stats for the stat cards
        assigned_count  = len(assigned_treks)
        participant_count = sum(len(t.bookings) for t in assigned_treks)
        upcoming_count  = sum(1 for t in assigned_treks if t.status in ('Open', 'Started'))
        completed_count = sum(1 for t in assigned_treks if t.status == 'Completed')

        return render_template('staff_dashboard.html',
                               assigned_treks=assigned_treks,
                               assigned_count=assigned_count,
                               participant_count=participant_count,
                               upcoming_count=upcoming_count,
                               completed_count=completed_count)

    # ========== STAFF: UPDATE TREK ==========
    @app.route('/staff/trek/<int:trek_id>/update', methods=['POST'])
    @login_required
    def update_trek(trek_id):
        if current_user.role != 'staff':
            return redirect(url_for('index'))
        trek = Trek.query.get(trek_id)
        # Only the assigned staff member may update
        if trek and trek.assigned_staff_id == current_user.id:
            trek.status          = request.form.get('status')
            trek.available_slots = int(request.form.get('slots'))
            db.session.commit()
            flash('Trek updated successfully.', 'success')
        else:
            flash('Unauthorized. You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff_dashboard'))

    # ========== STAFF: VIEW PARTICIPANTS ==========
    @app.route('/staff/trek/<int:trek_id>/participants')
    @login_required
    def view_participants(trek_id):
        if current_user.role != 'staff':
            return redirect(url_for('index'))

        trek = Trek.query.get(trek_id)

        # Only the assigned staff member may view participants
        if not trek or trek.assigned_staff_id != current_user.id:
            flash('Unauthorized. You are not assigned to this trek.', 'danger')
            return redirect(url_for('staff_dashboard'))

        search   = request.args.get('search', '').strip()
        bookings = Booking.query.filter_by(trek_id=trek_id).all()

        if search:
            sl = search.lower()
            bookings = [
                b for b in bookings
                if sl in b.trekker.name.lower() or sl in b.trekker.username.lower()
            ]

        return render_template('participants.html',
                               trek=trek,
                               bookings=bookings,
                               search=search)

    # ========== STAFF: MARK ATTENDANCE ==========
    @app.route('/staff/booking/<int:booking_id>/attendance/<att_status>')
    @login_required
    def mark_attendance(booking_id, att_status):
        if current_user.role != 'staff':
            return redirect(url_for('index'))

        booking = Booking.query.get(booking_id)
        if not booking:
            flash('Booking not found.', 'danger')
            return redirect(url_for('staff_dashboard'))

        trek = Trek.query.get(booking.trek_id)
        # Only the assigned staff member may mark attendance
        if not trek or trek.assigned_staff_id != current_user.id:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('staff_dashboard'))

        if att_status in ('Present', 'Absent', 'Not Marked'):
            booking.attendance = att_status
            db.session.commit()
            flash(f'Attendance marked as {att_status}.', 'success')

        return redirect(url_for('view_participants', trek_id=booking.trek_id))

    # ==========================================
    #              USER ROUTES
    # ==========================================

    # ========== USER: DASHBOARD ==========
    @app.route('/user/dashboard')
    @login_required
    def user_dashboard():
        if current_user.role != 'user':
            return redirect(url_for('index'))

        search_query = request.args.get('search', '').strip()
        active_tab   = request.args.get('tab', 'available')

        if search_query:
            open_treks = Trek.query.filter(
                Trek.status == 'Open',
                Trek.name.contains(search_query)
            ).all()
        else:
            open_treks = Trek.query.filter_by(status='Open').all()

        user_bookings = Booking.query.filter_by(user_id=current_user.id).all()

        # Set of trek IDs the user has already booked (non-cancelled)
        # Used to disable the "Book Now" button for already-booked treks
        booked_trek_ids = {
            b.trek_id for b in user_bookings if b.status != 'Cancelled'
        }

        return render_template('user_dashboard.html',
                               open_treks=open_treks,
                               user_bookings=user_bookings,
                               active_tab=active_tab,
                               search_query=search_query,
                               booked_trek_ids=booked_trek_ids)

    # ========== USER: BOOK TREK ==========
    @app.route('/user/book/<int:trek_id>')
    @login_required
    def book_trek(trek_id):
        if current_user.role != 'user':
            return redirect(url_for('index'))

        trek = Trek.query.get(trek_id)

        # Guard: trek must be Open and have slots
        if not trek or trek.status != 'Open':
            flash('This trek is not open for booking.', 'danger')
            return redirect(url_for('user_dashboard'))

        if trek.available_slots <= 0:
            flash('This trek is full. No slots available.', 'danger')
            return redirect(url_for('user_dashboard'))

        # Guard: no duplicate bookings
        existing = Booking.query.filter_by(
            user_id=current_user.id, trek_id=trek_id).filter(
            Booking.status != 'Cancelled').first()
        if existing:
            flash('You have already booked this trek.', 'info')
            return redirect(url_for('user_dashboard'))

        new_booking = Booking(user_id=current_user.id, trek_id=trek_id)
        trek.available_slots -= 1
        if trek.available_slots == 0:
            trek.status = 'Closed'
        db.session.add(new_booking)
        db.session.commit()
        flash('Trek booked successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    # ========== USER: CANCEL BOOKING ==========
    @app.route('/user/booking/cancel/<int:booking_id>')
    @login_required
    def cancel_booking(booking_id):
        if current_user.role != 'user':
            return redirect(url_for('index'))

        booking = Booking.query.get(booking_id)
        if booking and booking.user_id == current_user.id and booking.status == 'Booked':
            trek = Trek.query.get(booking.trek_id)
            if trek:
                trek.available_slots += 1
                if trek.status == 'Closed' and trek.available_slots > 0:
                    trek.status = 'Open'
            booking.status = 'Cancelled'
            db.session.commit()
            flash('Booking cancelled successfully.', 'success')
        else:
            flash('Unable to cancel this booking.', 'danger')
        return redirect(url_for('user_dashboard', tab='bookings'))
