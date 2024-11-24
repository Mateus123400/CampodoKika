from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import qrcode
import os
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')

# Configuração do banco de dados
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Corrige a URL do PostgreSQL para o formato correto
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info(f"Usando banco de dados PostgreSQL: {database_url.split('@')[1]}")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kikacampo.db'
    logger.info("Usando banco de dados SQLite local")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa as extensões
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuração do Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)

# Criar todas as tabelas do banco de dados
with app.app_context():
    try:
        db.create_all()
        logger.info("Tabelas do banco de dados criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")

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
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            
            # Validação dos campos
            if not all([name, email, phone, password]):
                flash('Todos os campos são obrigatórios', 'error')
                return render_template('register.html')
            
            # Verifica se o email já existe
            if User.query.filter_by(email=email).first():
                flash('Email já cadastrado', 'error')
                return render_template('register.html')
            
            # Cria o novo usuário
            try:
                new_user = User(
                    name=name,
                    email=email,
                    phone=phone,
                    password=generate_password_hash(password, method='sha256')
                )
                db.session.add(new_user)
                db.session.commit()
                logger.info(f"Novo usuário registrado: {email}")
                
                # Faz login automático após o registro
                login_user(new_user)
                flash('Registro realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erro ao salvar usuário no banco: {str(e)}")
                flash('Erro ao criar usuário. Por favor, tente novamente.', 'error')
                return render_template('register.html')
        
        return render_template('register.html')
    
    except Exception as e:
        logger.error(f"Erro na rota de registro: {str(e)}")
        flash('Ocorreu um erro. Por favor, tente novamente.', 'error')
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

@app.route('/test-db')
def test_db():
    try:
        # Tenta criar as tabelas
        with app.app_context():
            db.create_all()
        
        # Tenta fazer uma consulta simples
        test_user = User.query.first()
        
        return jsonify({
            'status': 'success',
            'message': 'Conexão com o banco de dados está funcionando!',
            'database_url': app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'sqlite',
            'test_user': test_user.name if test_user else 'Nenhum usuário encontrado'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Erro ao conectar com o banco de dados',
            'error': str(e)
        }), 500

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
    port = int(os.environ.get('PORT', 5000))
    if os.environ.get('RAILWAY_STATIC_URL'):
        app.run(host='0.0.0.0', port=port)
    else:
        socketio.run(app, debug=False, host='0.0.0.0', port=port)
