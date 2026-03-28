import google.generativeai as genai
import json
import os
from datetime import datetime

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

# ============================================
# CHATBOT PERSONALITY - The Chill Study Buddy
# ============================================

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
    """Generate the system prompt with current topic"""
    topic = TOPICS.get(topic_key, TOPICS["general"])
    return BASE_PERSONALITY.format(
        topic_name=topic["name"],
        topic_prompt=topic["prompt"]
    )

# ============================================
# CONVERSATION HISTORY MANAGEMENT
# ============================================

SAVE_FOLDER = "conversations"
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

def save_conversation(messages, filename=None, topic="general"):
    """Save conversation to a JSON file"""
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
    """Load a conversation from a JSON file"""
    with open(filename, "r") as f:
        data = json.load(f)
    return data.get("messages", []), data.get("topic", "general")

def list_saved_conversations():
    """List all saved conversation files"""
    files = [f for f in os.listdir(SAVE_FOLDER) if f.endswith(".json")]
    return sorted(files, reverse=True)

# ============================================
# COMMAND HANDLERS
# ============================================

def display_commands():
    """Show available commands"""
    print("\n" + "="*50)
    print("📋 STUDYPLAL COMMANDS")
    print("="*50)
    print("  /save          - Save current conversation")
    print("  /clear         - Clear conversation history")
    print("  /history       - Show conversation summary")
    print("  /topic         - Show available study topics")
    print("  /topic [name]  - Switch to a topic (e.g., /topic programming)")
    print("  /status        - Show current topic and stats")
    print("  /help          - Show this menu")
    print("  /exit          - Quit (auto-saves)")
    print("="*50 + "\n")

def show_topics():
    """Display available study topics"""
    print("\n📚 AVAILABLE STUDY TOPICS:")
    print("-"*40)
    for key, topic in TOPICS.items():
        print(f"  /topic {key:<12} - {topic['name']}")
    print("\n💡 Example: /topic programming\n")

def format_history_summary(messages):
    """Create a short summary of the conversation"""
    user_messages = []
    for m in messages:
        if m["role"] == "user" and isinstance(m["parts"], list):
            content = m["parts"][0] if m["parts"] else ""
            if content and not content.startswith("/topic"):
                user_messages.append(content)
    
    if not user_messages:
        return "No messages yet"
    
    summary = []
    for m in user_messages[:5]:
        text = m[:60] + "..." if len(m) > 60 else m
        summary.append(f"• {text}")
    
    if len(user_messages) > 5:
        summary.append(f"• ... and {len(user_messages) - 5} more messages")
    
    return "\n".join(summary)

def update_topic(conversation_history, topic_key, current_topic):
    """Switch to a new topic"""
    if topic_key not in TOPICS:
        print(f"\n❌ Topic '{topic_key}' not found. Type /topic to see available topics.\n")
        return conversation_history, current_topic
    
    # Keep only the system prompt from current history
    system_messages = [m for m in conversation_history 
                       if m["role"] == "user" and isinstance(m["parts"], list)
                       and m["parts"][0].startswith("You are StudyPal")]
    
    if not system_messages:
        # Create new system prompt
        new_system = {"role": "user", "parts": [get_system_prompt(topic_key)]}
    else:
        # Replace existing system prompt
        new_system = {"role": "user", "parts": [get_system_prompt(topic_key)]}
        conversation_history = [new_system] + [m for m in conversation_history 
                                                if not (m["role"] == "user" and 
                                                       isinstance(m["parts"], list) and
                                                       m["parts"][0].startswith("You are StudyPal"))]
    
    print(f"\n✅ Switched to {TOPICS[topic_key]['name']} mode!")
    print(f"   {TOPICS[topic_key]['prompt']}\n")
    
    return conversation_history, topic_key

# ============================================
# MAIN CHAT LOOP
# ============================================

