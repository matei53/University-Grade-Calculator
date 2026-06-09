# University-Grade-Calculator

A comprehensive full-stack application designed to help university students track, manage, and optimize their academic performance. The platform dynamically calculates grades and credit requirements while providing real-time visual progress bars to ensure students meet minimum benchmarks for yearly academic progression. Additionally, it integrates advanced AI-driven features, including an intelligent grade simulator and a personalized career advisor agent, to help students strategically plan their academic and professional journeys.

---

## 📐 Architecture & System Design

This project follows a clean, layered architecture separating the database models, business logic (services), API endpoints (routers), and frontend user interface.

### 1. Use Case Diagram
*It shows how the student interacts with the application tabs and how the AI agents communicate with external APIs.*

<img width="1085" height="1219" alt="Use diagram 1" src="https://github.com/user-attachments/assets/4aba0dbc-68e7-41aa-8921-ba9bd6046706" />


### 2. Class Diagram
*Illustrates the backend object-oriented structure, built with SQLAlchemy ORM models and dedicated static service layers.*

#### 🗄️ Database Environment Configuration
* **Production Environment:** Built using a robust **PostgreSQL** database. 
* **Testing & CI/CD Pipeline:** Used **SQLite** for testing. 

<img width="1583" height="1087" alt="Class diagram 2" src="https://github.com/user-attachments/assets/c1918c53-4331-47de-a4cd-ad110ee01959" />

---

## 🚀 How to Use the Application

Once you open UniGrade, you can easily navigate through your academic journey using the menu buttons at the top of the screen:

### 📊 Main Dashboard & Progress Tracking
* 📊 **Monitor Your Real Progress:** View your overall grade average and total credits on a live progress bar. **Crucial Rule:** Credits are only unlocked and added to your progress bar *after* you get a passing grade (5.0 or higher) in a subject!
* 📊 **Track Year Progression:** Check your eligibility status at a glance. The dashboard displays a clear `✓ ELIGIBLE` or `✗ NOT ELIGIBLE` badge so you know if you have passed enough classes to advance to the next university year.

### ⚙️ Academic Configuration & Data Management
* ⚙️ **Manage Subjects:** Go to the **Add Subject** screen to add your courses, input their credit values, and set custom passing or maximum grade scales. 
* ⚙️ **Log Assessments & Grades:** Break down each subject into individual components (like midterm exams, labs, or final projects). Assign percentage weights to each task, and the system will automatically calculate your final course average.
* ⚙️ **Set Progression Requirements:** Open the **Progression** settings screen to customize your advancement rules. Here, you can change the minimum credit percentage required to pass each year and toggle between single-year metrics or cumulative (rolling multi-year) calculations.

### 📊 Analytics & Community Standings
* 📊 **Leaderboard Tab:** Open the leaderboard to view class standings and see how your academic average stacks up against your peers. You can use the search bar to find friends, filter standings by university year, or toggle your own profile visibility on or off.

### ⚙️ Smart AI Assistants
* ⚙️ **Grade Simulator Tab:** Run predictive "what-if" scenarios. Simply type in your target GPA, select which upcoming or retakeable assignments you want to calculate, and the AI agent will tell you the exact scores you need to hit your goal.
* ⚙️ **Career Advisor Tab:** Head to your profile and click **Generate Career Guidance**. The built-in AI counselor will analyze your passed courses, strengths, and grades to build a personalized roadmap for your future internships and career choices.

---
## 🤖 AI Usage Report

This section outlines how Artificial Intelligence tools were leveraged throughout the Software Development Life Cycle (SDLC) to accelerate the design, implementation, and debugging of UniGrade.

### ⚙️ 1. AI Tool Roles
* **GitHub Copilot:** Used as an intelligent inline assistant for fast code autocompletion and writing quick PyQt6 frontend and FastAPI backend boilerplate.
* **Gemini:** Used as a high-level architectural consultant to design prompt engineering strategies for our AI agents, map out database schemas, and diagnose pipeline bugs.

### 📊 2. Frontend Development (PyQt6)
* **What the AI did:** Copilot quickly generated native desktop layout components, turning basic text forms into clean, organized `QFormLayout` and `QGridLayout` code blocks.
* **Where it failed:** The AI lacked spatial reasoning. It accidentally placed the **Delete Account** button directly over a panel border line. We had to manually rewrite the layout sequence, fix widget nesting, and inject `QSpacerItem` barriers to correct the visual layout.

### ⚙️ 3. Backend, CI/CD, and Debugging
* **What the AI did:** Cline automated our CRUD server endpoints, generating safe database query loops for creating, updating, and deleting academic data.
* **CI/CD Pipeline Fix:** When GitHub Actions automated tests crashed with a `ModuleNotFoundError: No module named 'PyQt6'`, Gemini diagnosed that the remote environment runner was trying to load frontend UI requirements during isolated backend tests. We then used Cline to swiftly rewrite file imports into absolute `server.` paths, repairing the pipeline.
* **Linter Compliance:** AI assisted in maintaining strict code hygiene, scanning for Flake8 errors and instantly fixing formatting oversights (such as replacing undefined catch variables with standard `{e}` exceptions).

### 📊 4. Core Feature Integration
* **Data Mapping:** We used AI to design clean mapping structures that convert complex PostgreSQL relational tables into plain Python dictionaries. This sanitized data is what gets passed safely into LangChain and our local Ollama framework to feed our background-threaded AI agents.

### ⚙️ 5. Key Limitations & Failures
* **Hallucinations:** AI assistants occasionally lost track of our codebase scope, inventing variables that did not exist. This led to multiple `NameError` bugs (such as referencing an undefined `raw_year` variable during database writes) which required manual code auditing.
* **Pathing Mistakes:** The AI frequently mixed up package roots and directory structures, writing broken internal imports that had to be manually re-mapped.

### 📊 6. Conclusion
Pairing GitHub Copilot (for quick boilerplate production) with Gemini (for structural problem-solving) reduced our overall engineering and debugging timeline by **70-80%**. While AI serves as a powerful development accelerator, rigorous human overview is completely mandatory to correct architectural scope, fix file pathing, and resolve visual UI bugs.
