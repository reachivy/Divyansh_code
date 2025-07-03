# # app.py - helloIVY Career Selector Application
#
# from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
# import google.generativeai as genai
#
# genai.configure(api_key=GEMINI_API_KEY)
# gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
#
# import os
# import json
# import tempfile
# import logging
# import re
# import time
# from datetime import datetime
# from pathlib import Path
# from flask import Flask, request, jsonify, send_from_directory, redirect
# from flask_cors import CORS
# from voice_processor import VoiceProcessor
#
# from config import WHISPER_MODEL_NAME, DEVICE
#
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
# app = Flask(__name__)
# CORS(app)
#
# os.makedirs('data', exist_ok=True)
# os.makedirs('data/audio_temp', exist_ok=True)
# os.makedirs('logs', exist_ok=True)
# os.makedirs('static', exist_ok=True)
#
# voice_processor = VoiceProcessor(model_name=WHISPER_MODEL_NAME, device=DEVICE)
# career_explorer = None  # Will be initialized later
#
# @app.route('/api/health')
# def health_check():
#     return jsonify({
#         'status': 'healthy',
#         'timestamp': datetime.now().isoformat(),
#         'voice_available': voice_processor.is_available()['whisper'],
#         'ai_available': career_explorer is not None,
#         'version': '1.0.0',
#         'features': {
#             'speech_recognition': voice_processor.is_available()['whisper'],
#             'career_exploration': career_explorer is not None,
#             'conversation_storage': True
#         }
#     })
#
# @app.route('/api/voice-transcribe', methods=['POST'])
# def voice_transcribe():
#     logger.info("VOICE TRANSCRIBE ENDPOINT CALLED")
#     try:
#         if 'audio' not in request.files:
#             return jsonify({'error': 'No audio file provided'}), 400
#         audio_file = request.files['audio']
#
#         audio_data = audio_file.read()
#         print("Received audio file:", audio_file.filename)
#         print("Audio file size:", len(audio_data))
#         audio_file.seek(0)  # Reset pointer for further operations
#
#         if len(audio_data) == 0:
#             return jsonify({'error': 'Received empty audio file'}), 400
#
#         if not voice_processor.is_available()['whisper']:
#             return jsonify({'error': 'Voice processing not available'}), 503
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
#             audio_file.save(temp_file.name)
#             temp_path = temp_file.name
#             logger.info(f"Saved audio file: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
#         try:
#             result = voice_processor.transcribe(temp_path)
#             logger.info(f"Transcription successful: {result['text'][:50]}...")
#             return jsonify({
#                 'success': True,
#                 'transcription': result['text'],
#                 'confidence': result['confidence'],
#                 'processing_time': result['processing_time'],
#                 'language': result.get('language', 'en')
#             })
#         finally:
#             os.unlink(temp_path)
#     except Exception as e:
#         logger.error(f"Transcription error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/voice-respond', methods=['POST'])
# def voice_respond():
#     try:
#         data = request.get_json()
#         user_message = data.get('message', '')
#         conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
#         if not user_message:
#             return jsonify({'error': 'No message provided'}), 400
#         ai_response = career_explorer.get_response(user_message, conversation_id)
#         ai_message = ai_response.get('message', '')
#         if not ai_message or not ai_message.strip():
#             logger.error(f"AI returned blank response for user: {user_message}")
#             return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200
#
#         voice_processor.speak(ai_message)
#         save_conversation_turn(conversation_id, user_message, ai_message)
#         logger.info(f"AI Response: {ai_message[:50]}...")
#         return jsonify({
#             'success': True,
#             'ai_response': ai_message,
#             'should_continue': ai_response['should_continue'],
#             'conversation_stage': ai_response['stage'],
#             'student_name': ai_response['student_name'],
#             'notes': ai_response['notes'],
#             'conversation_id': conversation_id
#         })
#
#     except Exception as e:
#         logger.error(f"Voice response error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/voice-conversation', methods=['POST'])
# def voice_conversation():
#     try:
#         if 'audio' not in request.files:
#             return jsonify({'error': 'No audio file provided'}), 400
#         audio_file = request.files['audio']
#
#         audio_data = audio_file.read()
#         print("Received audio file:", audio_file.filename)
#         print("Audio file size:", len(audio_data))
#         audio_file.seek(0)
#
#         if len(audio_data) == 0:
#             return jsonify({'error': 'Received empty audio file'}), 400
#
#         conversation_id = request.form.get('conversation_id', f'conv_{int(time.time())}')
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
#             audio_file.save(temp_file.name)
#             temp_path = temp_file.name
#         try:
#             transcription_result = voice_processor.transcribe(temp_path)
#             user_message = transcription_result['text']
#             if not user_message.strip():
#                 return jsonify({'success': False, 'error': 'No speech detected'}), 200
#             ai_response = career_explorer.get_response(user_message, conversation_id)
#             ai_message = ai_response.get('message', '')
#             if not ai_message or not ai_message.strip():
#                 logger.error(f"AI returned blank response for user: {user_message}")
#                 return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200
#
#             voice_processor.speak(ai_message)
#             save_conversation_turn(conversation_id, user_message, ai_message)
#             logger.info(f"AI Response: {ai_message[:50]}...")
#             return jsonify({
#                 'success': True,
#                 'ai_response': ai_message,
#                 'should_continue': ai_response['should_continue'],
#                 'conversation_stage': ai_response['stage'],
#                 'student_name': ai_response['student_name'],
#                 'notes': ai_response['notes'],
#                 'conversation_id': conversation_id
#             })
#
#         finally:
#             os.unlink(temp_path)
#     except Exception as e:
#         logger.error(f"Voice conversation error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/conversations')
# def get_conversations():
#     try:
#         conversations_file = 'data/conversations.json'
#         if not os.path.exists(conversations_file):
#             return jsonify([])
#         with open(conversations_file, 'r') as f:
#             all_conversations = json.load(f)
#         summaries = []
#         for conv_id, conv_data in all_conversations.items():
#             user_messages = [m for m in conv_data.get('messages', []) if m['role'] == 'user']
#             summaries.append({
#                 'id': conv_id,
#                 'created_at': conv_data.get('created_at'),
#                 'message_count': len(conv_data.get('messages', [])),
#                 'user_message_count': len(user_messages),
#                 'student_name': conv_data.get('student_name', 'Unknown'),
#                 'stage': conv_data.get('stage', 'unknown'),
#                 'last_updated': conv_data.get('last_updated'),
#                 'notes': conv_data.get('notes', [])
#             })
#         summaries.sort(key=lambda x: x.get('last_updated', x.get('created_at', '')), reverse=True)
#         return jsonify(summaries)
#     except Exception as e:
#         logger.error(f"Get conversations error: {e}")
#         return jsonify([])
#
# @app.route('/api/generate-career-plan', methods=['POST'])
# def generate_career_plan():
#     try:
#         data = request.get_json()
#         conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
#         conversations_file = 'data/conversations.json'
#         if not os.path.exists(conversations_file):
#             return jsonify({'error': 'No conversation data found'}), 404
#         with open(conversations_file, 'r') as f:
#             conversations = json.load(f)
#         if conversation_id not in conversations:
#             return jsonify({'error': 'Conversation not found'}), 404
#         conv_data = conversations[conversation_id]
#         user_messages = [m['content'] for m in conv_data.get('messages', []) if m['role'] == 'user']
#         notes = conv_data.get('notes', [])
#         SYSTEM_PROMPT = (
#             "You are a career guidance expert. Write a personalized career plan for the student below, based on their profile and conversation. "
#             "Make it engaging, age-appropriate, and actionable. Use clear, friendly language. Always include a title and a 300-word plan."
#         )
#
#         # Compose the full prompt for Gemini
#         full_prompt = (
#             f"{SYSTEM_PROMPT}\n\n"
#             f"Student Name: {conv_data.get('student_name', 'Student')}\n"
#             f"Conversation Inputs: {user_messages}\n"
#             f"Notes: {notes}\n"
#         )
#
#         response = gemini_model.generate_content(full_prompt)
#
#         plan = response.text.strip() if hasattr(response, "text") else "Sample Career Plan: Explore interests like science and develop skills over 5 years!"
#         return jsonify({
#             'success': True,
#             'title': 'Career Plan for ' + (conv_data.get('student_name', 'Student')),
#             'plan': plan,
#             'word_count': len(plan.split())
#         })
#     except Exception as e:
#         logger.error(f"Career plan generation error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# def save_conversation_turn(conversation_id, user_message, ai_message):
#     try:
#         conversations_file = 'data/conversations.json'
#         if os.path.exists(conversations_file):
#             with open(conversations_file, 'r') as f:
#                 conversations = json.load(f)
#         else:
#             conversations = {}
#         if conversation_id not in conversations:
#             conversations[conversation_id] = {
#                 'created_at': datetime.now().isoformat(),
#                 'messages': [],
#                 'notes': [],
#                 'student_name': None,
#                 'stage': 'reconnection'
#             }
#         conversations[conversation_id]['messages'].extend([
#             {'role': 'user', 'content': user_message, 'timestamp': datetime.now().isoformat()},
#             {'role': 'assistant', 'content': ai_message, 'timestamp': datetime.now().isoformat()}
#         ])
#         if not conversations[conversation_id]['student_name']:
#             name = extract_name_from_message(user_message)
#             if name:
#                 conversations[conversation_id]['student_name'] = name
#         conversations[conversation_id]['last_updated'] = datetime.now().isoformat()
#         conversations[conversation_id]['message_count'] = len(conversations[conversation_id]['messages'])
#         with open(conversations_file, 'w') as f:
#             json.dump(conversations, f, indent=2)
#         logger.info(f"Conversation saved: {conversation_id}")
#     except Exception as e:
#         logger.error(f"Error saving conversation: {e}")
#
# def extract_name_from_message(message):
#     patterns = [r"my name is (\w+)", r"i'm (\w+)", r"i am (\w+)", r"call me (\w+)", r"name's (\w+)", r"hello,? (?:i'm |my name is )?(\w+)", r"hi,? (?:i'm |my name is )?(\w+)"]
#     for pattern in patterns:
#         match = re.search(pattern, message.lower())
#         if match:
#             name = match.group(1).capitalize()
#             if name.lower() not in ['good', 'fine', 'well', 'okay', 'sure', 'yes', 'no']:
#                 return name
#     return None
#
# @app.errorhandler(404)
# def not_found(error):
#     return jsonify({'error': 'Endpoint not found'}), 404
#
# @app.errorhandler(500)
# def internal_error(error):
#     logger.error(f"Internal server error: {error}")
#     return jsonify({'error': 'Internal server error'}), 500
#
# @app.route('/')
# def index():
#     return redirect('/voice-chat')
#
# @app.route('/voice-chat')
# def voice_chat():
#     return send_from_directory('static', 'career_explorer.html')
#
# @app.route('/dashboard')
# def dashboard():
#     return send_from_directory('static', 'career_dashboard.html')
#
# @app.route('/static/<path:filename>')
# def static_files(filename):
#     return send_from_directory('static', filename)
#
# def initialize_career_explorer():
#     global career_explorer
#     from ai_chat import CareerExplorerAI
#     career_explorer = CareerExplorerAI()
#
# initialize_career_explorer()
#
# if __name__ == '__main__':
#     print("\n🎓 helloIVY Career Selector - Version 1.0")
#     print("=" * 60)
#     print(f"✅ Flask Server: Ready")
#     print(f"🎤 Voice Processing: {'Available' if voice_processor.is_available()['whisper'] else 'Limited (install: pip install openai-whisper torch)'}")
#     print(f"🤖 AI Chat: Gemini API Connected")
#     print(f"💾 Data Storage: Local JSON files")
#     print("")
#     print("🌐 Access your application:")
#     print("   🏠 Home: http://localhost:5000")
#     print("   🎤 Voice Chat: http://localhost:5000/voice-chat")
#     print("   📊 Dashboard: http://localhost:5000/dashboard")
#     print("")
#     if not voice_processor.is_available()['whisper']:
#         print("🎤 For voice processing:")
#         print("   pip install openai-whisper torch")
#         print("")
#     print("📋 Quick Dependencies Install:")
#     print("   pip install flask flask-cors openai-whisper torch requests google-generativeai")
#     print("")
#     print("🎯 Features:")
#     print("   • Fun voice-based career exploration")
#     print("   • Automatic speech-to-text transcription")
#     print("   • AI text-to-speech responses")
#     print("   • Notepad for career notes")
#     print("   • Career plan generation")
#     print("")
#     print("Press Ctrl+C to stop the server")
#     print("=" * 60)
#     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

