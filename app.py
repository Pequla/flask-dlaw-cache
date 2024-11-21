from flask import Flask, jsonify, make_response
import requests
from datetime import datetime
import mysql.connector
from config import DB_CONFIG

# Initialize Flask app
app = Flask(__name__)

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )

# Helper function to fetch data and sync with the database
def sync_data():
    url = 'https://api.beocraft.net/members'
    urlFordiscord_id = 'https://link.samifying.com/api/data/discord/'
    urlForMinecraftName = 'https://link.samifying.com/api/cache/uuid/'

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        discord_ids = []
        minecraftNames = []

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        for member in data:
            try:
                # Fetch Discord ID
                responsediscord_id = requests.get(urlFordiscord_id + str(member['id']))
                if responsediscord_id.status_code == 200:
                    discord_id = responsediscord_id.json()
                    discord_ids.append(discord_id)
                else:
                    print(f"Error fetching discord_id for member {member['id']}: {responsediscord_id.status_code}")
                    continue  # Skip this member and move on to the next

                # Fetch Minecraft Name
                responseMinecraftName = requests.get(urlForMinecraftName + str(discord_id['uuid']))
                if responseMinecraftName.status_code == 200:
                    minecraftName = responseMinecraftName.json()
                    minecraftNames.append(minecraftName)
                else:
                    print(f"Error fetching Minecraft name for discord_id {discord_id['uuid']}: {responseMinecraftName.status_code}")
                    continue  # Skip this member if we can't fetch Minecraft name

                # Update or insert the data into the database
                minecraft_names_dict = {entry['id']: entry['name'] for entry in minecraftNames}

                discord_name = member['name']
                user_discord_id = member['id']
                discord_joined_at = member['joinedAt']

                matching_discord_entry = next(
                    (item for item in discord_ids if item['user']['discordId'] == user_discord_id),
                    None
                )

                if matching_discord_entry:
                    discord_id = matching_discord_entry['user']['discordId']
                    uuid = matching_discord_entry['uuid']
                    link_created_at = matching_discord_entry['createdAt']
                    minecraft_name = minecraft_names_dict.get(uuid, "N/A")
                    cached_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

                    cursor.execute("SELECT * FROM player_data WHERE discord_id = %s OR uuid = %s", (discord_id, uuid))
                    existing_player = cursor.fetchone()

                    if existing_player:
                        if (existing_player['minecraft_name'] != minecraft_name or
                                existing_player['discord_name'] != discord_name or
                                existing_player['discord_joined_at'] != discord_joined_at):

                            sql = """
                            UPDATE player_data
                            SET minecraft_name = %s, discord_name = %s, discord_joined_at = %s,
                                link_created_at = %s, cached_at = %s
                            WHERE discord_id = %s AND uuid = %s
                            """
                            values = (
                                minecraft_name, discord_name, discord_joined_at,
                                link_created_at, cached_at, discord_id, uuid
                            )
                            cursor.execute(sql, values)
                            db.commit()
                    else:
                        sql = """
                        INSERT INTO player_data (
                            discord_id, uuid, minecraft_name, discord_name, 
                            discord_joined_at, link_created_at, cached_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        values = (
                            discord_id, uuid, minecraft_name, discord_name, 
                            discord_joined_at, link_created_at, cached_at
                        )
                        cursor.execute(sql, values)
                        db.commit()

            except Exception as e:
                print(f"Error processing member {member['id']}: {e}")
                continue  # Skip this member and move on to the next

        cursor.close()
        db.close()

def delete_inactive_players():
    url = 'https://api.beocraft.net/members'
    urlFordiscord_id = 'https://link.samifying.com/api/data/discord/'

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Store all the discord_ids from API
        api_discord_ids = []

        for member in data:
            try:
                # Fetch Discord ID
                responsediscord_id = requests.get(urlFordiscord_id + str(member['id']))
                if responsediscord_id.status_code == 200:
                    discord_id = responsediscord_id.json()
                    api_discord_ids.append(discord_id['user']['discordId'])
                else:
                    print(f"Error fetching discord_id for member {member['id']}: {responsediscord_id.status_code}")
                    continue  # Skip this member and move on to the next
            except Exception as e:
                print(f"Error processing member {member['id']}: {e}")
                continue

        # Fetch all discord_ids from the database
        cursor.execute("SELECT discord_id FROM player_data")
        database_discord_ids = [row['discord_id'] for row in cursor.fetchall()]

        # Find discord_ids that are in the database but not in the API response
        discord_ids_to_delete = set(database_discord_ids) - set(api_discord_ids)

        if discord_ids_to_delete:
            cursor.execute("DELETE FROM player_data WHERE discord_id IN (%s)" % ','.join(['%s'] * len(discord_ids_to_delete)), tuple(discord_ids_to_delete))
            db.commit()
            print(f"Deleted {cursor.rowcount} player(s) from the database.")

        cursor.close()
        db.close()

# Sync API endpoint
@app.route('/api/sync', methods=['POST'])
def sync_endpoint():
    sync_data()
    delete_inactive_players()
    return make_response('', 204)

# Retrieve all data
@app.route('/api/data', methods=['GET'])
def get_all_data():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM player_data")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(result)

# Retrieve data by Discord ID
@app.route('/api/data/discord/<discord_id>', methods=['GET'])
def get_data_by_discord_id(discord_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM player_data WHERE discord_id = %s", (discord_id,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result:
        return jsonify(result)
    else:
        return {"message": "No data found for the provided Discord ID"}, 404

# Retrieve data by Minecraft UUID
@app.route('/api/data/minecraft/<uuid>', methods=['GET'])
def get_data_by_uuid(uuid):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM player_data WHERE uuid = %s", (uuid,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result:
        return jsonify(result)
    else:
        return {"message": "No data found for the provided UUID"}, 404

# Retrieve data by database ID
@app.route('/api/data/<int:id>', methods=['GET'])
def get_data_by_id(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM player_data WHERE player_id = %s", (id,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result:
        return jsonify(result)
    else:
        return {"message": "No data found for the provided database ID"}, 404

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=False)
