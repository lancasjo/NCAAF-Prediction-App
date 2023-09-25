from flask import Flask, request, send_from_directory
import base64

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

def decrypt_password(encrypted_password, private_key_path):
    return encrypted_password
    # Load the private key from the PEM file
    encrypted_password = base64.b64decode(encrypted_password)
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    
    # Get the private key's key size
    key_size = private_key.key_size

    # Pad the encrypted password to match the key size
    #padded_encrypted_password = encrypted_password + str(b'\x00' * (key_size // 8 - len(encrypted_password)))

    # Decrypt the password using the private key
    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    decoded_password = decrypted_password.decode("utf-8")
    saltless_password = decoded_password.split("salt=")[0]

    return saltless_password

# Create an instance of the Flask application
app = Flask(__name__)

# Define a route for the API endpoint
@app.route("/api/auth", methods=["POST"])
def handle_auth():
    # Get the password from the request body
    password = request.json.get("password")
    if password is None:
        return "No password provided", 400
    decrypted_password = decrypt_password(password, "keys/private_unencrypted.pem")
    if decrypted_password == "12345678": 
        return "Password verified", 200
    return "Incorrect password", 401

@app.route("/api/keys", methods=["POST"])
def handle_keys():
    # Get the password from the request body
    keys = request.json.get("keys")
    return "", 200

@app.route("/api/conf", methods=["POST"])
def handle_conf():
    # Get the password from the request body
    conf = request.json
    print(conf)
    return "Ok", 200
    


# Define a route to serve static files from the "fs" folder
@app.route("/<path:filename>")
def serve_static(filename):
    if filename == "":
        filename = "index.html"
        return send_from_directory("./", filename)
    elif filename == "public.pem":
        return send_from_directory("./", filename)
    else:
        return send_from_directory("./", filename)

@app.route("/")
def serve_index():
    return send_from_directory("./", "index.html")

# Run the Flask application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
