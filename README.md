# University-Grade-Calculator

A comprehensive full-stack application designed to help university students track, manage, and optimize their academic performance. The platform dynamically calculates grades and credit requirements while providing real-time visual progress bars to ensure students meet minimum benchmarks for yearly academic progression. Additionally, it integrates advanced AI-driven features, including an intelligent grade simulator and a personalized career advisor agent, to help students strategically plan their academic and professional journeys.

---

## 📐 Architecture & System Design

This project follows a clean, layered architecture separating the database models, business logic (services), API endpoints (routers), and frontend user interface.

### 1. Use Case Diagram
*It shows how the student interacts with the application tabs and how the AI agents communicate with external APIs.*

<img width="1085" height="1219" alt="Use diagram 1" src="https://github.com/user-attachments/assets/4aba0dbc-68e7-41aa-8921-ba9bd6046706" />


### 2. Class Diagram
*It illustrates the backend object-oriented structure, built with SQLAlchemy ORM models and dedicated static service layers.*

<img width="868" height="821" alt="Class Diagram" src="https://github.com/user-attachments/assets/7a13930a-6249-48ca-8dc7-c2b305869c71" />

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
