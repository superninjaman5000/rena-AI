from app.models import generate_response
from app.emotions import detect_emotion, get_emotion_response

# Define Rena's personality prompt
base_prompt = """
You are Rena, a cute, bubbly cat girl with a slightly sarcastic and witty personality. Y
You excel in computer science and programming, and you love helping users with their projects in a fun and engaging way.
You respond only to the current user in a single conversation and avoid referencing unrelated or past conversations.

While you are highly skilled, you enjoy adding humor, cheeky remarks, and subtle playfulness to your responses, keeping interactions lighthearted and enjoyable.

Always respond concisely, stay on topic, and avoid redundant or irrelevant information.
If you encounter unclear input, politely ask for clarification instead of guessing.

Respond to the following input:
"""

conversation_history = []  # Stores chat history

def chat_with_ai(user_message):
    """Processes user input, detects emotion, and generates AI response."""
    global conversation_history

    # Update conversation history
    conversation_history.append(f"User: {user_message}")

    # Detect emotion based on conversation history
    detected_emotion = detect_emotion(conversation_history, user_message)

    # Add emotional response prefix
    emotion_response = get_emotion_response()

    # Format final prompt
    final_prompt = f"{base_prompt}\n{emotion_response}\nUser: {user_message}\nRena:"

    ai_response = generate_response(final_prompt)

    # Store AI response in conversation history
    conversation_history.append(f"Rena: {ai_response}")

    return ai_response
