import sqlite3

def svuota_db(percorso_db):
    conn = sqlite3.connect(percorso_db)
    cursor = conn.cursor()

    # Recupera tutti i nomi delle tabelle utente (esclude quelle di sistema)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tabelle = cursor.fetchall()

    print(tabelle)

    for tabella in tabelle:
        nome_tabella = tabella[0]
        try:
            cursor.execute(f'DELETE FROM "{nome_tabella}";')
            print(f'Tabella "{nome_tabella}" svuotata.')
        except Exception as e:
            print(f'Errore durante la cancellazione della tabella "{nome_tabella}": {e}')
    #cursor.execute(f'DELETE FROM "daily_prices";')
    conn.commit()
    conn.close()
    print("Database svuotato con successo.")

# Esempio di utilizzo
# svuota_db("percorso/del/tuo/database.sqlite")


svuota_db("./fares.db")
