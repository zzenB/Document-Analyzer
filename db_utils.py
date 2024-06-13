import sqlite3
import json

def create_db():
    # Create a new SQLite3 database file (if it doesn't exist)
    conn = sqlite3.connect('sqlite.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
             (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, message TEXT)''')
    conn.commit()
    conn.close()

def generate_session_id():
    conn = sqlite3.connect('sqlite.db')
    c = conn.cursor()

    # Get the maximum existing session ID from the message_store table
    c.execute("SELECT MAX(session_id) FROM history")
    max_session_id = c.fetchone()[0]

    if max_session_id is None:
        new_session_id = "1"
    else:
        new_session_id = str(int(max_session_id) + 1)

    conn.close()

    return new_session_id

def return_chat_history():
    # Display chat history based on session_id
    conn = sqlite3.connect('sqlite.db')
    result = {}
    data = []
    c = conn.cursor()

    c.execute("SELECT DISTINCT session_id FROM history")
    session_ids = [row[0] for row in c.fetchall()]

    for session_id in session_ids:
        c.execute("SELECT message FROM history WHERE session_id = ?", (session_id,))
        messages = c.fetchall()
        for message in messages:
            res = json.loads(message[0])
            # print(f"res at session_id {session_id}: {res}\n")
            # data.append({"session_id": session_id, res['type']: res['data']['content']})
            data.append({res['type']: res['data']['content']})
        # print(f"data at session_id {session_id}: {data}\n")
        result[session_id] = data[:]
        # print(f"result at session_id {session_id}: {result[session_id] }\n")
        data.clear()

    # print(f"result: {result}")
    # Close the database connection
    conn.close()

    return result

if __name__ == "__main__":
    return_chat_history()

    