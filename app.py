from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
import secrets
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Konfigurasi Database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jurusan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100),unique=True, nullable=False)
    nip = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    
class Information(db.Model):
    __tablename__ = 'informations'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    
class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    total_student = db.Column(db.Integer, nullable=False, default=0)
    id_batch = db.Column(db.Integer, db.ForeignKey('batch.id'))
    batch = db.relationship('Batch', backref='classes')

class Batch(db.Model):
    __tablename__ = 'batch'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_year = db.Column(db.Integer, nullable=False) 
    
class labRoom(db.Model):
    __tablename__ = 'lab_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    goods = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    profile = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)

def init_db():
    db.create_all()

@app.route('/')
def index():
    informations = Information.query.order_by(Information.id.desc()).limit(1).all()
    activities = Activity.query.order_by(Activity.id.desc()).limit(3).all()
    teachers = Teacher.query.all()
    batches = Batch.query.order_by(Batch.id.desc()).limit(3).all()
    return render_template('index.html', activities=activities, informations=informations,teachers=teachers,batches=batches)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nip = request.form.get('nip')
        password = request.form.get('password')

        errors = {}

        # Validasi NIP
        if not nip or not nip.isdigit() or len(nip) != 18:
            errors['nip'] = 'NIP harus terdiri dari 18 angka!'

        # Validasi Password
        if not password or len(password) < 8:
            errors['password'] = 'Password harus terdiri dari minimal 8 karakter!'

        if errors:
            for field, message in errors.items():
                flash(message, 'danger')
            return redirect(url_for('login'))

        # Cek NIP
        user = User.query.filter_by(nip=nip).first()
        if not user:
            flash('NIP tidak ditemukan!', 'danger')
            return redirect(url_for('login'))

        # Cek Password
        if user.password != password:
            flash('Password salah!', 'danger')
            return redirect(url_for('login'))

        # Jika validasi berhasil
        session['user'] = user.name
        flash('Login berhasil!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nip = request.form.get('nip')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        errors = {}

        # Validasi NIP
        if not nip or not nip.isdigit() or len(nip) != 18:
            errors['nip'] = 'NIP harus terdiri dari 18 angka!'

        # Validasi Nama
        if not name or len(name) < 3:
            errors['name'] = 'Nama harus terdiri dari minimal 3 karakter!'

        # Validasi Password
        if not password or len(password) < 8:
            errors['password'] = 'Password harus terdiri dari minimal 8 karakter!'

        # Validasi Email
        if not email or "@" not in email:  # Check for valid email
            errors['email'] = 'Email tidak valid!'

        # Cek apakah email sudah terdaftar
        if User.query.filter_by(email=email).first():
            errors['email'] = 'Email sudah terdaftar!'

        # Jika ada error, kirimkan pesan
        if errors:
            for field, message in errors.items():
                flash(message, 'danger')
            return redirect(url_for('register'))

        # Cek apakah NIP sudah terdaftar
        if User.query.filter_by(nip=nip).first():
            flash('NIP sudah terdaftar!', 'danger')
            return redirect(url_for('register'))

        # Simpan data ke database jika validasi lolos
        new_user = User(nip=nip, name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Halaman Forgot Password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    errors = {}

    if request.method == 'POST':
        email = request.form.get('email')

        # Validasi Email
        if not email or "@" not in email:
            errors['email'] = 'Email tidak valid!'
            return render_template('forgot_password.html', errors=errors)

        # Periksa apakah email ada dalam database
        user = User.query.filter_by(email=email).first()
        if not user:
            errors['email'] = 'Email tidak ditemukan dalam sistem kami!'
            return render_template('forgot_password.html', errors=errors)

        # Generate Token
        serializer = URLSafeTimedSerializer(app.secret_key)
        token = serializer.dumps(email, salt='reset-password')
        reset_url = url_for('reset_password', token=token, _external=True)

        # Konfigurasi Email
        sender_email = "muhammadabizar0016@gmail.com"
        receiver_email = email
        password = "cvhd stqx xwbf dxjd"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "Reset Password Request"

        # Body Email
        body = f'Klik tautan ini untuk mereset kata sandi Anda: {reset_url}'
        msg.attach(MIMEText(body, 'plain'))

        try:
            # Kirim Email
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            server.quit()

            flash('Tautan reset kata sandi telah dikirim ke email Anda.', 'success')
        except Exception as e:
            flash(f"Terjadi kesalahan saat mengirim email: {e}", 'danger')

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html', errors=errors)


# Halaman Reset Password
@app.route('/reset-password/<token>', methods=['GET', 'POST'], endpoint='reset_password')
def reset_password(token):
    try:
        # Verifikasi Token
        serializer = URLSafeTimedSerializer(app.secret_key)
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except Exception as e:
        flash('Token tidak valid atau telah kedaluwarsa.', 'danger')
        return redirect(url_for('forgot_password'))

    # Cari User Berdasarkan Email
    user = User.query.filter_by(email=email).first()

    if not user:
        flash('Pengguna dengan email tersebut tidak ditemukan.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')

        # Validasi Password
        if not password or len(password) < 8:
            flash('Password harus terdiri dari minimal 8 karakter!', 'danger')
            return redirect(url_for('reset_password', token=token))  # Pastikan token diteruskan

        # Update Password
        user.password = password
        db.session.commit()

        flash('Kata sandi berhasil direset.', 'success')
        return redirect(url_for('login'))

    # Pastikan token dikirim ke template
    return render_template('reset_password.html', email=email, token=token)




if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
