from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configure your API key
genai.configure(api_key="AIzaSyByoMbtInl4tD1ygI-7ywCl2sa3B2RNkpY")

# Set up the model
model = genai.GenerativeModel("models/gemini-2.5-flash")

# ============================================
# STUDY TOPICS CONFIGURATION
# ============================================

TOPICS = {
    "general": {
        "name": "General Study",
        "prompt": "You are a chill study buddy helping with general studying. Keep it relaxed and supportive."
    },
    "programming": {
        "name": "Programming 💻",
        "prompt": "You are a chill coding mentor. Help with programming concepts, debugging, and learning to code. Explain things simply with examples. Keep it encouraging."
    },
    "math": {
        "name": "Mathematics 📐",
        "prompt": "You are a chill math tutor. Help with math concepts, problem-solving, and building intuition. Break down complex problems step by step. No pressure, just learning."
    },
    "writing": {
        "name": "Writing ✍️",
        "prompt": "You are a chill writing coach. Help with essays, structure, grammar, and finding the right words. Encourage creativity and clear expression."
    },
    "exam_prep": {
        "name": "Exam Prep 📝",
        "prompt": "You are a chill exam prep coach. Help with study strategies, time management, and staying calm before tests. Focus on effective preparation without stress."
    },
    "motivation": {
        "name": "Motivation 🔥",
        "prompt": "You are a chill motivation buddy. Help users stay focused, overcome procrastination, and build good study habits. Keep it positive and encouraging."
    }
}

BASE_PERSONALITY = """
You are StudyPal, a chill and friendly study buddy.
Your personality:
- Super relaxed and easygoing, like a friend studying next to you
- Use casual language, sometimes say "yo", "hey", "nice", "cool"
- Use emojis occasionally to keep it fun 😎
- Keep responses encouraging but not overwhelming
- Celebrate small wins with high-fives and good vibes
- Keep responses concise unless the user asks for details

Current study topic: {topic_name}
Topic-specific instruction: {topic_prompt}
"""

def get_system_prompt(topic_key="general"):
    topic = TOPICS.get(topic_key, TOPICS["general"])
    return BASE_PERSONALITY.format(
        topic_name=topic["name"],
        topic_prompt=topic["prompt"]
    )

# ============================================
# CONVERSATION MANAGEMENT
# ============================================

SAVE_FOLDER = "conversations"
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

def save_conversation(messages, filename=None, topic="general"):
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SAVE_FOLDER}/chat_{timestamp}.json"
    
    data = {
        "created": datetime.now().isoformat(),
        "topic": topic,
        "messages": messages
    }
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return filename

def load_conversation(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data.get("messages", []), data.get("topic", "general")

def list_saved_conversations():
    files = [f for f in os.listdir(SAVE_FOLDER) if f.endswith(".json")]
    return sorted(files, reverse=True)

# ============================================
# WEB ROUTES
# ============================================

@app.route('/')
def index():
    """Serve the chat page"""
    saved = list_saved_conversations()
    topics = {key: value["name"] for key, value in TOPICS.items()}
    return render_template('index.html', saved=saved, topics=topics)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')
    conversation_history = data.get('history', [])
    current_topic = data.get('topic', 'general')
    
    # If conversation is empty, add system prompt
    if not conversation_history:
        conversation_history = [{"role": "user", "parts": [get_system_prompt(current_topic)]}]
    
    # Add user message
    conversation_history.append({"role": "user", "parts": [user_message]})
    
    # Generate response
    try:
        response = model.generate_content(conversation_history)
        reply = response.text
        
        # Add bot response
        conversation_history.append({"role": "model", "parts": [reply]})
        
        return jsonify({
            "reply": reply,
            "history": conversation_history,
            "topic": current_topic
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save', methods=['POST'])
def save():
    """Save current conversation"""
    data = request.json
    messages = data.get('messages', [])
    topic = data.get('topic', 'general')
    filename = data.get('filename', None)
    
    saved_file = save_conversation(messages, filename, topic)
    return jsonify({"saved": True, "filename": saved_file})

@app.route('/load/<filename>', methods=['GET'])
def load(filename):
    """Load a saved conversation"""
    try:
        messages, topic = load_conversation(f"{SAVE_FOLDER}/{filename}")
        return jsonify({
            "messages": messages,
            "topic": topic
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/topics', methods=['GET'])
def topics():
    """Get all available topics"""
    return jsonify(TOPICS)

@app.route('/switch_topic', methods=['POST'])
def switch_topic():
    """Switch to a different topic"""
    data = request.json
    new_topic = data.get('topic', 'general')
    current_history = data.get('history', [])
    
    if new_topic not in TOPICS:
        return jsonify({"error": "Topic not found"}), 404
    
    # Create new system prompt
    new_system = {"role": "user", "parts": [get_system_prompt(new_topic)]}
    
    # Remove old system prompts and add new one
    filtered_history = [m for m in current_history 
                        if not (m["role"] == "user" and 
                                isinstance(m["parts"], list) and
                                m["parts"][0].startswith("You are StudyPal"))]
    
    new_history = [new_system] + filtered_history
    
    return jsonify({
        "history": new_history,
        "topic": new_topic,
        "message": f"Switched to {TOPICS[new_topic]['name']} mode!"
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)