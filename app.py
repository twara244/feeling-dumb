from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get Firebase credentials from environment variable
firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
if not firebase_creds_json:
    raise ValueError("FIREBASE_CREDENTIALS environment variable is not set.")

try:
    firebase_creds = credentials.Certificate(json.loads(firebase_creds_json))
    firebase_admin.initialize_app(firebase_creds)
    db = firestore.client()
except Exception as e:
    raise ValueError(f"Error initializing Firebase: {e}")

# Set SECRET_KEY from environment variable
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable is not set.")

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No token provided"}), 401

        token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = auth.verify_id_token(token)
            request.user = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401

    return decorated_function

@app.route('/api/auth/signup/email', methods=['POST'])
def signup_with_email():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        display_name = data.get('displayName', '')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # First check if user exists
        try:
            existing_user = auth.get_user_by_email(email)
            return jsonify({"error": "Email already exists"}), 400
        except auth.UserNotFoundError:
            pass  # Continue with user creation if user not found

        # Create user in Firebase
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False
        )

        # Create user document in Firestore
        user_data = {
            'uid': user.uid,
            'email': email,
            'displayName': display_name,
            'createdAt': datetime.now(),
            'lastLogin': datetime.now()
        }
        db.collection('users').document(user.uid).set(user_data)

        # Create custom token
        custom_token = auth.create_custom_token(user.uid)

        return jsonify({
            "message": "User created successfully",
            "token": custom_token.decode(),
            "user": {
                "uid": user.uid,
                "email": email,
                "displayName": display_name
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/auth/signin/email', methods=['POST'])
def signin_with_email():
    try:
        data = request.json
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({"error": "ID token is required"}), 400

        # Verify the token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get user data
        user = auth.get_user(uid)

        # Update last login in Firestore
        db.collection('users').document(uid).update({
            'lastLogin': datetime.now()
        })

        return jsonify({
            "message": "Login successful",
            "user": {
                "uid": uid,
                "email": user.email,
                "displayName": user.display_name
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/api/auth/signin/google', methods=['POST'])
def signin_with_google():
    try:
        data = request.json
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({"error": "ID token is required"}), 400

        # Verify the Google ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get user data from Firebase Auth
        user = auth.get_user(uid)
        email = user.email
        name = user.display_name

        # Check if user exists in Firestore
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            # Create new user document
            user_data = {
                'uid': uid,
                'email': email,
                'displayName': name,
                'createdAt': datetime.now(),
                'lastLogin': datetime.now(),
                'provider': 'google'
            }
            user_ref.set(user_data)
        else:
            # Update last login
            user_ref.update({
                'lastLogin': datetime.now()
            })

        return jsonify({
            "message": "Google sign-in successful",
            "user": {
                "uid": uid,
                "email": email,
                "displayName": name
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/api/auth/verify-token', methods=['POST'])
def verify_token():
    try:
        data = request.json
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({"error": "ID token is required"}), 400

        # Verify the token
        decoded_token = auth.verify_id_token(id_token)
        
        # Get user data
        user = auth.get_user(decoded_token['uid'])
        
        return jsonify({
            "valid": True,
            "user": {
                "uid": user.uid,
                "email": user.email,
                "displayName": user.display_name
            }
        }), 200

    except Exception as e:
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 401

@app.route('/api/auth/password-reset', methods=['POST'])
def password_reset():
    try:
        data = request.json
        email = data.get('email')

        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Generate password reset link
        reset_link = auth.generate_password_reset_link(email)

        return jsonify({
            "message": "Password reset email sent successfully",
            "resetLink": reset_link
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/user/profile', methods=['GET'])
@auth_required
def get_user_profile():
    try:
        uid = request.user['uid']
        user_doc = db.collection('users').document(uid).get()

        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404

        user_data = user_doc.to_dict()
        return jsonify(user_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/user/profile', methods=['PUT'])
@auth_required
def update_user_profile():
    try:
        uid = request.user['uid']
        data = request.json

        allowed_updates = ['displayName', 'photoURL', 'phoneNumber']
        update_data = {k: v for k, v in data.items() if k in allowed_updates}

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Update in Firebase Auth
        auth.update_user(
            uid,
            display_name=update_data.get('displayName'),
            photo_url=update_data.get('photoURL'),
            phone_number=update_data.get('phoneNumber')
        )

        # Update in Firestore
        db.collection('users').document(uid).update(update_data)

        return jsonify({
            "message": "Profile updated successfully",
            "updates": update_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/')
def home():
    return "FeelingDumb"

# @app.route('/login')
# def login():
#     if 'user' in session:
#         return redirect(url_for('dashboard'))
#     else:
#         return render_template('login.html')

# @app.route('/signup')
# def signup():
#     if 'user' in session:
#         return redirect(url_for('dashboard'))
#     else:
#         return render_template('signup.html')


# @app.route('/reset-password')
# def reset_password():
#     if 'user' in session:
#         return redirect(url_for('dashboard'))
#     else:
#         return render_template('forgot_password.html')

# @app.route('/terms')
# def terms():
#     return render_template('terms.html')

# @app.route('/privacy')
# def privacy():
#     return render_template('privacy.html')

# @app.route('/logout')
# def logout():
#     session.pop('user', None)  # Remove the user from session
#     response = make_response(redirect(url_for('login')))
#     response.set_cookie('session', '', expires=0)  # Optionally clear the session cookie
#     return response


##############################################
""" Private Routes (Require authorization) """

@app.route('/dashboard')
@auth_required
def dashboard():

    return render_template('dashboard.html')


@app.route('/chat',methods=['GET','POST'])
def chat():
    output=None
    if request.method=='POST':
        # user_id = request.args.get('user_id')
        user_input = request.json.get('user_input')
        chat_id = request.json.get('chat_id')
        mood = request.json.get('mood')

        if not (chat_id or user_input or mood):
            return jsonify({"status": "error", "message": "all the fields are mandatory"}), 403

        # if user_input:
        prompt="You are my personal diary, and my mood is "+ mood + " so act as an therapist,give some tips and console or give suggessions in short like 1-2 lines max for whatever i write without any extra thing like sure,fine,okay etc.  "+ user_input
        print(prompt)
                                                

        genai.configure(api_key="AIzaSyAqlOp3sYu0wsGR8w3ksY8WSsNPEhsCJXo")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        output = response.text

        message_ref = db.collection('chats').document(chat_id).collection('messages').document()
        message_ref.set({
            'user_input': user_input,  # Save the user's message
            'output': output,    # Save Gemini's response
            'timestamp': firestore.SERVER_TIMESTAMP
        })


    return jsonify({"status": "success", "message": "Message saved","msg_id": message_ref.id,"output":output}), 404

# # Function to verify Firebase JWT token
# def verify_token(id_token):
#     try:
#         decoded_token = auth.verify_id_token(id_token)
#         return decoded_token['uid']
#     except Exception as e:
#         print(f"Error verifying token: {e}")
#         return None
    

@app.route('/get_chat', methods=['GET'])
def get_chat():
    """Retrieve all messages from the active chat session."""
    user_id = request.json.get('user_id')
    chat_id = request.json.get('chat_id')

    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    db_ref = db.collection('chats')

    if chat_id:
        # Fetch messages from a specific chat
        chat_ref = db_ref.document(chat_id)
        chat_doc = chat_ref.get()

        if not chat_doc.exists or chat_doc.to_dict().get('user_id') != user_id:
            return jsonify({"status": "error", "message": "Chat not found or unauthorized"}), 403

        messages_ref = chat_ref.collection('messages')
        messages = messages_ref.order_by('timestamp').stream()

        chat_history = [
            {
                "user_input": msg.to_dict().get('user_input', ""),
                "output": msg.to_dict().get('output', ""),
                "timestamp": msg.to_dict().get('timestamp')
            }
            for msg in messages
        ]

        return jsonify({"status": "success", "chat_id": chat_id, "messages": chat_history}), 200

    else:
        # Fetch all chat IDs for the given user and their messages
        user_chats = db_ref.where('user_id', '==', user_id).stream()

        chat_list = []
        
        for chat in user_chats:
            chat_data = chat.to_dict()
            chat_id = chat.id

            # Fetch messages for each chat
            messages_ref = db_ref.document(chat_id).collection('messages')
            messages = messages_ref.order_by('timestamp').stream()

            chat_messages = [
                {
                    "user_input": msg.to_dict().get('user_input', ""),
                    "output": msg.to_dict().get('output', ""),
                    "timestamp": msg.to_dict().get('timestamp')
                }
                for msg in messages
            ]

            chat_list.append({
                "chat_id": chat_id,
                "messages": chat_messages  # Include messages of this chat
            })

        return jsonify({"status": "success", "user_id": user_id, "chats": chat_list}), 200

@app.route('/start_chat', methods=['POST'])
def start_chat():
    """Create a new chat session for the user."""
    print(request.get_json())
    user_id = request.json.get('user_id')
    print(f"Received user_id: {user_id}") 


    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    chat_ref = db.collection('chats').document()  # Generate a new chat ID
    chat_ref.set({
        'user_id': user_id,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'chat_id': chat_ref.id
    })

    session['chat_id'] = chat_ref.id  # Store chat_id in session

    return jsonify({"status": "success", "chat_id": chat_ref.id, "message": "New chat started"}), 200

@app.route('/save_message', methods=['POST'])
def save_message():
    """Save or update user messages inside the active chat session, including full deletions."""
    data = request.get_json()  # Read JSON data

    chat_id = data.get('chat_id')
    latest_text = data.get('message')  # Allow multi-line text
    msg_id = data.get('msg_id')

    print("Received chat_id:", chat_id)
    print("Received message:", latest_text)

    if not chat_id or not latest_text:
        return jsonify({"status": "error", "message": "Missing chat_id or message"}), 403

    if msg_id:
        # Update existing message
        message_ref = db.collection('chats').document(chat_id).collection('messages').document(msg_id)
        message = message_ref.get()

        if message.exists:
            message_ref.update({'user_input': latest_text, 'timestamp': firestore.SERVER_TIMESTAMP})
            return jsonify({"status": "success", "message": "Message updated", "msg_id": msg_id}), 200
        else:
            return jsonify({"status": "error", "message": "Message not found"}), 404

    else:
        # Create a new message
        message_ref = db.collection('chats').document(chat_id).collection('messages').document()
        message_ref.set({
            'user_input': latest_text,  # This now supports multi-line text
            'timestamp': firestore.SERVER_TIMESTAMP
        })
  

    
    return jsonify({"status": "success", "message": "Message saved", "msg_id": message_ref.id}), 200

    
@app.route('/summary', methods=['GET'])
def summary():
    output=None
    chat_history=""
    if request.method=='GET':
        user_id = request.json.get('user_id')
        chat_id = request.json.get('chat_id')

        if not chat_id:
            return jsonify({"status": "error", "message": "all the fields are mandatory"}), 403

        # if user_input:
        db_ref = db.collection('chats')
        chat_ref = db_ref.document(chat_id)
        chat_doc = chat_ref.get()

        if not chat_doc.exists or chat_doc.to_dict().get('user_id') != user_id:
            return jsonify({"status": "error", "message": "Chat not found or unauthorized"}), 403

        messages_ref = chat_ref.collection('messages')
        messages = messages_ref.order_by('timestamp').stream()


            
        for msg in messages:
            chat_history = chat_history + msg.to_dict().get('user_input', "")
        

        prompt="See now i will provide you a list of my notes that i wrote, you have to give me a short summary and instead of author or writer use you." + chat_history


        genai.configure(api_key="AIzaSyAqlOp3sYu0wsGR8w3ksY8WSsNPEhsCJXo")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        output = response.text



        return jsonify({"status": "success", "chat_id": chat_id, "summary": output}), 200                                                


@app.route('/delete_chat', methods=['DELETE'])
def delete_chat():
    """Delete a specific chat document without explicitly deleting messages."""
    user_id = request.json.get('user_id')
    chat_id = request.json.get('chat_id')

    if not user_id or not chat_id:
        return jsonify({"status": "error", "message": "User ID and Chat ID are required"}), 400

    try:
        chat_ref = db.collection('chats').document(chat_id)
        
        # Check if the chat exists before deleting
        if not chat_ref.get().exists:
            return jsonify({"status": "error", "message": "Chat not found"}), 404
        
        chat_ref.delete()  # Delete the chat document

        return jsonify({"status": "success", "message": f"Chat {chat_id} deleted"}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

        
        
if __name__ == '__main__':
    app.run(debug=True)
