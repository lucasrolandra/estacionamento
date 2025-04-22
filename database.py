import sqlite3
from datetime import datetime

def criar_banco_dados():
    conn = sqlite3.connect('estacionamento.db')
    cursor = conn.cursor()
    
    # Tabela de veículos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT NOT NULL UNIQUE,
        modelo TEXT,
        cor TEXT,
        proprietario TEXT
    )
    ''')
    
    # Tabela de movimentações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        entrada DATETIME NOT NULL,
        saida DATETIME,
        valor_pago REAL,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def cadastrar_veiculo(placa, modelo, cor, proprietario):
    conn = sqlite3.connect('estacionamento.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO veiculos (placa, modelo, cor, proprietario)
        VALUES (?, ?, ?, ?)
        ''', (placa, modelo, cor, proprietario))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Placa já cadastrada
    finally:
        conn.close()

def registrar_entrada(placa):
    conn = sqlite3.connect('estacionamento.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM veiculos WHERE placa = ?', (placa,))
    resultado = cursor.fetchone()
    
    if resultado:
        veiculo_id = resultado[0]
        cursor.execute('''
        SELECT id FROM movimentacoes 
        WHERE veiculo_id = ? AND saida IS NULL
        ''', (veiculo_id,))
        
        if cursor.fetchone() is None:
            cursor.execute('''
            INSERT INTO movimentacoes (veiculo_id, entrada)
            VALUES (?, ?)
            ''', (veiculo_id, datetime.now()))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

def registrar_saida(placa, valor_por_hora=5.0):
    conn = sqlite3.connect('estacionamento.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM veiculos WHERE placa = ?', (placa,))
    resultado = cursor.fetchone()
    
    if resultado:
        veiculo_id = resultado[0]
        cursor.execute('''
        SELECT id, entrada FROM movimentacoes 
        WHERE veiculo_id = ? AND saida IS NULL
        ''', (veiculo_id,))
        
        movimento = cursor.fetchone()
        if movimento:
            movimento_id, entrada = movimento
            saida = datetime.now()
            entrada_dt = datetime.strptime(entrada, '%Y-%m-%d %H:%M:%S.%f')
            horas = (saida - entrada_dt).total_seconds() / 3600
            valor_pago = round(horas * valor_por_hora, 2)
            
            cursor.execute('''
            UPDATE movimentacoes 
            SET saida = ?, valor_pago = ?
            WHERE id = ?
            ''', (saida, valor_pago, movimento_id))
            conn.commit()
            conn.close()
            return valor_pago
    conn.close()
    return None

def listar_veiculos_estacionados():
    conn = sqlite3.connect('estacionamento.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT v.placa, v.modelo, v.cor, m.entrada 
    FROM veiculos v
    JOIN movimentacoes m ON v.id = m.veiculo_id
    WHERE m.saida IS NULL
    ''')
    
    veiculos = cursor.fetchall()
    conn.close()
    return veiculos

def gerar_relatorio(dia=None):
    conn = sqlite3.connect('estacionamento.db')
    cursor = conn.cursor()
    
    if dia:
        cursor.execute('''
        SELECT v.placa, v.modelo, m.entrada, m.saida, m.valor_pago
        FROM veiculos v
        JOIN movimentacoes m ON v.id = m.veiculo_id
        WHERE date(m.entrada) = date(?)
        ORDER BY m.entrada
        ''', (dia,))
    else:
        cursor.execute('''
        SELECT v.placa, v.modelo, m.entrada, m.saida, m.valor_pago
        FROM veiculos v
        JOIN movimentacoes m ON v.id = m.veiculo_id
        ORDER BY m.entrada
        ''')
    
    relatorio = cursor.fetchall()
    conn.close()
    return relatorio
