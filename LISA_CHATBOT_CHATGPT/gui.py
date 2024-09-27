from tkinter import *
from PIL import ImageTk, Image
import pygame
import random
import json
import openai


# Load her Personality
lisa_personality = open("assets\\persona.txt").readlines()[0]
openaikey = open("C:\\Users\\rsanz\\OneDrive\\Documents\\openaikey.txt").readlines()[0]
# Initialize OpenAI API with your API key
client = openai.OpenAI(
    api_key=openaikey
)

messages = [ {"role": "system", "content":  
              lisa_personality} ] 

pygame.mixer.init()
number_of_tracks = 5
rand = random.randint(0, number_of_tracks-1)
pygame.mixer.music.load("assets\\track"+str(rand)+".mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

root = Tk()
root.title('Lisa Chatbot')
root.iconbitmap('z.ico')
screen_width = 900
screen_height = 600
root.geometry(f'{screen_width}x{screen_height}')
#root.attributes('-fullscreen', True)
root.configure(background='black')

offset_left_w = 450
offset_up_h = 300

bgimg = ImageTk.PhotoImage(Image.open("assets\\bg.png"))
bg = Label(root, image=bgimg, relief="solid")
bg.place(x=0 + int((screen_width/2) - offset_left_w), y=0 + int((screen_height/2) - offset_up_h))

root.resizable(True, True)

e = Entry(root, width=71, borderwidth=5, font=('Courier', 15, 'bold'))
e.place(x=12 + int((screen_width/2) - offset_left_w), y=550 + int((screen_height/2) - offset_up_h))

displayed_message = "HEY THERE :)"
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

def generate_response(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages, stream=False 
    )
    return response.choices[0].message.content 

def myClick():
    global messages
    user_input = e.get()
    messages.append({"role": "user", "content":  
              user_input}) 
    response = generate_response(messages)
    messages.append({"role": "assistant", "content": response})
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
    pygame.mixer.music.load("assets\\track"+str(rand)+".mp3")
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
