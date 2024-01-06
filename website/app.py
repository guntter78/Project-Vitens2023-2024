from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

def create_connection():
    try:
        # Verbinding maken met de PostgreSQL-database 'vitenswatersystem'
        conn = psycopg2.connect(
            host="localhost",
            database=".",
            user='.',
            password='.')
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
            cur.execute("SELECT * FROM flowsensor")
            data = cur.fetchall()
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
    return render_template('index.html', sensor_data=sensor_data)

if __name__ == '__main__':
    app.run(debug=True)
