import psycopg2

conn = psycopg2.connect(
        host="localhost",
        database="vitens_data",
        user='vitens',
        password='project')

cur = conn.cursor()

cur.execute('CREATE TABLE data (id serial PRIMARY KEY,'
                                'Location varchar(50) NOT NULL,'
                                 'Flow varchar (50) NOT NULL,'
                                 'Pressure varchar (50) NOT NULL,'
                                 'author varchar (50) NOT NULL);')

 
conn.commit() 
  
cur.close() 
conn.close() 