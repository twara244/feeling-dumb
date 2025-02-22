import base64

with open("firebase-auth.json", "r") as file:
    encoded = base64.b64encode(file.read().encode()).decode()

print(encoded)
