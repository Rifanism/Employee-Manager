from flask import Flask, render_template, request, redirect, url_for
from MySQLdb.cursors import DictCursor
from config import init_mysql as sql

app = Flask(__name__)
mysql = sql(app)

@app.route('/')
def index():
    return render_template('index.html')

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
        SELECT p.id, p.nama, p.jabatan, FORMAT(p.gaji, 2, 'id_ID') gaji, d.nama_divisi,
        CASE p.id
            WHEN 1001 THEN 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWukf_3eIysNb3te75amKqP4IEqZgPYzThMQ&s'
            WHEN 1003 THEN 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRsM9xXuI5VIsDEIH1-Z1ArXLVHHpBxGkc_fA&s'
            WHEN 1004 THEN 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTFwlPaUZrPp39rUs05zqJTC51aVCzQ-igpRK6JLYGa1LQ-cvR-pnqttxRFFiWpZzufCK8&usqp=CAU'
            ELSE 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'
        END AS icon
        FROM pegawai p
        JOIN divisi d ON p.id_divisi = d.id
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

if __name__ == '__main__':
    app.run(debug=True)