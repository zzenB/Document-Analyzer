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
    # Generate session id for use in chat history
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

def update_message_with_sources(session_id, sources):
    # Update the AI message with sources
    conn = sqlite3.connect("sqlite.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, message FROM history
        WHERE session_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (session_id,))
    
    row = cursor.fetchone()
    if row:
        message_id, message_json = row
        message_data = json.loads(message_json)

        if message_data["type"] == "ai":
            message_data["data"]["sources"] = sources

            updated_message_json = json.dumps(message_data)
            cursor.execute("""
                UPDATE history SET message = ? WHERE id = ?
            """, (updated_message_json, message_id))
            
            conn.commit()


    conn.close()

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
            # data.append({res['type']: res['data']['content']})
            if res['type'] == 'human':
                data.append({res['type']: res['data']['content']})
            elif res['type'] == 'ai':
                ai_message = {
                    'content': res['data']['content'],
                    'sources': res['data'].get('sources', [])  # Include sources if available
                }
                data.append({res['type']: ai_message})
            
        result[session_id] = data[:]
        data.clear()

    # Close the database connection
    conn.close()

    return result

# DEBUG
# if __name__ == "__main__":
#     return_chat_history()