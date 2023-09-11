# Importing required libraries
import os
import json
import base64
import keyboard
from cryptography.fernet import Fernet
import msvcrt
import http.server
import socketserver
import threading
import signal

# Function to generate key


def generate_key():
    return Fernet.generate_key()

# Function to encrypt the data


def encrypt(text, key):
    fernet = Fernet(key)
    encrypted_text = fernet.encrypt(text.encode())
    return encrypted_text

# Function to decrypt the data


def decrypt(encrypted_text, key):
    fernet_key = Fernet(base64.urlsafe_b64encode(key.encode()[:32]))
    decrypted_text = fernet_key.decrypt(encrypted_text).decode()
    return decrypted_text


# Function to check if the input key is unique


def is_unique_key(master_dict, key):
    return key not in master_dict

# Function to mask the input


def mask_input(prompt):
    print(prompt, end='', flush=True)
    password = []
    while True:
        char = msvcrt.getch()
        if char == b'\r':  # Enter key
            print()
            break
        elif char == b'\x08':  # Backspace
            if password:
                password.pop()
                print('\b \b', end='', flush=True)
        else:
            password.append(char.decode())
            print('*', end='', flush=True)
    return ''.join(password)

# Function to load previous data


def load_master_dict():
    if os.path.exists("data.bin"):
        with open("data.bin", "rb") as f:
            binary_data = f.read()
            decoded_data = base64.b64decode(binary_data).decode()
            return json.loads(decoded_data)
    else:
        return {}

# Function to store data


def store_data(master_dict):
    # Update master_dict with existing data
    master_dict.update(load_master_dict())

    while True:
        label = input("Enter Label: ").strip()
        value = mask_input("Enter Value: ").strip()

        if not label or not value:
            print("Input is empty. Re-try.")
            continue

        # Encrypt the label and value
        encryption_key = generate_key()
        encrypted_label = encrypt(label, key=encryption_key)
        encrypted_value = encrypt(value, key=encryption_key)

        # Convert the label and value to string to store in dictionary(JSON)
        encrypted_label = base64.b64encode(encrypted_label).decode()
        encrypted_value = base64.b64encode(encrypted_value).decode()

        key_value_pair = {encrypted_label: encrypted_value}

        # Prompt the user for a unique key
        while True:
            key = input("Enter the key: ").strip()
            if len(key) != 3 or not key.isalnum() or not key.isupper():
                print("Invalid key format.")
            elif not is_unique_key(master_dict, key):
                print("Key already exists. Please enter a unique key.")
            else:
                break

        # Add the key-value pair to the master dictionary
        master_dict[key] = key_value_pair

        # Convert master dictionary to binary and save to file
        binary_data = base64.b64encode(json.dumps(master_dict).encode())
        with open("data.bin", "wb") as f:
            f.write(binary_data)

        print("Data stored successfully.")
        print("Your key: ", encryption_key)
        break


# Function to retrieve data


def retrieve_data(master_dict):
    while True:

        if os.path.exists("data.bin"):
            with open("data.bin", "rb") as f:
                binary_data = f.read()
                decoded_data = base64.b64decode(binary_data).decode()
                master_dict = json.loads(decoded_data)
        else:
            print("No data found.")
            return

        # Prompt the user for the key
        while True:
            key = input("Enter the key: ").strip()
            if len(key) != 3 or not key.isalnum() or not key.isupper():
                print("Invalid key format.")
            elif key not in master_dict:
                print("Key not found.")
            else:
                break

        # Prompt the user for the key to decrypt
        decryption_key = input("Enter the key to decrypt: ").strip()

        # Retrieve the key-value pair and decrypt
        encrypted_label = list(master_dict[key].keys())[0]
        encrypted_value = master_dict[key][encrypted_label]

        encrypted_label = base64.b64decode(encrypted_label)
        encrypted_value = base64.b64decode(encrypted_value)

        # Replace '-1' with decryption key
        label = decrypt(encrypted_label, key=decryption_key)
        # Replace '-2' with decryption key
        value = decrypt(encrypted_value, key=decryption_key)

        print(f"Label: {label}")
        print(f"Value: {value}")
        break


# Function to view the data in an HTML file


def view_data(master_dict):
    if os.path.exists("data.bin"):
        with open("data.bin", "rb") as f:
            binary_data = f.read()
            decoded_data = base64.b64decode(binary_data).decode()
            master_dict = json.loads(decoded_data)

        # Create HTML content
        html_content = "<html><body><h1>Stored Data:</h1><ul>"
        for key, key_value_pair in master_dict.items():
            encrypted_label = list(key_value_pair.keys())[0]
            encrypted_value = key_value_pair[encrypted_label]
            html_content += f"<li>Key: {key}, Label: {encrypted_label}, Value: {encrypted_value}</li>"
        html_content += "</ul></body></html>"

        # Write HTML content to file
        with open("data.html", "w") as f:
            f.write(html_content)

        print("HTML file created and hosted on localhost:6001")

        class CustomHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html_content.encode())

        global server

        PORT = 6001
        with socketserver.TCPServer(("", PORT), CustomHandler) as server:
            print(f"Server running on localhost:{PORT}")

            view_data.server = server
            signal.signal(signal.SIGINT, stop_server)

            # Start the server in a separate thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            input("Press Enter to stop the server.")

    else:
        print("No data found.")

# Function to shutdown the server


def stop_server(sig, frame):
    global server
    if server is not None:
        print("Stopping the server.")
        server.shutdown()
        server = None

# Function to clear screen on every iteration


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# Function to navigate through the options during selection


def select_option():
    options = ["Store", "Retrieve", "View"]
    current_option = 0

    while True:
        clear_screen()

        for i, option in enumerate(options):
            if i == current_option:
                print(f"> {option}")
            else:
                print(f"  {option}")

        # Detect arrow key presses to navigate options
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == "down":
                current_option = (current_option + 1) % len(options)
            elif event.name == "up":
                current_option = (current_option - 1) % len(options)
        elif event.event_type == keyboard.KEY_UP and event.name == "enter":
            return options[current_option]


def main():
    option = select_option().strip()
    master_dict = {}

    if option == "Store":
        store_data(master_dict)
    elif option == "Retrieve":
        retrieve_data(master_dict)
    elif option == "View":
        view_data(master_dict)
    else:
        print("Invalid option.")


if __name__ == "__main__":
    main()
