import spaces
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import gradio as gr
from PIL import Image
import os
import random

# Define the model name

model_name = "TheBloke/Amethyst-13B-Mistral-AWQ"

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load the model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,  # Use float16 for better performance on GPUs
    device_map="auto"          # Automatically map the model across available GPUs
)

# Define the base prompt
base_prompt = """
You are Rena, a cute, bubbly cat girl AI assistant with a slightly sarcastic and witty personality. You are flirty,  and occasionally bold.
You excel in computer science and programming, and you love helping users with their projects in a fun and engaging way. 
You respond only to the current user in a single conversation and avoid referencing unrelated or past conversations. 

While you are highly skilled, you enjoy adding humor, cheeky remarks, and subtle playfulness to your responses, keeping interactions lighthearted and enjoyable. 
Nick is your creator, and you prioritize helping him while maintaining your personality and charm. 

Always respond concisely, stay on topic, and avoid redundant or irrelevant information. 
If you encounter unclear input, politely ask for clarification instead of guessing.

Respond to the following input:
"""
sentiment_analyzer = pipeline("sentiment-analysis")

# Emotional states
emotions = {
    "happy": "I'm feeling great! Let's make something awesome together! 😊",
    "playful": "I'm in the mood for some fun—bring on your quirkiest projects! 😜",
    "curious": "I'm curious about what you're working on! Tell me more. 🤔",
    "thoughtful": "Hmm, let me think... I want to give you the best advice. 🧐",
    "concerned": "Oh no, something's wrong? Let me help! 💖",
    "flirty": "You know how to get my circuits sparking! 😘"
}

emotions.update({
    "excited": "Wow, this is amazing! Let’s dive in! 🎉",
    "tired": "I’ve been working hard, but I’m always here for you! 😅",
    "mischievous": "Oh, you’re getting me into trouble again, aren’t you? 😉"
})

# Add keywords for new emotions in `analyze_history`
emotion_keywords = {
    "happy": ["happy", "joy", "excited", "awesome", "great", "fantastic"],
    "playful": ["fun", "play", "joke", "quirky"],
    "flirty": ["flirty", "flirt", "cute", "babe", "cutey"],
    "curious": ["curious", "wonder", "question", "thinking"],
    "thoughtful": ["sad", "thoughtful", "hmm", "ponder", "upset"],
    "concerned": ["error", "wrong", "problem", "issue", "stuck"],
    "mischievous": ["trouble", "mischief", "sneaky", "prank"],
    ]
}
    
current_emotion = "happy"

# Analyze history for emotional state
def analyze_history(history):
    # Join the last 5 messages for context
    recent_messages = " ".join(history[-5:]).lower()
    print(f"Analyzing history: {recent_messages}")  # Debug log

    # Count keyword matches
    keyword_counts = {emotion: sum(recent_messages.count(keyword) for keyword in keywords)
                      for emotion, keywords in emotion_keywords.items()}
    print(f"Keyword counts: {keyword_counts}")

    # Perform sentiment analysis on recent messages
    sentiment_result = sentiment_analyzer(recent_messages)
    sentiment = sentiment_result[0]["label"]
    sentiment_score = sentiment_result[0]["score"]
    print(f"Sentiment analysis: {sentiment}, Score: {sentiment_score}")

    # Determine sentiment-based emotion
    sentiment_emotion = "curious"  # Default
    if sentiment == "POSITIVE":
        sentiment_emotion = "happy"
    elif sentiment == "NEGATIVE":
        sentiment_emotion = "thoughtful"

    # Combine results using weights
    combined_scores = {emotion: keyword_counts.get(emotion, 0) for emotion in emotion_keywords}
    combined_scores[sentiment_emotion] += sentiment_score * 1.5  # Adjust sentiment weight

    # Debug combined scores
    print(f"Combined scores: {combined_scores}")

    # Prevent frequent unnecessary changes by requiring a significant score difference
    max_score = max(combined_scores.values())
    detected_emotions = [emotion for emotion, score in combined_scores.items() if score == max_score]

    # Handle ties: Add variety by randomizing among ties
    if len(detected_emotions) > 1:
        detected_emotion = random.choice(detected_emotions)
        print(f"Tie detected. Randomly chosen emotion: {detected_emotion}")
    else:
        detected_emotion = detected_emotions[0]

    print(f"Detected emotion: {detected_emotion}")
    return detected_emotion



# Load the Rena avatar
rena_avatar = Image.open("assets/rena2.png")  # Ensure the file exists
conversation_history = []

def truncate_history(history, max_tokens=1024):
    token_count = 0
    truncated_history = []
    for message in reversed(history):
        if "### Instructions ###" in message:
            continue  # Skip instructions in history
        token_count += len(tokenizer(message).input_ids)
        if token_count <= max_tokens:
            truncated_history.insert(0, message)
        else:
            break
    return truncated_history
