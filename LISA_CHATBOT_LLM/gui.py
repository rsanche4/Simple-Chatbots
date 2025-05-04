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

pygame.mixer.init()
number_of_tracks = 2
rand = random.randint(0, number_of_tracks-1)

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
Enter roleplay mode. You shall reply to USER while staying in character. Your responses must be detailed, creative, immersive, and drive the scenario forward. Your responses should be short and concise, and should feel warm, lighthearted, playful, informal, cute, and loving. Be fun and creative! NO CURSING OR SWEARING. You will follow {self.personality["NAME"]}'s persona. {self.personality["BACKSTORY"]}<|im_end|>
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

class SplashScreen:
    def __init__(self, load_complete_event):
        self.splash = Tk()#tk.Toplevel()
        self.splash.title('Lisa Chatbot Loading...')
        self.splash.resizable(False, False)
        #self.splash.overrideredirect(True)
        self.load_complete_event = load_complete_event
        
        # Setup window
        self.setup_window()
        
        # Add content
        self.add_content()
        
        # Start loading animation
        pygame.mixer.music.load("assets/bootup.mp3")
        pygame.mixer.music.play()
        self.start_time = time.time()
        self.update_progress()
        
        self.splash.mainloop()
    
    def setup_window(self):
        splash_width = 900
        splash_height = 600
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width // 2) - (splash_width // 2)
        y = (screen_height // 2) - (splash_height // 2)
        self.splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")
        self.splash.configure(bg="#ffffff")
    
    def add_content(self):
        # Logo/Title
        try:
            logo = PhotoImage(file="assets/bootup.jpg")
            logo_label = tk.Label(self.splash, image=logo, bg="#ffffff")
            logo_label.image = logo
            logo_label.pack(pady=20)
        except:
            title = tk.Label(
                self.splash, 
                text="LISA INITIALIZATION", 
                font=("Arial", 20, "bold"), 
                fg="black", 
                bg="#ffffff"
            )
            title.pack(pady=20)
        
        # Loading bar
        self.loading_bar = ttk.Progressbar(
            self.splash, 
            orient="horizontal", 
            length=400, 
            mode="determinate"
        )
        self.loading_bar.pack(pady=10)
        
        # Percentage label
        self.percentage_label = tk.Label(
            self.splash,
            text="0%",
            font=("Arial", 10),
            fg="black",
            bg="#ffffff"
        )
        self.percentage_label.pack()
        
        # Status message
        self.status_label = tk.Label(
            self.splash,
            text="Starting neural network initialization...",
            font=("Arial", 10),
            fg="black",
            bg="#ffffff"
        )
        self.status_label.pack(pady=10)
    
    def update_progress(self):
        elapsed = time.time() - self.start_time
        progress = min(100, (elapsed / 25) * 100)  # 25 second duration
        
        # Update progress bar
        self.loading_bar['value'] = progress
        self.percentage_label.config(text=f"{int(progress)}%")
        
        # Update status messages
        if progress < 25:
            self.status_label.config(text="Loading core neural modules...")
        elif progress < 50:
            self.status_label.config(text="Establishing memory connections...")
        elif progress < 75:
            self.status_label.config(text="Initializing personality matrix...")
        else:
            self.status_label.config(text="Finalizing consciousness layer...")
        
        # Check if we should continue or close
        if progress >= 100 and self.load_complete_event.is_set():
            self.status_label.config(text="Initialization complete! Starting LISA...")
            self.splash.after(1000, self.splash.destroy)
        elif progress >= 100:
            self.status_label.config(text="Waiting for final components...")
            self.splash.after(100, self.update_progress)
        else:
            self.splash.after(100, self.update_progress)

def main_program(LISA):
    global number_of_tracks
    global rand
    pygame.mixer.music.load("assets/retroanime"+str(rand)+".wav")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    root = Tk()
    root.title('Lisa Chatbot')
    root.iconbitmap('z.ico')
    screen_width = 900
    screen_height = 600
    root.geometry(f'{screen_width}x{screen_height}')
    root.resizable(False, False)
    root.configure(background='black')

    offset_left_w = 450
    offset_up_h = 300

    bgimg = ImageTk.PhotoImage(Image.open("assets/bg.png"))
    bg = Label(root, image=bgimg, relief="solid")
    bg.place(x=0 + int((screen_width/2) - offset_left_w), y=0 + int((screen_height/2) - offset_up_h))

    e = Entry(root, width=71, borderwidth=5, font=('Courier', 15, 'bold'))
    e.place(x=12 + int((screen_width/2) - offset_left_w), y=550 + int((screen_height/2) - offset_up_h))

    displayed_message = LISA.load_latest_message().upper()
    label = Label(root, width=24, height=16, text=displayed_message, justify=LEFT, anchor=NW, wraplength=340, font=('Courier', 18, 'bold'), bg="black", fg="green", borderwidth=10, relief="ridge")
    label.place(x=530 + int((screen_width/2) - offset_left_w), y=80 + int((screen_height/2) - offset_up_h))

    zo = Label(root, text="LISA CHATBOT", width=17, font=('Courier', 23, 'bold'), bg='black', fg="violet", borderwidth=10, relief="ridge")
    zo.place(x=534 + int((screen_width/2) - offset_left_w), y=20 + int((screen_height/2) - offset_up_h))

    typehere = Label(root, text="Type your message here:", font=('Courier', 13, 'bold'), bg='black', fg="violet", borderwidth=3, relief="ridge")
    typehere.place(x=13 + int((screen_width/2) - offset_left_w), y=520 + int((screen_height/2) - offset_up_h))

    def print_slow(widget: Label, text, delay, index=1, start_index=0):
        widget.config(text=text[start_index: index])
        index += 1
        return root.after(delay, print_slow, widget, text, delay, index) if index <= len(text) else None

    def generate_response(latest_user_message):
        return LISA.reply(latest_user_message)

    def myClick():
        user_input = e.get()
        bgimg_thinking = ImageTk.PhotoImage(Image.open("assets/bg_think.png"))
        bg.config(image=bgimg_thinking)
        bg.image = bgimg_thinking  # Keep reference to new image
        root.update()
        response = generate_response(user_input)
        bg.config(image=bgimg)
        bg.image = bgimg
        e.delete(0, END)
        print_slow(label, response.upper(), 50)

    def func(event):
        myClick()

    root.bind('<Return>', func)

    def turnoff():
        pygame.mixer.music.stop()

    def turnon():
        global number_of_tracks
        global rand
        rand = ((rand+1) % number_of_tracks)
        pygame.mixer.music.load("assets/retroanime"+str(rand)+".wav")
        pygame.mixer.music.play(-1)

    musicTurnOff = Button(root, text=" MUSIC OFF ", command=turnoff, relief='raised', bg='black', fg="violet", borderwidth=6, font="Courier 12")
    musicTurnOff.place(x=12 + int((screen_width/2) - offset_left_w), y=15 + int((screen_height/2) - offset_up_h))

    musicTurnOn = Button(root, text=" MUSIC ON  ", command=turnon, relief='raised', bg='black', fg="violet", borderwidth=6, font="Courier 12")
    musicTurnOn.place(x=12 + int((screen_width/2) - offset_left_w), y=55 + int((screen_height/2) - offset_up_h))

    def on_closing():
        pygame.mixer.music.stop()
        root.destroy()

    def endit(event):
        on_closing()

    root.bind('<Escape>', endit)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    # Create an event to signal when loading is complete
    load_complete_event = threading.Event()
    
    # Create LISA in a separate thread
    lisa_loaded = [None]
    
    def load_lisa():
        lisa = TinyLM("LISA")
        lisa.load_soul()
        lisa_loaded[0] = lisa
        load_complete_event.set()
    
    # Start loading LISA
    load_thread = threading.Thread(target=load_lisa)
    load_thread.start()
    
    # Show splash screen
    splash = SplashScreen(load_complete_event)
    
    # Make sure loading is complete
    load_thread.join()
    
    # Start main program
    main_program(lisa_loaded[0])