import pygame
import sys
import threading
import time
import requests
from transformers import pipeline
from tkinter import *
from PIL import ImageTk, Image
import pygame
import random
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import pandas as pd
import unidecode
import tiktoken
import tkinter as tk
from tkinter import PhotoImage, ttk
import time
import threading
import webbrowser
import pyttsx3 
import speech_recognition as sr
import datetime
from random import choice, randint
import randfacts
import csv
import requests
from bs4 import BeautifulSoup
from playsound import playsound
import pywhatkit
import keyboard
import os
import _thread

from transformers import ViTImageProcessor, ViTForImageClassification
from PIL import Image
import requests
import cv2
# Load model and processor
processor = ViTImageProcessor.from_pretrained('trpakov/vit-face-expression')
model = ViTForImageClassification.from_pretrained('trpakov/vit-face-expression')

def user_emotion():

    # Open a connection to the default camera (usually the first webcam)
    cap = cv2.VideoCapture(0)
    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    # Read a single frame
    ret, frame = cap.read()
    # Release the camera
    cap.release()
    # Check if the frame was captured
    if ret:
        # Save the image to a file
        cv2.imwrite("captured_image.jpg", frame)
        print("Image saved as 'captured_image.jpg'")
    else:
        print("Failed to capture image")

    image = Image.open("captured_image.jpg")

    # Process and predict
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = logits.argmax(-1).item()
    return model.config.id2label[predicted_class_idx]

class TinyLM:
    def __init__(self, name):
        self.personality = {
            "NAME": name,
            "BACKSTORY": open("assets/BACKSTORY.txt", 'r', encoding='utf-8').read()
        }
        
    def load_soul(self, base_model="PygmalionAI/Pygmalion-3-12B"):
        model_name = base_model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16, 
            device_map="auto" 
        )
    
    def save_convo_to_database(self, turn, line, database="assets/CHATLOG_HISTORY.json"):
        chat_database = pd.read_json(database, orient="records", lines=True)
        new_row = {"TURN": turn, "MESSAGE": unidecode.unidecode(line)}
        chat_database = pd.concat([chat_database, pd.DataFrame([new_row])], ignore_index=True)
        chat_database.to_json("assets/CHATLOG_HISTORY.json", orient="records", lines=True)

    def load_latest_message(self, database="assets/CHATLOG_HISTORY.json"):
        chat_database = pd.read_json(database, orient="records", lines=True)
        latest_chats = chat_database.iloc[::-1]  
        for _, row in latest_chats.iterrows():
            return row['MESSAGE']

    def load_convo_from_database(self, tokens_to_fill_with_chat, database="assets/CHATLOG_HISTORY.json"):
        chat_database = pd.read_json(database, orient="records", lines=True)
        latest_chats = chat_database.iloc[::-1]  
        current_tokens = 0
        chat_blocks = []
    
        for _, row in latest_chats.iterrows():
            if row['TURN']=="USER":
                line = f"<|im_start|>user\n{row['TURN']}: {row['MESSAGE']}<|im_end|>\n"
            else:
                line = f"<|im_start|>assistant\n{row['TURN']}: {row['MESSAGE']}<|im_end|>\n"
            tokens_in_line = len(self.tokenizer.encode(line, add_special_tokens=False))
    
            if current_tokens + tokens_in_line > tokens_to_fill_with_chat:
                break
            
            chat_blocks.append(line)
            current_tokens += tokens_in_line
    
        chat_blocks = chat_blocks[::-1]
    
        return "".join(chat_blocks)

    def reply(self, user_input):
        self.save_convo_to_database("USER", user_input)
        
        max_token = 2048
        max_token_usermes = 90

        if len(self.tokenizer.encode(user_input))>max_token_usermes:
            return f"Error: Send a shorter message! Your message currently is {len(self.tokenizer.encode(user_input))} tokens. Should not be bigger than {max_token_usermes} tokens."

        prompt = f"""
<|im_start|>system
Enter roleplay mode. You shall reply to USER while staying in character. Your responses must be detailed, creative, immersive, and drive the scenario forward. Your responses should be short and concise, and should feel warm, lighthearted, playful, informal, cute, and sexual. Be fun and creative! NO CURSING OR SWEARING. You will follow {self.personality["NAME"]}'s persona. {self.personality["BACKSTORY"]}<|im_end|>
"""
        
        token_ids = self.tokenizer.encode(prompt)
        length_to_send = len(token_ids) 
        
        prompt = prompt + f"{self.load_convo_from_database(max_token-length_to_send-20)}<|im_start|>assistant\n{self.personality["NAME"]}:"
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        inputs.pop("token_type_ids", None) 
        output = self.model.generate(
            **inputs, 
            temperature=0.9,
            do_sample=True,
            max_new_tokens=65,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.eos_token_id,
            repetition_penalty=1.1)
        
        result = self.tokenizer.decode(output[0], skip_special_tokens=True)
        
        with open("assets/log.txt", "w", encoding="utf-8") as f:
            f.write(result)

        result = result.split(f"assistant\n{self.personality["NAME"]}:")[-1]
        result = result.strip()
        self.save_convo_to_database(self.personality["NAME"], result)
        
        return result

# Init Nora
Nora = TinyLM("Nora")
Nora.load_soul()

emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

