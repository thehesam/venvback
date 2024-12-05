from flask import Flask, jsonify, request
from pymongo import MongoClient
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.backends import default_backend

# Flask setup
app = Flask(__name__)

# MongoDB setup
mongo_user = "Hesam"
mongo_pass = "2360291"
uri = f"mongodb+srv://{mongo_user}:{mongo_pass}@v-env.m0bml.mongodb.net/?retryWrites=true&w=majority&appName=v-env"

client = MongoClient(uri)
db = client['air_quality_data']
collection = db['sensor_readings_sec']

# Encryption key setup
key = 'JPmtyDKw6x6nF5t9fLC9_GrfFVwnpvjZJ081uA9Ak_8='

if key is None:
    raise ValueError("Environment variable 'AIR_QUALITY_AES_KEY' is not set.")

key = key.encode()[:32]  # AES-256 requires a 32-byte key

def decrypt_data(encrypted_data):
    """
    Decrypt data using AES in CBC mode by extracting the IV.
    """
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    # Create a cipher object
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the data
    decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove padding
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(decrypted_padded_data) + unpadder.finalize()

def verify_hash(data, hash_from_db):
    """
    Verify the hash of the decrypted data matches the stored hash.
    """
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(data)
    calculated_hash = digest.finalize()

    return calculated_hash == hash_from_db

@app.route('/api/sensor', methods=['GET'])
def get_sensor_data():
    """
    Endpoint to get the 10 most recent sensor data from the database.
    """
    try:
        # Query the database for the 10 most recent records
        data = collection.find().sort("timestamp", -1).limit(10)  # Sort by timestamp descending, limit to 10

        # Prepare the response list
        sensor_data_list = []
        for record in data:
            # Decrypt the data fields
            decrypted_pm1 = decrypt_data(record["PM1.0"]).decode()
            decrypted_pm25 = decrypt_data(record["PM2.5"]).decode()
            decrypted_pm10 = decrypt_data(record["PM10"]).decode()

            # Combine the decrypted data to calculate hash
            combined_data = f"{decrypted_pm1},{decrypted_pm25},{decrypted_pm10}".encode()

            # Verify the hash
            is_valid = verify_hash(combined_data, record["hash"])

            # Construct the response object
            sensor_data = {
                "PM1.0": decrypted_pm1,
                "PM2.5": decrypted_pm25,
                "PM10": decrypted_pm10,
                "timestamp": record["timestamp"].isoformat(),  # Format the timestamp
                "hash": is_valid  # Include hash verification result
            }

            sensor_data_list.append(sensor_data)

        # Return as JSON
        return jsonify(sensor_data_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


from flask import Flask, jsonify, request, send_from_directory
import os

# Existing imports and setup

@app.route('/')
def serve_frontend():
    """
    Serve the front-end HTML file.
    """
    return send_from_directory(os.getcwd(), 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)