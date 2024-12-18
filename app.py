from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
import secrets
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from itsdangerous import URLSafeTimedSerializer
from itertools import chain
from werkzeug.utils import secure_filename

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
    
class Major(db.Model):
    __tablename__ = "majors"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

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
    total_student = db.Column(db.Integer, nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=False)

    # Relationship with Batch
    batch = db.relationship('Batch', back_populates='classes')

class Batch(db.Model):
    __tablename__ = 'batch'

    id = db.Column(db.Integer, primary_key=True)
    batch_year = db.Column(db.String(20), nullable=False)

    # Relationship with Class
    classes = db.relationship('Class', back_populates='batch')
    
class labRoom(db.Model):
    __tablename__ = 'lab_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Goods(db.Model):
    __tablename__ = 'goods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    id_lab_rooms = db.Column(db.Integer, db.ForeignKey('lab_rooms.id'))
    lab_rooms = db.relationship('labRoom', backref='goods')
    
class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    profile = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)

def init_db():
    db.create_all()
    
@app.context_processor
def utility_processor():
    return dict(chain=chain)

@app.template_global()
def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


@app.route('/')
def index():
    majors = Major.query.order_by(Major.id.desc()).first()  # Ambil data terakhir
    informations = Information.query.order_by(Information.id.desc()).limit(1).all()
    activities = Activity.query.order_by(Activity.id.desc()).limit(3).all()
    teachers = Teacher.query.all()
    batches = Batch.query.order_by(Batch.id.desc()).limit(3).all()
    labrooms = labRoom.query.order_by(labRoom.id.desc()).limit(4).all()
    return render_template('index.html', activities=activities, informations=informations, teachers=teachers, batches=batches, labrooms=labrooms, majors=majors)


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

        # Cek NIP di database
        user = User.query.filter_by(nip=nip).first()
        if not user:
            flash('NIP tidak ditemukan!', 'danger')
            return redirect(url_for('login'))

        # Validasi password
        if not check_password_hash(user.password, password):
            flash('Password salah!', 'danger')
            return redirect(url_for('login'))

        # Login berhasil
        session['user'] = user.name  # Simpan data pengguna di session
        flash(f'Selamat datang, {user.name}!', 'success')
        return redirect(url_for('admin'))  # Ganti dengan halaman utama Anda

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # Hapus data session
    flash('Anda telah logout!', 'info')
    return redirect(url_for('login'))

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
        hashed_password = generate_password_hash(password)
        new_user = User(nip=nip, name=name, email=email, password=hashed_password)
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

@app.route('/admin', methods=['GET'])
def admin():
    if 'user' not in session:
        flash('Silakan login terlebih dahulu!', 'warning')
        return redirect(url_for('login'))
        
    major = Major.query.order_by(Major.id.desc()).first()
    return render_template('admin.html', major=major, user=session['user'])


@app.route('/admin/informations', methods=['POST'])
def create_information():
    data = request.form
    image_file = request.files['image_path']
    image_filename = secure_filename(image_file.filename)
    image_file.save('static/assets/img/' + image_filename)
    information = Information(description=data['description'], image_path=image_filename)
    db.session.add(information)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/activities', methods=['POST'])
def create_activity():
    data = request.form
    image_file = request.files['image_path']
    image_filename = secure_filename(image_file.filename)
    image_file.save('static/assets/img/' + image_filename)
    activity = Activity(description=data['description'], image_path=image_filename)
    db.session.add(activity)
    db.session.commit()
    return redirect(url_for('admin'))

UPLOAD_FOLDER = 'static/assets/img/'  # Tentukan lokasi upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Format file yang diperbolehkan

