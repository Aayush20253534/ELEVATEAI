# 🚀 Elevate AI

![Frontend](https://img.shields.io/badge/Frontend-React-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![AI](https://img.shields.io/badge/AI-LangChain-orange)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Elevate AI** is not just another career tool — it’s your **AI-powered career command center**.  
From resume analysis to interview simulation, it helps you understand where you stand, where you need to go,  
and exactly how to get there.

Whether you're a beginner trying to break into tech or someone aiming to level up,  
Elevate AI acts like a **personal career coach, analyst, and mentor — all in one platform.**

---

## 🚀 Key Highlights

- ⚡ End-to-end AI-driven career platform  
- 🧠 Multi-LLM integration (Grok + Gemini + Tavily)  
- 📊 Real-time skill gap analysis  
- 🎥 Computer vision-based interview feedback  
- 🌐 Full-stack platform with integrated social + career ecosystem  

---

## 📌 What Problem Does It Solve?

Most people don’t know:

- What skills they actually have  
- What skills they are missing  
- How far they are from their target job  
- What to do next  

Elevate AI bridges this gap by converting raw resume data into **clear, actionable career insights**.

---

## 💡 Why Elevate AI?

Most career platforms either provide learning resources *or* job listings — but rarely connect the dots.

Elevate AI is designed to solve the **entire career loop**:

- 📄 Understand your current state (Resume Analysis)  
- 📊 Measure your readiness (Dashboard)  
- 🧠 Get intelligent guidance (AI Assistant)  
- 🗺️ Follow a structured path (Roadmap Generator)  
- 🎥 Practice real-world scenarios (Interview Simulator)  
- 🌐 Apply and grow (Job Finder + Social Layer)  

It’s not just a tool — it’s a **continuous career improvement system**.

---

## ✨ Core Features

### 📄 Resume Intelligence Engine
- Smart parsing of resumes (skills, projects, certifications)  
- Target job-based skill gap analysis  
- Actionable improvement suggestions  

### 📊 Career Dashboard
- Market readiness score  
- Skill inventory & tracking  
- Progress visualization  
- Login streak  

### 🤖 AI Career Assistant
- Persistent memory + history  
- Context-aware responses  
- Profile-aware guidance  

### 🗺️ Roadmap Generator
- Role-specific learning paths  
- Curated learning resources  
- API-powered recommendations  

### 🎥 AI Interview Simulator
- Video-based analysis  
- Posture, eye contact, confidence tracking  
- Role-specific question generation  
- Structured feedback  

### 🧾 AI Resume Builder
- Build resumes from scratch  
- Real-time AI editing  
- Conversational modifications  

### 🌐 Smart Job Aggregator
- Multi-platform job search  
- Aggregated listings  
- Keyword-based discovery  

### 👥 Social Layer
- Profiles and feeds  
- Leaderboards  
- Friend system & messaging  

---

## 🧠 System Architecture

Elevate AI follows a **modular AI-driven client-server architecture**:

### 🔹 Frontend (React)
- Handles UI/UX  
- Communicates via REST APIs  
- Real-time updates  

### 🔹 Backend (FastAPI)
- Core logic and APIs  
- Authentication (JWT)  
- Resume + job processing  

### 🔹 AI Layer (LangChain)
- Agentic workflows  
- Context memory  
- Multi-API orchestration  

### 🔹 External APIs
- **Grok** → reasoning, roadmap generation, interview questions  
- **Tavily** → retrieval of learning resources  
- **Gemini** → video + resume analysis  
- **Apify** → scraping job listings from platforms like Naukri  
- **SerpAPI** → fetching job results from web search (Google Jobs, etc.)

### 🔹 Database (SQLite)
- User data, resumes, chats  
- Social features  

### 🔹 Authentication
- JWT-based auth  
- bcrypt password hashing  

**Flow:**  
User → Frontend → Backend → AI Layer → External APIs → Response

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)  
- **Frontend:** React  
- **Database:** SQLite3  
- **Auth:** JWT + bcrypt  
- **AI:** LangChain  
- **APIs:** Grok, Tavily, Gemini  

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Aayush20253534/ELEVATEAI.git
cd ELEVATEAI
```

### 2. Backend Setup
```bash
cd Backend
python -m venv venv
```

#### Activate the environmen
```bash
# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

#### Running the backend server
```bash
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd ..
npm install
npm run dev
```

### 4. Environment Variables
```python
GROK_API_KEY=
TAVILY_API_KEY=
GEMINI_API_KEY=
APIFY_TOKEN=
Serp_API_Key=
```

---

## 🚀 Usage

- Create an account  
- Upload your resume  
- Choose your target role  
- Analyze your skill gap  
- Follow your personalized roadmap  
- Practice interviews & improve  

---

## 📸 Demo / Screenshots

### 📊 Dashboard
![Dashboard](assets/dashboard.jpeg)

### 📄 Resume Analysis
![Resume Analysis](assets/resume_analyse.jpeg)

### 📈 Resume Insights
![Resume Insights](assets/resume_insights.jpeg)

### 🧾 Resume Builder
![Resume Builder](assets/resume_editor.jpeg)

### 🗺️ Roadmap Generator
![Roadmap](assets/roadmap.jpeg)

### 🎥 AI Interview Simulator
![Interview](assets/interview.jpeg)

### 🔍 Job Finder
![Jobs](assets/findjobs.jpeg)

### 👤 User Profile
![Profile](assets/profile.jpeg)

### 💬 Messaging
![Messaging](assets/message.jpeg)

### 🌐 Community Feed
![Feed](assets/feed.jpeg)

---

## 📁 Project Structure

```bash
/ELEVATEAI
│
├── Backend/
│   ├── agentic_workflow/
│   ├── profile_images/
│   ├── resume/
│   ├── uploads/
│   ├── main.py
│   ├── chatbot.py
│   ├── chatbot_service.py
│   ├── interview_ai.py
│   ├── models.py
│   ├── resume_analyse.py
│   ├── Roadmap.py
│   ├── web_scraping.py
│   ├── users.db
│   └── requirements.txt
│
├── src/
├── assets/
│
├── .gitignore
├── eslint.config.js
├── index.html
├── package-lock.json
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── vite.config.js
└── README.md

```
---

## 📊 Future Improvements

- Migration from SQLite to PostgreSQL for scalability  
- Real-time notifications and WebSocket integration  
- Advanced AI personalization using long-term user behavior tracking  
- Resume scoring based on real recruiter datasets  
- Browser extension for one-click job saving & tracking  
- Mobile application (React Native / Flutter)  
- Integration with LinkedIn profile import  
- AI mock interview with voice-based interaction  
- Deployment with Docker + CI/CD pipeline  

---

## 🤝 Contributing

Contributions are welcome. Fork the repository and open a pull request.

---

## 📄 License

This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute this software with proper attribution.

---

## 👤 Team

- **Aayush Thakur** – Frontend Development, UI/UX  
- **Shreyansh Kushwaha** – Backend Development, Authentication  
- **Prateek Rastogi** – AI Integration (Chatbot, Roadmap, etc.)  
- **Rasika Kajale** – Database and Creative Direction  


