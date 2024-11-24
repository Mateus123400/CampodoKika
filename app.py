from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import qrcode
import os
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kikacampo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin_message = db.Column(db.Boolean, default=False)

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, phone=phone, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin_code = request.form.get('admin_code')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            if admin_code:
                if admin_code == 'kika01' and user.is_admin:
                    login_user(user)
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Código de administrador inválido')
            else:
                login_user(user)
                return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha inválidos')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    time_slots = TimeSlot.query.all()
    return render_template('dashboard.html', bookings=bookings, time_slots=time_slots)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    # Get all bookings with user information
    bookings = db.session.query(Booking, User).join(User).all()
    
    # Get all messages grouped by user
    messages = db.session.query(Message, User).join(User).order_by(Message.timestamp.desc()).all()
    
    # Get time slots
    time_slots = TimeSlot.query.all()
    
    return render_template('admin_dashboard.html', 
                         bookings=bookings, 
                         messages=messages, 
                         time_slots=time_slots)

@app.route('/admin/manage_slots', methods=['POST'])
@login_required
def manage_slots():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    action = request.form.get('action')
    slot_id = request.form.get('slot_id')
    
    slot = TimeSlot.query.get_or_404(slot_id)
    
    if action == 'toggle':
        slot.is_available = not slot.is_available
        db.session.commit()
        return jsonify({'status': 'success', 'is_available': slot.is_available})
    
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/admin/update_booking', methods=['POST'])
@login_required
def update_booking():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking_id = request.form.get('booking_id')
    status = request.form.get('status')
    
    booking = Booking.query.get_or_404(booking_id)
    booking.payment_status = status
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/admin/reply_message', methods=['POST'])
@login_required
def reply_message():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user_id = request.form.get('user_id')
    content = request.form.get('content')
    
    message = Message(
        user_id=user_id,
        content=content,
        is_admin_message=True
    )
    db.session.add(message)
    db.session.commit()
    
    # Emit the message through Socket.IO
    socketio.emit('new_message', {
        'user': 'Admin',
        'message': content,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }, room=user_id)
    
    return jsonify({'status': 'success'})

@app.route('/admin/user_details/<int:user_id>')
@login_required
def user_details(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).all()
    messages = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp.desc()).all()
    
    return render_template('user_details.html', 
                         user=user, 
                         bookings=bookings, 
                         messages=messages)

@app.route('/book', methods=['POST'])
@login_required
def book():
    date = request.form.get('date')
    time_slot = request.form.get('time_slot')
    payment_method = request.form.get('payment_method')
    
    booking = Booking(
        user_id=current_user.id,
        date=datetime.strptime(date, '%Y-%m-%d').date(),
        time_slot=time_slot,
        payment_method=payment_method
    )
    
    db.session.add(booking)
    db.session.commit()
    
    if payment_method == 'pix':
        # Generate PIX QR Code logic here
        pass
    
    return redirect(url_for('dashboard'))

@app.route('/messages')
@login_required
def messages():
    messages = Message.query.filter_by(user_id=current_user.id).all()
    return render_template('messages.html', messages=messages)

@socketio.on('send_message')
def handle_message(data):
    message = Message(
        user_id=current_user.id,
        content=data['message'],
        is_admin_message=current_user.is_admin
    )
    db.session.add(message)
    db.session.commit()
    emit('new_message', {
        'user': current_user.name,
        'message': data['message'],
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }, broadcast=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=False, host='0.0.0.0')