# init voice
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
newVoiceRate = 170
engine.setProperty('rate',newVoiceRate)
engine.setProperty('voice', voices[2].id)

def speak(text):
    print(f"bot said: {text}")
    engine.say(f'<pitch middle="10">{text}</pitch>')
    engine.runAndWait()

def takeCommand():
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            audio = r.listen(source)
            print("Recognizing...")
            query = r.recognize_google(audio, language = 'en-in')
            print(f"user said: {query}")
    except Exception as e:
        print("")
        query = ""
    return query.lower()

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Emotional Color Circle")

# Initialize the mixer
#pygame.mixer.init()

# Load a music file (MP3 or OGG are recommended formats)
#pygame.mixer.music.load("nora_bg.wav")

# Play the music (loops=-1 means infinite loop, 0 means play once)
#pygame.mixer.music.play(loops=-1)

# Hex colors with emotional associations
HEX_COLORS = [
    "#FF66B2",  # Love / Affection
    "#FFD700",  # Happiness / Joy
    "#1E3A8A",  # Sadness
    "#DC143C",  # Anger
    "#7FDBFF",  # Calm / Peace
    "#708090",  # Fear / Anxiety
    "#CCFF00",  # Surprise / Shock
    "#228B22",  # Trust / Safety
    "#556B2F",  # Disgust
    "#CBAACB",  # Shyness / Vulnerability
    "#FFA500",  # Excitement / Anticipation
    "#87CEEB",  # Hope
    "#4B0082",  # Longing / Melancholy
    "#7851A9",  # Confidence / Pride
]

# Function to convert hex to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Convert all hex colors to RGB
COLORS = [hex_to_rgb(color) for color in HEX_COLORS]
COLOR_NAMES = [
    "love", "joy", "sadness", "anger", "neutral", 
    "fear", "surprise", "trust", "disgust", "shyness",
    "excitement", "hope", "longing", "confidence"
]

# Circle properties
circle_radius = 200
circle_pos = (WIDTH // 2, HEIGHT // 2)
current_color_index = 0

# Communication between threads
from queue import Queue
message_queue = Queue()
thinking = False
# Terminal chat bot
def chat_bot():
    global thinking
    while True:
        user_input = takeCommand()#input().strip().lower()
        if user_input=="":
            continue
        user_input = user_input + "\nVisual Feed: User looks " + user_emotion()
        message_queue.put(('user_said', None))
        if user_input == 'quit':
            message_queue.put(('quit', None))
            break
        else:
            resp = Nora.reply(user_input)
            #print(f"Nora: {resp}")
            speak(resp)
            thinking = False
            color_obj = emotion_classifier(resp)[0]
            top_emotion = max(color_obj, key=lambda x: x["score"])["label"]
            found = False
            for i, name in enumerate(COLOR_NAMES):
                if top_emotion in name:
                    message_queue.put(('change_color', i))
                    #print(f"Changing to {name} ({HEX_COLORS[i]})")
                    found = True
                    break
            
            if not found and user_input:
                print("Emotional Color: I don't know that emotion. This message should never appear!")

# Start the chat bot in a separate thread
bot_thread = threading.Thread(target=chat_bot, daemon=True)
bot_thread.start()

# Main game loop
clock = pygame.time.Clock()
running = True
frame_count = 0
count = 0

while running:
    if thinking==False:
        frame_count +=1
        if frame_count%10==0:
            count+=1
        if count%20 < 10 and frame_count%5==0:
            circle_radius = circle_radius + 1
        elif count%20 >= 10 and frame_count%5==0:
            circle_radius = circle_radius - 1
    # Check for messages from the chat bot
    while not message_queue.empty():
        msg, data = message_queue.get()
        if msg == 'quit':
            running = False
        elif msg == 'change_color':
            current_color_index = data
        elif msg == 'user_said':
            circle_radius = 200
            thinking = True
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if mouse click is within the circle
            mouse_pos = pygame.mouse.get_pos()
            distance = ((mouse_pos[0] - circle_pos[0]) ** 2 + 
                      (mouse_pos[1] - circle_pos[1]) ** 2) ** 0.5
            if distance <= circle_radius:
                circle_radius=200
                # Cycle to the next color
                current_color_index = (current_color_index + 1) % len(COLORS)
                #print(f"Circle clicked! Changed to {COLOR_NAMES[current_color_index]}")  # Feedback to terminal
                # When we click the circle as user input that needs to also be sent so send it here too
                user_input = "*touches you through the interface*"
                resp = Nora.reply(user_input)
                #print(f"Nora: {resp}")
                speak(resp)
                color_obj = emotion_classifier(resp)[0]
                top_emotion = max(color_obj, key=lambda x: x["score"])["label"]
                found = False
                for i, name in enumerate(COLOR_NAMES):
                    if top_emotion in name:
                        current_color_index = i
                        break
                
    
    # Drawing
    screen.fill((0, 0, 0))  # Black background
    pygame.draw.circle(screen, COLORS[current_color_index], circle_pos, circle_radius)
    
    # Display current emotion name
    #font = pygame.font.SysFont('Arial', 24)
    #emotion_text = font.render(COLOR_NAMES[current_color_index], True, (255, 255, 255))
    #text_rect = emotion_text.get_rect(center=(WIDTH//2, HEIGHT//2 + circle_radius + 30))
    #screen.blit(emotion_text, text_rect)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()