import sqlite3
import os
import json

db_path = 'data/user_profiles.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get current profile data
    cursor.execute('SELECT profile_data FROM users WHERE user_id = "free_user"')
    result = cursor.fetchone()

    if result:
        profile_data = json.loads(result[0])
        profile_data['context']['task_count'] = 0

        # Update the profile data
        cursor.execute('UPDATE users SET profile_data = ? WHERE user_id = "free_user"',
                      (json.dumps(profile_data),))
        conn.commit()
        print('Reset task count for free_user')
    else:
        print('User not found')

    conn.close()
else:
    print('Database not found')