# Helper function untuk memvalidasi file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/teachers', methods=['POST'])
def create_teacher():
    names = request.form.getlist('name[]')
    titles = request.form.getlist('title[]')
    profiles = request.files.getlist('profile[]')

    # Validasi jumlah input
    if not (len(names) == len(titles) == len(profiles)):
        flash('Jumlah data tidak konsisten. Pastikan semua data diisi.', 'danger')
        return redirect(url_for('admin'))

    for name, title, profile in zip(names, titles, profiles):
        if not name or not title:
            flash('Nama dan keterangan tidak boleh kosong.', 'danger')
            continue  # Skip data yang tidak valid

        if profile and allowed_file(profile.filename):
            profile_filename = secure_filename(profile.filename)
            save_path = os.path.join(UPLOAD_FOLDER, profile_filename)
            profile.save(save_path)

            # Simpan ke database
            teacher = Teacher(profile=profile_filename, name=name, title=title)
            db.session.add(teacher)
        else:
            flash(f'File untuk guru "{name}" tidak valid atau tidak diunggah.', 'warning')

    db.session.commit()
    flash('Data guru pembimbing berhasil ditambahkan!', 'success')
    return redirect(url_for('admin'))
@app.route('/admin/major', methods=['POST'])
def major_proses():
    name = request.form['name']
    
    if name:
        # Cek apakah sudah ada data Major
        major = Major.query.first()  # Ambil data pertama jika ada, jika tidak maka None
        
        if major:
            # Jika data Major sudah ada, update data
            major.name = name
        else:
            # Jika belum ada data, create data baru
            major = Major(name=name)
            db.session.add(major)
        
        db.session.commit()  # Simpan perubahan ke database
    return redirect(url_for('admin'))  # Kembali ke halaman admin

@app.route('/admin/lab', methods=['POST'])
def lab_proses():
    # Ambil data lab_name, object_name, dan object_amount dari form
    lab_names = request.form.getlist('lab_name[]')
    
    for idx, lab_name in enumerate(lab_names):
        if lab_name:
            # Buat objek Lab Room baru
            lab_room = labRoom(name=lab_name)
            db.session.add(lab_room)
            db.session.commit()  # Simpan lab_room ke database

            # Ambil data barang berdasarkan indeks lab
            object_names = request.form.getlist(f'object_name_{idx+1}[]')
            object_amounts = request.form.getlist(f'object_amount_{idx+1}[]')

            # Menambahkan barang terkait dengan lab ini
            for i in range(len(object_names)):
                if object_names[i] and object_amounts[i]:
                    object_name = object_names[i]
                    object_amount = object_amounts[i]

                    # Buat objek Goods dan hubungkan dengan lab_room
                    goods = Goods(name=object_name, amount=object_amount, id_lab_rooms=lab_room.id)
                    db.session.add(goods)

            db.session.commit()  # Simpan barang ke database

    return redirect(url_for('admin'))  # Redirect setelah data disimpan


@app.route('/admin/student', methods=['POST'])
def student_proses():
    # Ambil data dari form
    batch_years = request.form.getlist('batch_year[]')  # Tahun angkatan

    for idx, batch_year in enumerate(batch_years):
        if batch_year:
            # Buat objek Batch baru
            batch = Batch(batch_year=batch_year)
            db.session.add(batch)
            db.session.commit()  # Simpan batch ke database

            # Ambil data kelas dan total siswa berdasarkan indeks batch
            class_names = request.form.getlist(f'class_name_{idx+1}[]')
            total_students = request.form.getlist(f'total_student_{idx+1}[]')

            # Menambahkan kelas terkait dengan batch ini
            for i in range(len(class_names)):
                if class_names[i] and total_students[i]:
                    class_name = class_names[i]
                    total_student = total_students[i]

                    # Buat objek Class baru dan hubungkan dengan batch
                    new_class = Class(
                        class_name=class_name,
                        total_student=int(total_student),
                        batch_id=batch.id  # Menghubungkan dengan batch yang benar
                    )
                    db.session.add(new_class)

            db.session.commit()  # Simpan semua kelas ke database

    return redirect(url_for('admin'))  # Redirect setelah data disimpan

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
