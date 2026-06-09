# University-Grade-Calculator

A comprehensive full-stack application designed to help university students track, manage, and optimize their academic performance. The platform dynamically calculates grades and credit requirements while providing real-time visual progress bars to ensure students meet minimum benchmarks for yearly academic progression. Additionally, it integrates advanced AI-driven features, including an intelligent grade simulator and a personalized career advisor agent, to help students strategically plan their academic and professional journeys.

---

## 📐 Architecture & System Design

This project follows a clean, layered architecture separating the database models, business logic (services), API endpoints (routers), and frontend user interface.

### 1. Use Case Diagram
*Shows how the student interacts with the application tabs and how the AI agents communicate with external APIs.*


### 2. Class Diagram
*Illustrates the backend object-oriented structure, built with SQLAlchemy ORM models and dedicated static service layers.*

<img width="868" height="856" alt="Case Diagram" src="https://github.com/user-attachments/assets/be686e0e-80d2-41ba-85b6-4ae574606984" />

---

## 🚀 How to Use the Application

Once you launch the platform, you can navigate through the interface using the dedicated application tabs:

### 📊 Main Dashboard & Progress Tracking
* 📊 **Monitor Credits:** View your ongoing credit totals against a live progress bar.
* 📊 **Track Progression:** Check the application metrics to see if you have cleared the minimum credit thresholds required to advance to the next academic year (Year 2, Year 3, etc.).
* 📊 **Check Graduation Status:** View a real-time summary of your remaining graduation requirements.

### ⚙️ Academic Data Management
* ⚙️ **Manage Subjects:** Use the input fields to add and edit subjects, including their custom name, credit value, and passing scale.
* ⚙️ **Log Assessments:** Add evaluations (such as midterms, labs, or finals) to individual courses and modify weights to automatically compute final grades.

### 📊 Analytics & Community
* 📊 **Leaderboard Tab:** Head over to the leaderboard to view class standings and see how your academic progression stacks up against fellow peers.

### ⚙️ Interactive AI Agents
* ⚙️ **Grade Simulator Tab:** Run predictive scoring scenarios to estimate exactly what marks you need on upcoming assignments to maintain or achieve your target GPA.
* ⚙️ **Career Advisor Tab:** Chat with the integrated AI guidance counselor agent to receive personalized internship and career roadmap suggestions based on your completed courses and academic history.
