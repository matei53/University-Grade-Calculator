# University-Grade-Calculator

A comprehensive full-stack application designed to help university students track, manage, and optimize their academic performance. The platform dynamically calculates grades and credit requirements while providing real-time visual progress bars to ensure students meet minimum benchmarks for yearly academic progression. Additionally, it integrates advanced AI-driven features, including an intelligent grade simulator and a personalized career advisor agent, to help students strategically plan their academic and professional journeys.

---

## 📐 Architecture & System Design

This project follows a clean, layered architecture separating the database models, business logic (services), API endpoints (routers), and frontend user interface.

### 1. Use Case Diagram
*Shows how the student interacts with the application tabs and how the AI agents communicate with external APIs.*

https://www.planttext.com?text=VLHTQnin47mt-3yi5sWJIEX3wKDJABawhGd4DDHneH0eQsbzfqOdkPBEhYdvxrtfFdAkayXW-tQrSpipArtuW2xKbHwF_BqoQtHOGOb6RfqAWGoiK7iQ9Yjhh2YThUWmjqPnZmNDmquJE181JQ7tTlWIfTqgKtJ5msJjIQ0d-3iU0QzFZ5OuMniviTewE5gzZvysQPqaroRUfjKaSkVijes_IsiyUeZlGH4ubir3BSa4M7Xo6Q27Bd24MWbQwfe-Q6NeFFxhgxwkoUHNy0QkhsUGtroboZPuf753XhjfwjQrM-l4h5S0ieLH6t9UXHrC7Kg22MfHQupWyvqFL6KTxUPRqof0iE1KKGQGAc8fQuPR1l0pL0OkqPTBYqx2AxXnjd3aVOyQLwVlOlBpkw9jt1zfPF7XiVhE7ASMFSDC74aLV0_7dhYJx4d4MyTspPHfIX9k2W77L5LN7TQTMJ7d7uIkHsLUBMOowZzkkU1cAYMumu0mGyCJLh5Xpr5hTgJDiOdc4VPGc68kvUbdxkVqaZG5Wdcz_CNlZAGRzYSlj7IBoxWnDwXtGOaNLRucHdEDBxtOW-3JQavA4lUnaM_qEvMbG6gjnZW8m8cQfo8guLzIxmg-48QQTORZl8YxJvvhDn6Vgogza7_ZV58hHpSLqCRPGrRXcLcOe2DokTmaf2a5Q28mhPL48uZHsFoLuWu7A0_jINtTdqbb0l4GHS8UjYgKi7AMOqP2O0_6esxZsTd7uLWV9FQdyo3zE3DFGWxiEiWFdJf8TeeULdKADNpPfUGD26iCjNpvzDCVvizJbguTlh0sV4EDHqEh8bvx3vr3ng8AFb3izJeIRO2oLF7eoNx9b0nB7BX4D1uvYxB2THOxks2bw-eV

### 2. Class Diagram
*Illustrates the backend object-oriented structure, built with SQLAlchemy ORM models and dedicated static service layers.*


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