def start_chat():
    """Start a new conversation"""
    print("\n" + "="*50)
    print("🎓 STUDYPLAL - Your Chill Study Buddy! 🎓")
    print("="*50)
    
    saved = list_saved_conversations()
    if saved:
        print("\n📁 Saved conversations found:")
        for i, file in enumerate(saved[:5]):
            # Try to show topic if available
            try:
                with open(f"{SAVE_FOLDER}/{file}", "r") as f:
                    data = json.load(f)
                    topic = data.get("topic", "general")
                    topic_name = TOPICS.get(topic, TOPICS["general"])["name"]
                    print(f"   {i+1}. {file} [{topic_name}]")
            except:
                print(f"   {i+1}. {file}")
        
        print(f"   {len(saved)+1}. Start a new conversation")
        choice = input("\nEnter number to load, or press Enter for new chat: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(saved):
            filename = f"{SAVE_FOLDER}/{saved[int(choice)-1]}"
            conversation_history, topic = load_conversation(filename)
            print(f"\n✅ Loaded conversation from {saved[int(choice)-1]}")
            print(f"   Current topic: {TOPICS.get(topic, TOPICS['general'])['name']}\n")
            return conversation_history, filename, topic
    
    # Start new conversation
    print("\n🆕 Starting a fresh conversation!")
    print("   Type /topic to see available study topics")
    print("   Type /help for all commands\n")
    
    initial_topic = "general"
    conversation_history = [{"role": "user", "parts": [get_system_prompt(initial_topic)]}]
    return conversation_history, None, initial_topic

# Start the chat
conversation_history, current_file, current_topic = start_chat()

print("💬 Start chatting! (Type /help for commands)\n")

while True:
    user_input = input("You: ").strip()
    
    if not user_input:
        continue
    
    # ============================================
    # COMMAND HANDLING
    # ============================================
    
    if user_input.lower() == "/exit":
        print("\n💾 Saving conversation...")
        saved_file = save_conversation(conversation_history, current_file, current_topic)
        print(f"✅ Saved to: {saved_file}")
        print("👋 Goodbye! Keep up the great studying! 🌟")
        break
    
    elif user_input.lower() == "/help":
        display_commands()
        continue
    
    elif user_input.lower() == "/save":
        saved_file = save_conversation(conversation_history, current_file, current_topic)
        print(f"💾 Conversation saved to: {saved_file}")
        continue
    
    elif user_input.lower() == "/clear":
        print("🔄 Clearing conversation history...")
        conversation_history = [{"role": "user", "parts": [get_system_prompt(current_topic)]}]
        print("✅ Conversation cleared! Starting fresh.\n")
        continue
    
    elif user_input.lower() == "/history":
        print("\n📜 CONVERSATION SUMMARY:")
        print(f"   Current Topic: {TOPICS[current_topic]['name']}")
        print(f"   Total messages: {len(conversation_history)}")
        print("\nRecent messages:")
        print(format_history_summary(conversation_history))
        print()
        continue
    
    elif user_input.lower() == "/topic":
        show_topics()
        continue
    
    elif user_input.lower() == "/status":
        print(f"\n📊 CURRENT STATUS:")
        print(f"   Topic: {TOPICS[current_topic]['name']}")
        print(f"   Messages in this session: {len(conversation_history)}")
        print(f"   Saved file: {current_file or 'Not saved yet'}")
        print()
        continue
    
    elif user_input.lower().startswith("/topic "):
        new_topic = user_input.split(" ", 1)[1].strip().lower()
        conversation_history, current_topic = update_topic(conversation_history, new_topic, current_topic)
        continue
    
    # ============================================
    # REGULAR CHAT
    # ============================================
    
    # Add user message
    conversation_history.append({"role": "user", "parts": [user_input]})
    
    # Generate response
    try:
        response = model.generate_content(conversation_history)
        reply = response.text
        
        print("\nStudyPal:", reply)
        print()
        
        # Add bot response
        conversation_history.append({"role": "model", "parts": [reply]})
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Try again or type /help for commands\n")