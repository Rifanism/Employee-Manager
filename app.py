from flask import Flask, render_template, request, redirect, url_for, session
from MySQLdb.cursors import DictCursor
from config import init_mysql as sql

app = Flask(__name__)
app.secret_key = 'whtvr'
mysql = sql(app)

PUBLIC_ROUTES = [
    'welcome', 'login', 'logout', 'static'
]

USER_ROUTES = [
    'user', 'schedule', 'presenceIn', 'presenceOut'
]


@app.before_request
def protect_all_routes():
    endpoint = request.endpoint

    if endpoint is None:
        return redirect('/')

    if endpoint in PUBLIC_ROUTES:
        return
    
    if request.path == "/login" and request.method == "POST":
        return

    if not session.get('logged'):
        return redirect('/')

    role = session.get('role')

    if role == 'admin':
        return

    if role == 'employee':
        if endpoint not in USER_ROUTES:
            return redirect('/user/dashboard')
    return

#======================================SEBEULM LOGIN
@app.route('/')
def welcome():
    return render_template('landing_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(DictCursor)
        query = 'SELECT p.*, a.role FROM pegawai p JOIN account a ON p.id = a.id WHERE p.nama = %s AND p.id = %s'
        value = (username, password)
        cursor.execute(query, value)
        user = cursor.fetchone()
        mysql.connection.close()
        if user:
            session['logged'] = True
            session['username'] = user['nama']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect('/admin/dashboard')
            elif user['role'] == 'employee':
                return redirect('/user/dashboard')
        elif not user:
            return render_template('login.html', error='Username atau Password salah!')

@app.route('/admin/dashboard')
def admin():
    cursor = mysql.connection.cursor(DictCursor)
    query = '''
            SELECT p.id ID, p.nama Nama, m.waktu_masuk Waktu, CONCAT('Masuk ', m.status) 'Status', m.tanggal 'Tanggal'
            FROM presensi_masuk m
            JOIN pegawai p ON m.id_pegawai = p.id AND m.tanggal = CURRENT_DATE
            UNION
            SELECT p.id ID, p.nama Nama, m.waktu_keluar Waktu, CONCAT('Pulang ', m.status) 'Status', m.tanggal 'Tanggal'
            FROM presensi_keluar m
            JOIN pegawai p ON m.id_pegawai = p.id AND m.tanggal = CURRENT_DATE;
    '''
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('admin_dashboard.html', pegawai=data)

@app.route('/user/dashboard')
def user():
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('''  SELECT p.id, p.nama, d.nama_divisi
                        FROM pegawai p
                        JOIN divisi d ON p.id_divisi = d.id
                        WHERE p.id BETWEEN 1001 AND (
                            SELECT id FROM pegawai
                            ORDER BY id DESC LIMIT 1)
                        ORDER BY p.id''')
    data = cursor.fetchall()
    cursor.close()
    return render_template('user_dashboard.html', pegawai=data)

@app.route('/logout')
def logout():
    session.clear()
    session.modified = True
    return redirect('/')

@app.route('/back')
def go_back():
    if session.get('role') == 'admin':
        return redirect('/admin/dashboard')
    return redirect('/user/dashboard')


@app.route('/pegawai')
def pegawai():
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('''  SELECT p.id, p.nama, d.nama_divisi
                        FROM pegawai p
                        JOIN divisi d ON p.id_divisi = d.id ORDER BY p.id''')
    data = cursor.fetchall()
    cursor.close()
    return render_template('pegawai.html', pegawai=data)

@app.route('/pegawai/<int:id>')
def detail(id):
    cursor = mysql.connection.cursor(DictCursor)
    query = '''
        SELECT p.id, p.nama, p.jabatan, format_gaji(p.gaji) gaji, d.nama_divisi, IFNULL(COUNT(m.id_pegawai), 0) 'Total',
        CASE p.id
            WHEN 1001 THEN 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWukf_3eIysNb3te75amKqP4IEqZgPYzThMQ&s'
            WHEN 1003 THEN 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRsM9xXuI5VIsDEIH1-Z1ArXLVHHpBxGkc_fA&s'
            WHEN 1004 THEN 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTFwlPaUZrPp39rUs05zqJTC51aVCzQ-igpRK6JLYGa1LQ-cvR-pnqttxRFFiWpZzufCK8&usqp=CAU'
            ELSE 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
        END AS icon
        FROM pegawai p
        JOIN divisi d ON p.id_divisi = d.id
        LEFT JOIN presensi_masuk m ON p.id = m.id_pegawai
        WHERE p.id = %s
    '''
    cursor.execute(query, (id,))
    pegawai = cursor.fetchone()
    cursor.close()
    return render_template('detail.html', pegawai=pegawai)

@app.route('/pegawai/tambah-pegawai', methods=['GET', 'POST'])
def tambahPegawai():
    if request.method == 'POST':
        nama = request.form['nama']
        jabatan = request.form['Posisi']
        match request.form['Divisi']:
            case 'Manajemen Puncak':
                id_divisi = 1
            case 'Keamanan':
                id_divisi = 2
            case 'Kebersihan':
                id_divisi = 3
            case 'Penataan Barang':
                id_divisi = 4
            case 'Gudang & Logistik':
                id_divisi = 5
            case 'Kasir':
                id_divisi = 6
        gaji = request.form['gaji']
        cursor = mysql.connection.cursor()
        query = 'CALL addPegawai(%s, %s, %s, %s)'
        data = (nama, jabatan, id_divisi, gaji)
        cursor.execute(query, data)
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('pegawai'))
    return render_template('tambah.html')