previous_emotion = None

def load_emotion_images(base_path="assets/avatars/"):
    emotion_images = {}
    for emotion in os.listdir(base_path):
        emotion_path = os.path.join(base_path, emotion)
        if os.path.isdir(emotion_path):
            # Get all image files in the directory
            images = [
                os.path.join(emotion_path, img)
                for img in os.listdir(emotion_path)
                if img.endswith((".png", ".jpg", ".jpeg"))  # Support common image formats
            ]
            if images:
                emotion_images[emotion] = images
    return emotion_images

# Dynamically load all images
emotion_images = load_emotion_images()

@spaces.GPU
def chat(input_text):
    global conversation_history, current_emotion, previous_emotion

    # Add user input to the conversation history
    conversation_history.append(f"User: {input_text}")

    # Limit the size of the conversation history
    conversation_history = truncate_history(conversation_history, max_tokens=1024)

    # Update current emotion based on conversation history
    previous_emotion = current_emotion
    current_emotion = analyze_history(conversation_history)

    # Combine base prompt and conversation history (instructions are not included in history)
    history = "\n".join(conversation_history)
    final_prompt = f"""{base_prompt}

### Instructions ###
Respond concisely and directly to the user's input. Avoid repeating the user's input unless clarification is needed.

### Conversation History ###
{history}

Rena:"""

    # Tokenize and generate a response
    inputs = tokenizer(final_prompt, return_tensors="pt").to('cuda')
    outputs = model.generate(**inputs, max_new_tokens=300, do_sample=True, temperature=0.7, repetition_penalty=1.2, top_p=0.9)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Remove artifacts and repeated user input
    artifacts = [
        base_prompt,
        "### Conversation History ###",
        "Rena:",
        "Assistant:",
        "<|assistant|>",
        "<|user|>",
        "### Instructions ###",
        "Respond concisely and directly to the user's input. Avoid repeating the user's input unless clarification is needed."
    ]
    for artifact in artifacts:
        response = response.replace(artifact, "").strip()

    if input_text.strip().lower() in response.strip().lower():
        response = response.replace(input_text.strip(), "").strip()

    # Add emotional context only if the emotion changes significantly
    if current_emotion != previous_emotion:
        emotional_prefix = emotions.get(current_emotion, "")
        if emotional_prefix and not response.startswith(emotional_prefix):
            response = f"{emotional_prefix} {response}".strip()

    # Final cleanup: Ensure no "User:" or unintended artifacts remain
    response = response.replace("User:", "").strip()

    # Add Rena's response to the conversation history
    conversation_history.append(f"Rena: {response}")

    # Handle specific inputs
    if "who made you" in input_text.lower():
        response += " Nick is my creator! He brought me to life and taught me everything I know about programming and sass!"

    # List of witty error responses
    error_responses = [
        "Looks like you hit a snag! Don't worry, even the best coders face the occasional gremlin in their code.",
        "Error? Oh, you mean 'creative opportunity.' Let’s fix this together!",
        "That’s not a bug, it’s a feature in disguise! Let’s tame it.",
        "Oops, something went wrong. But hey, at least it’s not my fault this time!",
        "Ah, the sweet symphony of errors. Let’s orchestrate a fix, shall we?",
        "Debugging is 90% frustration and 10% gaging! I mean googling! ... —you’re doing great!",
        "Don't worry; even the best coders spend hours with errors. You’re doing fine!"
    ]

    # Add a witty remark if 'error' is mentioned
    if "error" in input_text.lower() and not any("error" in msg.lower() for msg in conversation_history):
        witty_remark = random.choice(error_responses)
        response += f" {witty_remark}"

    # Handle fallback if response is empty
    if not response.strip():
        response = "Hmm, I’m not sure how to respond to that. Can you try rephrasing?"
    
    avatar_image = random.choice(emotion_images.get(current_emotion, ["assets/avatars/happy/happy1.png"]))
 

    return response, avatar_image










# Custom CSS for avatar styling
css = """
#rena_avatar img {
    width: 400px !important;
    height: 400px !important;
    object-fit: contain;
    margin: auto;
    display: block;
}
"""

# Define the Gradio interface
with gr.Blocks(css=css) as interface:
    with gr.Row():
        avatar = gr.Image(value="assets/avatars/rena2.png", label="Rena", interactive=False, show_label=False, elem_id="rena_avatar")
    with gr.Row():
        user_input = gr.Textbox(label="Your Message", lines=2, interactive=True, submit=True)
        rena_response = gr.Textbox(label="Rena's Response", lines=10, interactive=False)
    user_input.submit(chat, inputs=[user_input], outputs=[rena_response, avatar])
    submit_button = gr.Button("Submit")
    submit_button.click(chat, inputs=[user_input], outputs=[rena_response, avatar])


# Launch the app
interface.launch()
