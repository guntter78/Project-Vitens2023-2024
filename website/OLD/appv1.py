from flask import Flask, render_template
import psycopg2
from decimal import Decimal
from datetime import datetime

app = Flask(__name__)

def create_connection():
    try:
        # Verbinding maken met de PostgreSQL-database 'vitenswatersystem'
        conn = psycopg2.connect(
            host="localhost",
            database="vitenswatersystem",
            user='vitens',
            password='project')
        return conn
    except Exception as e:
        print(f"Fout bij het verbinden met de database: {str(e)}")
        return None

def fetch_data():
    conn = create_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Voorbeeldquery om gegevens op te halen uit de 'flowsensor'-tabel
            cur.execute("SELECT * FROM flows")
            data = cur.fetchall()
            return data
        except Exception as e:
            print(f"Fout bij het ophalen van gegevens: {str(e)}")
        finally:
            cur.close()
            conn.close()
    return None

def sensor():
    conn = create_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM sensor")
            data = cur.fetchall()
            print(data)
            return data
        except Exception as e:
            print(f"Fout bij het ophalen van gegevens: {str(e)}")
        finally:
            cur.close()
            conn.close()
    return None

def mal_func():
    conn = create_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM malfunction")
            data = cur.fetchall()
            print(data)
            return data
        except Exception as e:
            print(f"Fout bij het ophalen van gegevens: {str(e)}")
        finally:
            cur.close()
            conn.close()
    return None


@app.route('/')
def index():
    sensor_data = fetch_data()
    # Convert Decimal and datetime objects to native Python types for better rendering in the template
    formatted_data = [
        {'id': row[0], 'sensor_id': row[1], 'mal_code': row[2], 'flowrate': float(row[3]),
         'cons_amount': float(row[4]), 'timestamp': row[5].strftime('%Y-%m-%d %H:%M:%S')}
        for row in sensor_data
    ]
    return render_template('index.html', sensor_data=formatted_data)

@app.route('/malfunction')
def mal():
    data=sensor()
    data2 = mal_func()
    return render_template('mal.html',data=data, data2=data2)


if __name__ == '__main__':
    app.run(debug=True)
