# University-Grade-Calculator

A comprehensive full-stack application designed to help university students track, manage, and optimize their academic performance. The platform dynamically calculates grades and credit requirements while providing real-time visual progress bars to ensure students meet minimum benchmarks for yearly academic progression. Additionally, it integrates advanced AI-driven features, including an intelligent grade simulator and a personalized career advisor agent, to help students strategically plan their academic and professional journeys.

---

## 📐 Architecture & System Design

This project follows a clean, layered architecture separating the database models, business logic (services), API endpoints (routers), and frontend user interface.

### 1. Use Case Diagram
*It shows how the student interacts with the application tabs and how the AI agents communicate with external APIs.*

<img width="1142" height="1252" alt="Use diagram" src="https://github.com/user-attachments/assets/80424387-336c-4a61-a4b2-233f922f4962" />


### 2. Class Diagram
It illustrates the database schema for an academic performance tracking system, mapping how user profiles link to chronological course timelines, progression rules, and final graduation requirements.

<img width="1823" height="958" alt="class diagram modified" src="https://github.com/user-attachments/assets/ab28acbf-9b2c-4228-a7c2-76d6dc2570d8" />


### 3. Architectural Class Diagram
It illustrates how the PyQt6 frontend screens trigger asynchronous background worker threads, route workflows through client-side business logic services, and communicate with the central API network gateway to ensure responsive data processing and strict layer isolation.

<img width="1835" height="2008" alt="img 8" src="https://github.com/user-attachments/assets/98689ede-1f05-4577-8ab5-08baad947ca4" />


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
