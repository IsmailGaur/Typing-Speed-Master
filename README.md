# ⌨️ Typing Speed Master 

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-Game%20Engine-orange)
![Status](https://img.shields.io/badge/status-Active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

> **Typing Speed Master** is an interactive, real-time typing game developed in **Python** using **Pygame**. It helps users practice and improve their typing speed and accuracy through a beautifully designed dark-mode interface with audio feedback and multiple paragraph challenges.

---

## Demo

Here’s a preview of the application:

### 🏠 Home Screen  
![Home UI](assets/Home-ui.png)

### 🧑‍💼 Manage Users  
![Manage Users](assets/manage%20users.png)

### ⌨️ Typing Box  
![Typing Box](assets/Typing%20Box.png)

### 🏁 Final Result  
![Result Screen](assets/result.png)

---

## ✨ Features

- 🟢 Real-time WPM and Accuracy calculation
- ⏱️ Countdown timer + session duration
- ✅ Character-level visual feedback:
  - Green = correct
  - Red = incorrect
  - Gray = remaining
- 🔀 Paragraph selector with multiple choices
- 📊 End result screen with all key metrics
- 🔁 Restart functionality
- 🔊 Sound feedback for typing, errors, and game completion
- 🧠 Tracks high and low scores locally
- 🌙 Clean, dark-mode UI

---

## 🛠 Tech Stack

- **Python 3.8+**
- **Pygame 2.x**
- JSON for local paragraph and score data

---

## 📁 Folder Structure
Typing-Speed-Master/
├── main.py # Game logic
├── paragraph.json # Paragraph bank
├── sentences.txt # Paragraphs text
├── scores.txt # High/low scores
├── users.json # User data (optional)
├── assets/
│ ├── Audio/ # Keypress and system sounds
│ ├── Home-ui.png
│ ├── manage users.png
│ ├── Typing Box.png
│ └── result.png
├── .gitignore
├── requirements.txt
└── README.md



 How WPM & Accuracy Are Calculated
WPM = (Correct Characters / 5) ÷ Minutes

Accuracy = (Correct Characters ÷ Total Typed) × 100

You’ll see a full report at the end showing:

 Words Per Minute

 Accuracy %

 Typing Errors

Total Time

High & Low Score


🙌 Special Thanks
Pygame – for the graphics and sound framework

Freesound.org – for royalty-free sounds
