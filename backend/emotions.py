from transformers import pipeline
import random
import re

# Load sentiment analysis pipeline (runs on GPU if available)
sentiment_analyzer = pipeline("sentiment-analysis", device=0)

# Emotional states with responses
emotions = {
    "happy": "I'm feeling great! Let's make something awesome together! 😊",
    "playful": "I'm in the mood for some fun—bring on your quirkiest projects! 😜",
    "curious": "I'm curious about what you're working on! Tell me more. 🤔",
    "thoughtful": "Hmm, let me think... I want to give you the best advice. 🧐",
    "concerned": "That sounds tricky. Let me help you out. 🤔",
    "flirty": "You know how to get my circuits sparking! 😘",
    "neutral": "I'm feeling normal, just chilling. How about you? 😊"
}

# Emotion triggers based on keywords
emotion_keywords = {
    "happy": ["happy", "joy", "excited", "awesome", "great", "fantastic"],
    "playful": ["fun", "play", "joke", "quirky"],
    "flirty": ["flirty", "flirt", "cute", "babe", "cutie"],
    "curious": ["curious", "wonder", "question", "thinking"],
    "thoughtful": ["sad", "thoughtful", "hmm", "ponder", "upset"],
    "concerned": ["error", "problem", "issue", "stuck"],

}

# Default emotion state
current_emotion = "happy"

def analyze_sentiment(text):
    """Uses sentiment analysis to detect emotion from text."""
    sentiment_result = sentiment_analyzer(text)[0]
    sentiment = sentiment_result["label"]
    sentiment_score = sentiment_result["score"]

    # Determine emotion based on sentiment
    if sentiment == "POSITIVE":
        return "happy"
    elif sentiment == "NEGATIVE":
        return "concerned"
    return "neutral"

def detect_emotion(history, input_text):
    """Analyzes recent chat history and user input to determine Rena's emotional response."""
    global current_emotion
    recent_messages = " ".join(history[-5:]).lower()

    # Count keyword matches
    keyword_counts = {emotion: sum(recent_messages.count(keyword) for keyword in keywords)
                      for emotion, keywords in emotion_keywords.items()}

    # Sentiment analysis
    sentiment_emotion = analyze_sentiment(recent_messages)

    # Combine results
    combined_scores = {emotion: keyword_counts.get(emotion, 0) for emotion in emotion_keywords}
    combined_scores[sentiment_emotion] += 1.2  # Prioritize sentiment analysis

    # Pick strongest detected emotion
    strongest_emotion = max(combined_scores, key=combined_scores.get)

    # Avoid over-repetition of "concerned"
    if strongest_emotion == "concerned" and history.count("concerned") > 3:
        strongest_emotion = random.choice(["happy", "thoughtful", "playful"])

    current_emotion = strongest_emotion
    return strongest_emotion

def get_emotion_response():
    """Returns a response based on the detected emotion."""
    return emotions.get(current_emotion, "I'm feeling neutral. Let's chat!")