# app.py - helloIVY Career Selector Application

from config import GEMINI_API_KEY, GEMINI_MODEL_NAME, WHISPER_MODEL_NAME, DEVICE
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

import os
import json
import tempfile
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS

from voice_processor import VoiceProcessor

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- Directory setup ---
os.makedirs('data', exist_ok=True)
os.makedirs('data/audio_temp', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('static', exist_ok=True)

# --- Voice Processor Initialization ---
try:
    voice_processor = VoiceProcessor(model_name=WHISPER_MODEL_NAME)
except Exception as e:
    logger.error(f"Failed to initialize VoiceProcessor: {e}")
    voice_processor = None

career_explorer = None  # Will be initialized later

# --- API Endpoints ---

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'voice_available': voice_processor.is_available()['whisper'] if voice_processor else False,
        'ai_available': career_explorer is not None,
        'version': '1.0.0',
        'features': {
            'speech_recognition': voice_processor.is_available()['whisper'] if voice_processor else False,
            'career_exploration': career_explorer is not None,
            'conversation_storage': True
        }
    })

@app.route('/api/voice-transcribe', methods=['POST'])
def voice_transcribe():
    logger.info("VOICE TRANSCRIBE ENDPOINT CALLED")
    try:
        if not voice_processor or not voice_processor.is_available()['whisper']:
            return jsonify({'error': 'Voice processing not available'}), 503

        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        audio_file = request.files['audio']

        audio_data = audio_file.read()
        print("Received audio file:", audio_file.filename)
        print("Audio file size:", len(audio_data))
        audio_file.seek(0)  # Reset pointer for further operations

        if len(audio_data) == 0:
            return jsonify({'error': 'Received empty audio file'}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
            logger.info(f"Saved audio file: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
        try:
            result = voice_processor.transcribe(temp_path)
            logger.info(f"Transcription successful: {result['text'][:50]}...")
            return jsonify({
                'success': True,
                'transcription': result['text'],
                'confidence': result['confidence'],
                'processing_time': result['processing_time'],
                'language': result.get('language', 'en')
            })
        finally:
            os.unlink(temp_path)
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-respond', methods=['POST'])
def voice_respond():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        if not career_explorer:
            return jsonify({'error': 'AI is not initialized.'}), 503
        ai_response = career_explorer.get_response(user_message, conversation_id)
        ai_message = ai_response.get('message', '')
        if not ai_message or not ai_message.strip():
            logger.error(f"AI returned blank response for user: {user_message}")
            return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200

        voice_processor.speak(ai_message)
        save_conversation_turn(conversation_id, user_message, ai_message)
        logger.info(f"AI Response: {ai_message[:50]}...")
        return jsonify({
            'success': True,
            'ai_response': ai_message,
            'should_continue': ai_response['should_continue'],
            'conversation_stage': ai_response['stage'],
            'student_name': ai_response['student_name'],
            'notes': ai_response['notes'],
            'conversation_id': conversation_id
        })

    except Exception as e:
        logger.error(f"Voice response error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-conversation', methods=['POST'])
def voice_conversation():
    try:
        if not voice_processor or not voice_processor.is_available()['whisper']:
            return jsonify({'error': 'Voice processing not available'}), 503
        if not career_explorer:
            return jsonify({'error': 'AI is not initialized.'}), 503

        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        audio_file = request.files['audio']

        audio_data = audio_file.read()
        print("Received audio file:", audio_file.filename)
        print("Audio file size:", len(audio_data))
        audio_file.seek(0)

        if len(audio_data) == 0:
            return jsonify({'error': 'Received empty audio file'}), 400

        conversation_id = request.form.get('conversation_id', f'conv_{int(time.time())}')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        try:
            transcription_result = voice_processor.transcribe(temp_path)
            user_message = transcription_result['text']
            if not user_message.strip():
                return jsonify({'success': False, 'error': 'No speech detected'}), 200
            ai_response = career_explorer.get_response(user_message, conversation_id)
            ai_message = ai_response.get('message', '')
            if not ai_message or not ai_message.strip():
                logger.error(f"AI returned blank response for user: {user_message}")
                return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200

            voice_processor.speak(ai_message)
            save_conversation_turn(conversation_id, user_message, ai_message)
            logger.info(f"AI Response: {ai_message[:50]}...")
            return jsonify({
                'success': True,
                'ai_response': ai_message,
                'should_continue': ai_response['should_continue'],
                'conversation_stage': ai_response['stage'],
                'student_name': ai_response['student_name'],
                'notes': ai_response['notes'],
                'conversation_id': conversation_id
            })

        finally:
            os.unlink(temp_path)
    except Exception as e:
        logger.error(f"Voice conversation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations')
def get_conversations():
    try:
        conversations_file = 'data/conversations.json'
        if not os.path.exists(conversations_file):
            return jsonify([])
        with open(conversations_file, 'r') as f:
            all_conversations = json.load(f)
        summaries = []
        for conv_id, conv_data in all_conversations.items():
            user_messages = [m for m in conv_data.get('messages', []) if m['role'] == 'user']
            summaries.append({
                'id': conv_id,
                'created_at': conv_data.get('created_at'),
                'message_count': len(conv_data.get('messages', [])),
                'user_message_count': len(user_messages),
                'student_name': conv_data.get('student_name', 'Unknown'),
                'stage': conv_data.get('stage', 'unknown'),
                'last_updated': conv_data.get('last_updated'),
                'notes': conv_data.get('notes', [])
            })
        summaries.sort(key=lambda x: x.get('last_updated', x.get('created_at', '')), reverse=True)
        return jsonify(summaries)
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        return jsonify([])

@app.route('/api/generate-career-plan', methods=['POST'])
def generate_career_plan():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
        conversations_file = 'data/conversations.json'
        if not os.path.exists(conversations_file):
            return jsonify({'error': 'No conversation data found'}), 404
        with open(conversations_file, 'r') as f:
            conversations = json.load(f)
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        conv_data = conversations[conversation_id]
        user_messages = [m['content'] for m in conv_data.get('messages', []) if m['role'] == 'user']
        notes = conv_data.get('notes', [])
        SYSTEM_PROMPT = (
            "You are a career guidance expert. Write a personalized career plan for the student below, based on their profile and conversation. "
            "Make it engaging, age-appropriate, and actionable. Use clear, friendly language. Always include a title and a 300-word plan."
        )

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Student Name: {conv_data.get('student_name', 'Student')}\n"
            f"Conversation Inputs: {user_messages}\n"
            f"Notes: {notes}\n"
        )

        response = gemini_model.generate_content(full_prompt)

        plan = response.text.strip() if hasattr(response, "text") else "Sample Career Plan: Explore interests like science and develop skills over 5 years!"
        return jsonify({
            'success': True,
            'title': 'Career Plan for ' + (conv_data.get('student_name', 'Student')),
            'plan': plan,
            'word_count': len(plan.split())
        })
    except Exception as e:
        logger.error(f"Career plan generation error: {e}")
        return jsonify({'error': str(e)}), 500

# --- Helper Functions ---

def save_conversation_turn(conversation_id, user_message, ai_message):
    try:
        conversations_file = 'data/conversations.json'
        if os.path.exists(conversations_file):
            with open(conversations_file, 'r') as f:
                conversations = json.load(f)
        else:
            conversations = {}
        if conversation_id not in conversations:
            conversations[conversation_id] = {
                'created_at': datetime.now().isoformat(),
                'messages': [],
                'notes': [],
                'student_name': None,
                'stage': 'reconnection'
            }
        conversations[conversation_id]['messages'].extend([
            {'role': 'user', 'content': user_message, 'timestamp': datetime.now().isoformat()},
            {'role': 'assistant', 'content': ai_message, 'timestamp': datetime.now().isoformat()}
        ])
        if not conversations[conversation_id]['student_name']:
            name = extract_name_from_message(user_message)
            if name:
                conversations[conversation_id]['student_name'] = name
        conversations[conversation_id]['last_updated'] = datetime.now().isoformat()
        conversations[conversation_id]['message_count'] = len(conversations[conversation_id]['messages'])
        with open(conversations_file, 'w') as f:
            json.dump(conversations, f, indent=2)
        logger.info(f"Conversation saved: {conversation_id}")
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

def extract_name_from_message(message):
    patterns = [r"my name is (\w+)", r"i'm (\w+)", r"i am (\w+)", r"call me (\w+)", r"name's (\w+)", r"hello,? (?:i'm |my name is )?(\w+)", r"hi,? (?:i'm |my name is )?(\w+)"]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            name = match.group(1).capitalize()
            if name.lower() not in ['good', 'fine', 'well', 'okay', 'sure', 'yes', 'no']:
                return name
    return None

# --- Flask Error Handlers and Routes ---

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/')
def index():
    return redirect('/voice-chat')

@app.route('/voice-chat')
def voice_chat():
    return send_from_directory('static', 'career_explorer.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('static', 'career_dashboard.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

def initialize_career_explorer():
    global career_explorer
    try:
        from ai_chat import CareerExplorerAI
        career_explorer = CareerExplorerAI()
        logger.info("✅ CareerExplorerAI initialized")
    except Exception as e:
        logger.error(f"Failed to initialize CareerExplorerAI: {e}")
        career_explorer = None

initialize_career_explorer()

if __name__ == '__main__':
    print("\n🎓 helloIVY Career Selector - Version 1.0")
    print("=" * 60)
    print(f"✅ Flask Server: Ready")
    print(f"🎤 Voice Processing: {'Available' if (voice_processor and voice_processor.is_available()['whisper']) else 'Limited (install: pip install openai-whisper torch)'}")
    print(f"🤖 AI Chat: Gemini API Connected")
    print(f"💾 Data Storage: Local JSON files")
    print("")
    print("🌐 Access your application:")
    print("   🏠 Home: http://localhost:5000")
    print("   🎤 Voice Chat: http://localhost:5000/voice-chat")
    print("   📊 Dashboard: http://localhost:5000/dashboard")
    print("")
    if not voice_processor or not voice_processor.is_available()['whisper']:
        print("🎤 For voice processing:")
        print("   pip install openai-whisper torch")
        print("")
    print("📋 Quick Dependencies Install:")
    print("   pip install flask flask-cors openai-whisper torch requests google-generativeai")
    print("")
    print("🎯 Features:")
    print("   • Fun voice-based career exploration")
    print("   • Automatic speech-to-text transcription")
    print("   • AI text-to-speech responses")
    print("   • Notepad for career notes")
    print("   • Career plan generation")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)


# from config import GEMINI_API_KEY, GEMINI_MODEL_NAME, WHISPER_MODEL_NAME, DEVICE
# import google.generativeai as genai
#
# genai.configure(api_key=GEMINI_API_KEY)
# gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
#
# import os
# import json
# import tempfile
# import logging
# import re
# import time
# from datetime import datetime
# from flask import Flask, request, jsonify, send_from_directory, redirect
# from flask_cors import CORS
# from pydub import AudioSegment
#
# from voice_processor import VoiceProcessor
#
# # --- Logging setup ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
# app = Flask(__name__)
# CORS(app)
#
# # --- Directory setup ---
# os.makedirs('data', exist_ok=True)
# os.makedirs('data/audio_temp', exist_ok=True)
# os.makedirs('logs', exist_ok=True)
# os.makedirs('static', exist_ok=True)
#
# # --- Voice Processor Initialization ---
# try:
#     voice_processor = VoiceProcessor(model_name=WHISPER_MODEL_NAME)
# except Exception as e:
#     logger.error(f"Failed to initialize VoiceProcessor: {e}")
#     voice_processor = None
#
# career_explorer = None  # Will be initialized later
#
# # --- API Endpoints ---
#
# @app.route('/api/health')
# def health_check():
#     return jsonify({
#         'status': 'healthy',
#         'timestamp': datetime.now().isoformat(),
#         'voice_available': voice_processor.is_available()['whisper'] if voice_processor else False,
#         'ai_available': career_explorer is not None,
#         'version': '1.0.0',
#         'features': {
#             'speech_recognition': voice_processor.is_available()['whisper'] if voice_processor else False,
#             'career_exploration': career_explorer is not None,
#             'conversation_storage': True
#         }
#     })
#
# @app.route('/api/voice-transcribe', methods=['POST'])
# def voice_transcribe():
#     logger.info("VOICE TRANSCRIBE ENDPOINT CALLED")
#     try:
#         if not voice_processor or not voice_processor.is_available()['whisper']:
#             return jsonify({'error': 'Voice processing not available'}), 503
#
#         if 'audio' not in request.files:
#             return jsonify({'error': 'No audio file provided'}), 400
#         audio_file = request.files['audio']
#
#         audio_data = audio_file.read()
#         logger.info(f"Received audio file: {audio_file.filename}, size: {len(audio_data)} bytes")
#         audio_file.seek(0)
#
#         if len(audio_data) == 0:
#             return jsonify({'error': 'Received empty audio file'}), 400
#
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
#             audio_file.save(temp_file.name)
#             temp_path = temp_file.name
#             logger.info(f"Saved audio file: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
#             try:
#                 audio = AudioSegment.from_file(temp_path)
#                 logger.info(f"Audio details - sample_rate: {audio.frame_rate}, channels: {audio.channels}, duration: {audio.duration_seconds}s")
#             except Exception as e:
#                 logger.error(f"Audio metadata error: {e}")
#         try:
#             result = voice_processor.transcribe(temp_path)
#             logger.info(f"Transcription successful: {result['text'][:50]}...")
#             return jsonify({
#                 'success': True,
#                 'transcription': result['text'],
#                 'confidence': result['confidence'],
#                 'processing_time': result['processing_time'],
#                 'language': result.get('language', 'en')
#             })
#         finally:
#             # os.unlink(temp_path)  # Commented for debugging
#             logger.info(f"Preserved temp file for debugging: {temp_path}")
#     except Exception as e:
#         logger.error(f"Transcription error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/voice-respond', methods=['POST'])
# def voice_respond():
#     try:
#         data = request.get_json()
#         user_message = data.get('message', '')
#         conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
#         if not user_message:
#             return jsonify({'error': 'No message provided'}), 400
#         if not career_explorer:
#             return jsonify({'error': 'AI is not initialized.'}), 503
#         ai_response = career_explorer.get_response(user_message, conversation_id)
#         ai_message = ai_response.get('message', '')
#         if not ai_message or not ai_message.strip():
#             logger.error(f"AI returned blank response for user: {user_message}")
#             return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200
#
#         voice_processor.speak(ai_message)
#         save_conversation_turn(conversation_id, user_message, ai_message, ai_response['notes'])
#         logger.info(f"AI Response: {ai_message[:50]}...")
#         return jsonify({
#             'success': True,
#             'ai_response': ai_message,
#             'should_continue': ai_response['should_continue'],
#             'conversation_stage': ai_response['stage'],
#             'student_name': ai_response['student_name'],
#             'notes': ai_response['notes'],
#             'conversation_id': conversation_id
#         })
#     except Exception as e:
#         logger.error(f"Voice response error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/voice-conversation', methods=['POST'])
# def voice_conversation():
#     try:
#         if not voice_processor or not voice_processor.is_available()['whisper']:
#             return jsonify({'error': 'Voice processing not available'}), 503
#         if not career_explorer:
#             return jsonify({'error': 'AI is not initialized.'}), 503
#
#         if 'audio' not in request.files:
#             return jsonify({'error': 'No audio file provided'}), 400
#         audio_file = request.files['audio']
#
#         audio_data = audio_file.read()
#         logger.info(f"Received audio file: {audio_file.filename}, size: {len(audio_data)} bytes")
#         audio_file.seek(0)
#
#         if len(audio_data) == 0:
#             return jsonify({'error': 'Received empty audio file'}), 400
#
#         conversation_id = request.form.get('conversation_id', f'conv_{int(time.time())}')
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
#             audio_file.save(temp_file.name)
#             temp_path = temp_file.name
#             logger.info(f"Saved audio file: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
#             try:
#                 audio = AudioSegment.from_file(temp_path)
#                 logger.info(f"Audio details - sample_rate: {audio.frame_rate}, channels: {audio.channels}, duration: {audio.duration_seconds}s")
#             except Exception as e:
#                 logger.error(f"Audio metadata error: {e}")
#         try:
#             transcription_result = voice_processor.transcribe(temp_path)
#             user_message = transcription_result['text']
#             if not user_message.strip():
#                 return jsonify({'success': False, 'error': 'No speech detected'}), 200
#             ai_response = career_explorer.get_response(user_message, conversation_id)
#             ai_message = ai_response.get('message', '')
#             if not ai_message or not ai_message.strip():
#                 logger.error(f"AI returned blank response for user: {user_message}")
#                 return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200
#
#             voice_processor.speak(ai_message)
#             save_conversation_turn(conversation_id, user_message, ai_message, ai_response['notes'])
#             logger.info(f"AI Response: {ai_message[:50]}...")
#             return jsonify({
#                 'success': True,
#                 'ai_response': ai_message,
#                 'should_continue': ai_response['should_continue'],
#                 'conversation_stage': ai_response['stage'],
#                 'student_name': ai_response['student_name'],
#                 'notes': ai_response['notes'],
#                 'conversation_id': conversation_id
#             })
#         finally:
#             # os.unlink(temp_path)  # Commented for debugging
#             logger.info(f"Preserved temp file for debugging: {temp_path}")
#     except Exception as e:
#         logger.error(f"Voice conversation error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/conversations')
# def get_conversations():
#     try:
#         conversations_file = 'data/conversations.json'
#         if not os.path.exists(conversations_file):
#             return jsonify([])
#         with open(conversations_file, 'r') as f:
#             all_conversations = json.load(f)
#         summaries = []
#         for conv_id, conv_data in all_conversations.items():
#             user_messages = [m for m in conv_data.get('messages', []) if m['role'] == 'user']
#             summaries.append({
#                 'id': conv_id,
#                 'created_at': conv_data.get('created_at'),
#                 'message_count': len(conv_data.get('messages', [])),
#                 'user_message_count': len(user_messages),
#                 'student_name': conv_data.get('student_name', 'Unknown'),
#                 'stage': conv_data.get('stage', 'unknown'),
#                 'last_updated': conv_data.get('last_updated'),
#                 'notes': conv_data.get('notes', [])
#             })
#         summaries.sort(key=lambda x: x.get('last_updated', x.get('created_at', '')), reverse=True)
#         return jsonify(summaries)
#     except Exception as e:
#         logger.error(f"Get conversations error: {e}")
#         return jsonify([])
#
# @app.route('/api/generate-career-plan', methods=['POST'])
# def generate_career_plan():
#     try:
#         data = request.get_json()
#         conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
#         conversations_file = 'data/conversations.json'
#         if not os.path.exists(conversations_file):
#             return jsonify({'error': 'No conversation data found'}), 404
#         with open(conversations_file, 'r') as f:
#             conversations = json.load(f)
#         if conversation_id not in conversations:
#             return jsonify({'error': 'Conversation not found'}), 404
#         conv_data = conversations[conversation_id]
#         user_messages = [m['content'] for m in conv_data.get('messages', []) if m['role'] == 'user']
#         notes = conv_data.get('notes', [])
#         SYSTEM_PROMPT = (
#             "You are a career guidance expert. Write a personalized career plan for the student below, based on their profile and conversation. "
#             "Make it engaging, age-appropriate, and actionable. Use clear, friendly language. Always include a title and a 300-word plan."
#         )
#
#         full_prompt = (
#             f"{SYSTEM_PROMPT}\n\n"
#             f"Student Name: {conv_data.get('student_name', 'Student')}\n"
#             f"Conversation Inputs: {user_messages}\n"
#             f"Notes: {notes}\n"
#         )
#
#         response = gemini_model.generate_content(full_prompt)
#
#         plan = response.text.strip() if hasattr(response, "text") else "Sample Career Plan: Explore interests like science and develop skills over 5 years!"
#         return jsonify({
#             'success': True,
#             'title': 'Career Plan for ' + (conv_data.get('student_name', 'Student')),
#             'plan': plan,
#             'word_count': len(plan.split())
#         })
#     except Exception as e:
#         logger.error(f"Career plan generation error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# # --- Helper Functions ---
#
# def save_conversation_turn(conversation_id, user_message, ai_message, notes):
#     try:
#         conversations_file = 'data/conversations.json'
#         if os.path.exists(conversations_file):
#             with open(conversations_file, 'r') as f:
#                 conversations = json.load(f)
#         else:
#             conversations = {}
#         if conversation_id not in conversations:
#             conversations[conversation_id] = {
#                 'created_at': datetime.now().isoformat(),
#                 'messages': [],
#                 'notes': [],
#                 'student_name': None,
#                 'stage': 'reconnection'
#             }
#         conversations[conversation_id]['messages'].extend([
#             {'role': 'user', 'content': user_message, 'timestamp': datetime.now().isoformat()},
#             {'role': 'assistant', 'content': ai_message, 'timestamp': datetime.now().isoformat()}
#         ])
#         conversations[conversation_id]['notes'] = notes  # Update notes directly
#         if not conversations[conversation_id]['student_name']:
#             name = extract_name_from_message(user_message)
#             if name:
#                 conversations[conversation_id]['student_name'] = name
#         conversations[conversation_id]['last_updated'] = datetime.now().isoformat()
#         conversations[conversation_id]['message_count'] = len(conversations[conversation_id]['messages'])
#         with open(conversations_file, 'w') as f:
#             json.dump(conversations, f, indent=2)
#         logger.info(f"Conversation saved: {conversation_id}, Notes: {notes}")
#     except Exception as e:
#         logger.error(f"Error saving conversation: {e}")
#
# def extract_name_from_message(message):
#     patterns = [r"my name is (\w+)", r"i'm (\w+)", r"i am (\w+)", r"call me (\w+)", r"name's (\w+)", r"hello,? (?:i'm |my name is )?(\w+)", r"hi,? (?:i'm |my name is )?(\w+)"]
#     for pattern in patterns:
#         match = re.search(pattern, message.lower())
#         if match:
#             name = match.group(1).capitalize()
#             if name.lower() not in ['good', 'fine', 'well', 'okay', 'sure', 'yes', 'no']:
#                 return name
#     return None
#
# # --- Flask Error Handlers and Routes ---
#
# @app.errorhandler(404)
# def not_found(error):
#     return jsonify({'error': 'Endpoint not found'}), 404
#
# @app.errorhandler(500)
# def internal_error(error):
#     logger.error(f"Internal server error: {error}")
#     return jsonify({'error': 'Internal server error'}), 500
#
# @app.route('/')
# def index():
#     return redirect('/voice-chat')
#
# @app.route('/voice-chat')
# def voice_chat():
#     return send_from_directory('static', 'career_explorer.html')
#
# @app.route('/dashboard')
# def dashboard():
#     return send_from_directory('static', 'career_dashboard.html')
#
# @app.route('/static/<path:filename>')
# def static_files(filename):
#     return send_from_directory('static', filename)
#
# def initialize_career_explorer():
#     global career_explorer
#     try:
#         from ai_chat import CareerExplorerAI
#         career_explorer = CareerExplorerAI()
#         logger.info("✅ CareerExplorerAI initialized")
#     except Exception as e:
#         logger.error(f"Failed to initialize CareerExplorerAI: {e}")
#         career_explorer = None
#
# initialize_career_explorer()
#
# if __name__ == '__main__':
#     print("\n🎓 helloIVY Career Selector - Version 1.0")
#     print("=" * 60)
#     print(f"✅ Flask Server: Ready")
#     print(f"🎤 Voice Processing: {'Available' if (voice_processor and voice_processor.is_available()['whisper']) else 'Limited (install: pip install openai-whisper torch)'}")
#     print(f"🤖 AI Chat: Gemini API Connected")
#     print(f"💾 Data Storage: Local JSON files")
#     print("")
#     print("🌐 Access your application:")
#     print("   🏠 Home: http://localhost:5000")
#     print("   🎤 Voice Chat: http://localhost:5000/voice-chat")
#     print("   📊 Dashboard: http://localhost:5000/dashboard")
#     print("")
#     if not voice_processor or not voice_processor.is_available()['whisper']:
#         print("🎤 For voice processing:")
#         print("   pip install openai-whisper torch")
#         print("")
#     print("📋 Quick Dependencies Install:")
#     print("   pip install flask flask-cors openai-whisper torch requests google-generativeai pydub")
#     print("")
#     print("🎯 Features:")
#     print("   • Fun voice-based career exploration")
#     print("   • Automatic speech-to-text transcription")
#     print("   • AI text-to-speech responses")
#     print("   • Notepad for career notes")
#     print("   • Career plan generation")
#     print("")
#     print("Press Ctrl+C to stop the server")
#     print("=" * 60)
#     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

# from config import GEMINI_API_KEY, GEMINI_MODEL_NAME, WHISPER_MODEL_NAME, DEVICE
# import google.generativeai as genai
#
# genai.configure(api_key=GEMINI_API_KEY)
# gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
#
# import os
# import json
# import tempfile
# import logging
# import re
# import time
# from datetime import datetime
# from flask import Flask, request, jsonify, send_from_directory, redirect
# from flask_cors import CORS
# from pydub import AudioSegment
#
# from voice_processor import VoiceProcessor
#
# # --- Logging setup ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
# app = Flask(__name__)
# CORS(app)
#
# # --- Directory setup ---
# os.makedirs('data', exist_ok=True)
# os.makedirs('data/audio_temp', exist_ok=True)
# os.makedirs('logs', exist_ok=True)
# os.makedirs('static', exist_ok=True)
#
# # --- Voice Processor Initialization ---
# try:
#     voice_processor = VoiceProcessor(model_name=WHISPER_MODEL_NAME)
# except Exception as e:
#     logger.error(f"Failed to initialize VoiceProcessor: {e}")
#     voice_processor = None
#
# career_explorer = None  # Will be initialized later
#
# # --- API Endpoints ---
#
# @app.route('/api/health')
# def health_check():
#     return jsonify({
#         'status': 'healthy',
#         'timestamp': datetime.now().isoformat(),
#         'voice_available': voice_processor.is_available()['whisper'] if voice_processor else False,
#         'ai_available': career_explorer is not None,
#         'version': '1.0.0',
#         'features': {
#             'speech_recognition': voice_processor.is_available()['whisper'] if voice_processor else False,
#             'career_exploration': career_explorer is not None,
#             'conversation_storage': True
#         }
#     })
#
# @app.route('/api/voice-transcribe', methods=['POST'])
# def voice_transcribe():
#     logger.info("VOICE TRANSCRIBE ENDPOINT CALLED")
#     try:
#         if not voice_processor or not voice_processor.is_available()['whisper']:
#             return jsonify({'error': 'Voice processing not available'}), 503
#
#         if 'audio' not in request.files:
#             return jsonify({'error': 'No audio file provided'}), 400
#         audio_file = request.files['audio']
#
#         audio_data = audio_file.read()
#         logger.info(f"Received audio file: {audio_file.filename}, size: {len(audio_data)} bytes")
#         audio_file.seek(0)
#
#         if len(audio_data) == 0:
#             return jsonify({'error': 'Received empty audio file'}), 400
#
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
#             audio_file.save(temp_file.name)
#             temp_path = temp_file.name
#             logger.info(f"Saved audio file: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
#             try:
#                 audio = AudioSegment.from_file(temp_path)
#                 logger.info(f"Audio details - sample_rate: {audio.frame_rate}, channels: {audio.channels}, duration: {audio.duration_seconds}s")
#             except Exception as e:
#                 logger.error(f"Audio metadata error: {e}")
#         try:
#             result = voice_processor.transcribe(temp_path)
#             logger.info(f"Transcription successful: {result['text'][:50]}...")
#             return jsonify({
#                 'success': True,
#                 'transcription': result['text'],
#                 'confidence': result['confidence'],
#                 'processing_time': result['processing_time'],
#                 'language': result.get('language', 'en')
#             })
#         finally:
#             # os.unlink(temp_path)  # Commented for debugging
#             logger.info(f"Preserved temp file for debugging: {temp_path}")
#     except Exception as e:
#         logger.error(f"Transcription error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/voice-respond', methods=['POST'])
# def voice_respond():
#     try:
#         data = request.get_json()
#         user_message = data.get('message', '')
#         conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
#         if not user_message:
#             return jsonify({'error': 'No message provided'}), 400
#         if not career_explorer:
#             return jsonify({'error': 'AI is not initialized.'}), 503
#         ai_response = career_explorer.get_response(user_message, conversation_id)
#         ai_message = ai_response.get('message', '')
#         if not ai_message or not ai_message.strip():
#             logger.error(f"AI returned blank response for user: {user_message}")
#             return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200
#
#         voice_processor.speak(ai_message)
#         save_conversation_turn(conversation_id, user_message, ai_message, ai_response['notes'])
#         logger.info(f"AI Response: {ai_message[:50]}...")
#         return jsonify({
#             'success': True,
#             'ai_response': ai_message,
#             'should_continue': ai_response['should_continue'],
#             'conversation_stage': ai_response['stage'],
#             'student_name': ai_response['student_name'],
#             'notes': ai_response['notes'],
#             'conversation_id': conversation_id
#         })
#     except Exception as e:
#         logger.error(f"Voice response error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/voice-conversation', methods=['POST'])
# def voice_conversation():
#     try:
#         if not voice_processor or not voice_processor.is_available()['whisper']:
#             return jsonify({'error': 'Voice processing not available'}), 503
#         if not career_explorer:
#             return jsonify({'error': 'AI is not initialized.'}), 503
#
#         if 'audio' not in request.files:
#             return jsonify({'error': 'No audio file provided'}), 400
#         audio_file = request.files['audio']
#
#         audio_data = audio_file.read()
#         logger.info(f"Received audio file: {audio_file.filename}, size: {len(audio_data)} bytes")
#         audio_file.seek(0)
#
#         if len(audio_data) == 0:
#             return jsonify({'error': 'Received empty audio file'}), 400
#
#         conversation_id = request.form.get('conversation_id', f'conv_{int(time.time())}')
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
#             audio_file.save(temp_file.name)
#             temp_path = temp_file.name
#             logger.info(f"Saved audio file: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
#             try:
#                 audio = AudioSegment.from_file(temp_path)
#                 logger.info(f"Audio details - sample_rate: {audio.frame_rate}, channels: {audio.channels}, duration: {audio.duration_seconds}s")
#             except Exception as e:
#                 logger.error(f"Audio metadata error: {e}")
#         try:
#             transcription_result = voice_processor.transcribe(temp_path)
#             user_message = transcription_result['text']
#             if not user_message.strip():
#                 return jsonify({'success': False, 'error': 'No speech detected'}), 200
#             ai_response = career_explorer.get_response(user_message, conversation_id)
#             ai_message = ai_response.get('message', '')
#             if not ai_message or not ai_message.strip():
#                 logger.error(f"AI returned blank response for user: {user_message}")
#                 return jsonify({'success': False, 'error': 'AI did not reply. Please try again.'}), 200
#
#             voice_processor.speak(ai_message)
#             save_conversation_turn(conversation_id, user_message, ai_message, ai_response['notes'])
#             logger.info(f"AI Response: {ai_message[:50]}...")
#             return jsonify({
#                 'success': True,
#                 'ai_response': ai_message,
#                 'should_continue': ai_response['should_continue'],
#                 'conversation_stage': ai_response['stage'],
#                 'student_name': ai_response['student_name'],
#                 'notes': ai_response['notes'],
#                 'conversation_id': conversation_id
#             })
#         finally:
#             # os.unlink(temp_path)  # Commented for debugging
#             logger.info(f"Preserved temp file for debugging: {temp_path}")
#     except Exception as e:
#         logger.error(f"Voice conversation error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# @app.route('/api/conversations')
# def get_conversations():
#     try:
#         conversations_file = 'data/conversations.json'
#         if not os.path.exists(conversations_file):
#             return jsonify([])
#         with open(conversations_file, 'r') as f:
#             all_conversations = json.load(f)
#         summaries = []
#         for conv_id, conv_data in all_conversations.items():
#             user_messages = [m for m in conv_data.get('messages', []) if m['role'] == 'user']
#             summaries.append({
#                 'id': conv_id,
#                 'created_at': conv_data.get('created_at'),
#                 'message_count': len(conv_data.get('messages', [])),
#                 'user_message_count': len(user_messages),
#                 'student_name': conv_data.get('student_name', 'Unknown'),
#                 'stage': conv_data.get('stage', 'unknown'),
#                 'last_updated': conv_data.get('last_updated'),
#                 'notes': conv_data.get('notes', [])
#             })
#         summaries.sort(key=lambda x: x.get('last_updated', x.get('created_at', '')), reverse=True)
#         return jsonify(summaries)
#     except Exception as e:
#         logger.error(f"Get conversations error: {e}")
#         return jsonify([])
#
# @app.route('/api/generate-career-plan', methods=['POST'])
# def generate_career_plan():
#     try:
#         data = request.get_json()
#         conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
#         conversations_file = 'data/conversations.json'
#         if not os.path.exists(conversations_file):
#             return jsonify({'error': 'No conversation data found'}), 404
#         with open(conversations_file, 'r') as f:
#             conversations = json.load(f)
#         if conversation_id not in conversations:
#             return jsonify({'error': 'Conversation not found'}), 404
#         conv_data = conversations[conversation_id]
#         user_messages = [m['content'] for m in conv_data.get('messages', []) if m['role'] == 'user']
#         notes = conv_data.get('notes', [])
#         SYSTEM_PROMPT = (
#             "You are a career guidance expert. Write a personalized career plan for the student below, based on their profile and conversation. "
#             "Make it engaging, age-appropriate, and actionable. Use clear, friendly language. Always include a title and a 300-word plan."
#         )
#
#         full_prompt = (
#             f"{SYSTEM_PROMPT}\n\n"
#             f"Student Name: {conv_data.get('student_name', 'Student')}\n"
#             f"Conversation Inputs: {user_messages}\n"
#             f"Notes: {notes}\n"
#         )
#
#         response = gemini_model.generate_content(full_prompt)
#
#         plan = response.text.strip() if hasattr(response, "text") else "Sample Career Plan: Explore interests like science and develop skills over 5 years!"
#         return jsonify({
#             'success': True,
#             'title': 'Career Plan for ' + (conv_data.get('student_name', 'Student')),
#             'plan': plan,
#             'word_count': len(plan.split())
#         })
#     except Exception as e:
#         logger.error(f"Career plan generation error: {e}")
#         return jsonify({'error': str(e)}), 500
#
# # --- Helper Functions ---
#
# def save_conversation_turn(conversation_id, user_message, ai_message, notes):
#     try:
#         conversations_file = 'data/conversations.json'
#         if os.path.exists(conversations_file):
#             with open(conversations_file, 'r') as f:
#                 conversations = json.load(f)
#         else:
#             conversations = {}
#         if conversation_id not in conversations:
#             conversations[conversation_id] = {
#                 'created_at': datetime.now().isoformat(),
#                 'messages': [],
#                 'notes': [],
#                 'student_name': None,
#                 'stage': 'reconnection'
#             }
#         conversations[conversation_id]['messages'].extend([
#             {'role': 'user', 'content': user_message, 'timestamp': datetime.now().isoformat()},
#             {'role': 'assistant', 'content': ai_message, 'timestamp': datetime.now().isoformat()}
#         ])
#         conversations[conversation_id]['notes'] = notes  # Update notes directly
#         if not conversations[conversation_id]['student_name']:
#             name = extract_name_from_message(user_message)
#             if name:
#                 conversations[conversation_id]['student_name'] = name
#         conversations[conversation_id]['last_updated'] = datetime.now().isoformat()
#         conversations[conversation_id]['message_count'] = len(conversations[conversation_id]['messages'])
#         with open(conversations_file, 'w') as f:
#             json.dump(conversations, f, indent=2)
#         logger.info(f"Conversation saved: {conversation_id}, Notes: {notes}")
#     except Exception as e:
#         logger.error(f"Error saving conversation: {e}")
#
# def extract_name_from_message(message):
#     patterns = [r"my name is (\w+)", r"i'm (\w+)", r"i am (\w+)", r"call me (\w+)", r"name's (\w+)", r"hello,? (?:i'm |my name is )?(\w+)", r"hi,? (?:i'm |my name is )?(\w+)"]
#     for pattern in patterns:
#         match = re.search(pattern, message.lower())
#         if match:
#             name = match.group(1).capitalize()
#             if name.lower() not in ['good', 'fine', 'well', 'okay', 'sure', 'yes', 'no']:
#                 return name
#     return None
#
# # --- Flask Error Handlers and Routes ---
#
# @app.errorhandler(404)
# def not_found(error):
#     return jsonify({'error': 'Endpoint not found'}), 404
#
# @app.errorhandler(500)
# def internal_error(error):
#     logger.error(f"Internal server error: {error}")
#     return jsonify({'error': 'Internal server error'}), 500
#
# @app.route('/')
# def index():
#     return redirect('/voice-chat')
#
# @app.route('/voice-chat')
# def voice_chat():
#     return send_from_directory('static', 'career_explorer.html')
#
# @app.route('/dashboard')
# def dashboard():
#     return send_from_directory('static', 'career_dashboard.html')
#
# @app.route('/static/<path:filename>')
# def static_files(filename):
#     return send_from_directory('static', filename)
#
# def initialize_career_explorer():
#     global career_explorer
#     try:
#         from ai_chat import CareerExplorerAI
#         print("AI Chat module imported successfully")
#         career_explorer = CareerExplorerAI()
#         logger.info("✅ CareerExplorerAI initialized")
#     except ImportError as e:
#         logger.error(f"Import error for CareerExplorerAI: {e}")
#         career_explorer = None
#     except Exception as e:
#         logger.error(f"Failed to initialize CareerExplorerAI: {e}")
#         career_explorer = None
#
# initialize_career_explorer()
#
# if __name__ == '__main__':
#     print("\n🎓 helloIVY Career Selector - Version 1.0")
#     print("=" * 60)
#     print(f"✅ Flask Server: Ready")
#     print(f"🎤 Voice Processing: {'Available' if (voice_processor and voice_processor.is_available()['whisper']) else 'Limited (install: pip install openai-whisper torch)'}")
#     print(f"🤖 AI Chat: Gemini API Connected" if career_explorer else f"🤖 AI Chat: Not initialized - check logs")
#     print(f"💾 Data Storage: Local JSON files")
#     print("")
#     print("🌐 Access your application:")
#     print("   🏠 Home: http://localhost:5000")
#     print("   🎤 Voice Chat: http://localhost:5000/voice-chat")
#     print("   📊 Dashboard: http://localhost:5000/dashboard")
#     print("")
#     if not voice_processor or not voice_processor.is_available()['whisper']:
#         print("🎤 For voice processing:")
#         print("   pip install openai-whisper torch")
#         print("")
#     print("📋 Quick Dependencies Install:")
#     print("   pip install flask flask-cors openai-whisper torch requests google-generativeai pydub")
#     print("")
#     print("🎯 Features:")
#     print("   • Fun voice-based career exploration")
#     print("   • Automatic speech-to-text transcription")
#     print("   • AI text-to-speech responses")
#     print("   • Notepad for career notes")
#     print("   • Career plan generation")
#     print("")
#     print("Press Ctrl+C to stop the server")
#     print("=" * 60)
#     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)