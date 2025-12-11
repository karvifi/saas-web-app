import sqlite3
import json

conn = sqlite3.connect('data/user_profiles.db')
cursor = conn.cursor()
cursor.execute('SELECT user_id, profile_data FROM users')
rows = cursor.fetchall()
for row in rows:
    print(f'User: {row[0]}')
    profile = json.loads(row[1])
    context = profile.get('context', {})
    print(f'  Task count: {context.get("task_count", 0)}')
    print(f'  Subscription: {context.get("subscription", "none")}')
conn.close()