@app.route('/delete/<id>')
def delete(id):
    cursor = mysql.connection.cursor()
    cursor.execute('CALL deletePegawai(%s)', (id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('pegawai'))

@app.route('/update/<id>', methods=['GET', 'POST'])
def update(id):
    cursor = mysql.connection.cursor(DictCursor)
    if request.method == 'POST':
        gaji = request.form['gaji']
        cursor.execute('UPDATE pegawai SET gaji = %s WHERE id = %s', (gaji, id))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('detail', id=id))
    cursor.execute('SELECT p.id, p.nama FROM pegawai p WHERE p.id = %s', (id,))
    data = cursor.fetchone()
    cursor.close()
    return render_template('update.html', pegawai=data)

@app.route('/history-presensi')
def history():
    cursor = mysql.connection.cursor(DictCursor)
    query = '''
            SELECT p.id ID, p.nama Nama, m.waktu_masuk Waktu, CONCAT('Masuk ', m.status) 'Status', m.tanggal 'Tanggal'
            FROM presensi_masuk m
            JOIN pegawai p ON m.id_pegawai = p.id AND m.tanggal = CURRENT_DATE
            UNION
            SELECT p.id ID, p.nama Nama, m.waktu_keluar Waktu, CONCAT('Pulang ', m.status) 'Status', m.tanggal 'Tanggal'
            FROM presensi_keluar m
            JOIN pegawai p ON m.id_pegawai = p.id AND m.tanggal = CURRENT_DATE;
    '''
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('history.html', pegawai=data)

@app.route('/jadwal-kerja', methods=['GET', 'POST'])
def schedule():
    if request.method == 'POST':
        hari = request.form['Hari']
    else:
        hari = 'Senin'
    cursor = mysql.connection.cursor(DictCursor)
    query = '''
            SELECT p.id, p.nama, s.kategori, s.jam_kerja, s.jam_selesai, j.hari
            FROM jadwal_kerja j
            JOIN pegawai p ON j.id_pegawai = p.id
            JOIN shift s ON j.id_shift = s.id
            WHERE j.hari = %s
            ORDER BY j.hari ASC, s.jam_kerja ASC
            '''
    cursor.execute(query, (hari,))
    data = cursor.fetchall()
    cursor.close()
    return render_template('jadwal.html', pegawai=data, hari=hari)

@app.route('/presensi-masuk', methods=['GET', 'POST'])
def presenceIn():
    cursor = mysql.connection.cursor(DictCursor)
    if request.method == 'POST':
        id_pegawai = request.form['id_pegawai']
        cursor.execute('CALL masuk(%s)', (id_pegawai,))
        mysql.connection.commit()
        cursor.close()
        if session['role'] == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('user'))
    return render_template('presensi_masuk.html')

@app.route('/presensi-pulang', methods = ['GET', 'POST'])
def presenceOut():
    cursor = mysql.connection.cursor(DictCursor)
    if request.method == 'POST':
        id_pegawai = request.form['id_pegawai']
        cursor.execute('CALL keluar(%s)', (id_pegawai,))
        mysql.connection.commit()
        cursor.close()
        if session['role'] == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('user'))
    return render_template('presensi_keluar.html')

if __name__ == '__main__':
    app.run(debug=True)