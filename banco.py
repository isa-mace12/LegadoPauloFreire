import psycopg2

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="legado_paulo_freire",
        user="postgres",
        password="senai",
        port="5432"
    )
