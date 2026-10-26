# Direction sheet — workshop 1

> **Software Engineering 2026–27** · optional, not graded.
> Workshop 1 (W5, 26–30 Oct) confirms the direction you are taking your project in.

| | |
|---|---|
| **Team** | T2MR |
| **Members** | Roșoiu Matei, Necula Rareș Andrei, Soe Win Tint Sabei, Popescu Marta Gabriela |
| **Repository** | [is2627-proiect-group-27](https://github.com/inginerie-software-26-27/is2627-proiect-group-27) |

---

## 1. The system as it is (as-is)

UniGrade is a PyQt6 desktop app for university students. Students can add subjects, assessments and grades and see their averages, credits and progress. It has a FastAPI server with PostgreSQL, a leaderboard, graduation calculations, a grade simulator and a career advisor.

## 2. Direction (to-be)

| # | Goal | Why now | How we'll know we reached it |
|---|---|---|---|
| G1 | Build a web version of the main student features before adding more features. | The app only works as a desktop app, but the API can support a web client. | In six test scenarios, a user can register, log in, see the dashboard and progress, manage subjects and grades, and see graduation data. All tests pass in CI. |
| G2 | Make the web version safe to run and move the existing academic data to it. | The server needs the right PostgreSQL settings, and we have not tested a web deployment or data move yet. | One command starts the database and server; `/health` works; all users, subjects, assessments and grades are kept; protected pages reject users who are not logged in. |
| G3 | Add no more than one small new feature after G1 and G2 (possible feature: CSV export). | A full rewrite and many new AI or social features would be too much for one semester. | The workshop agrees on the feature; we build it and test it, or we leave it for later without delaying G1 and G2. |

**What we will not do:**

- No full rewrite of the grade or progress rules, no mobile app and no second web framework.
- No several new features or new social features. We will keep the current leaderboard behavior.
- No large production hosting or live connection to university systems this semester.

## 3. Stakeholders

| Who | What they want from the system | How we find out (interview, observation, scenario, repository) |
|---|---|---|
| Students (current users) | They need correct grades, credits, progress and graduation results, private data and access through a browser. | Read the repository and tests; walk through common scenarios; talk to and observe students. |
| Project maintainers / deployer | They need an easy start-up process, simple settings, health checks, logs and data backups. | Read the Docker and CI files; try a deployment; talk to the person who will run it. |
| People whose academic data is processed | They need their data to be seen only by the right account and not sent to an AI service by mistake. | Draw a data-flow scenario; read the code and settings; discuss privacy and security. |
| Future web users on supported browsers | They need the main academic actions to work in a browser without installing the desktop app. | Try the main actions in browsers; observe users; compare with the current PyQt/API behavior. |

## 4. Our resources

| Resource | What we have, realistically | What we are missing |
|---|---|---|
| **People** <br><sub>members, hours per week each, who is away and when</sub> | 1–2 hours per week are likely available. | More time and clear owners for web, data, testing and deployment. |
| **Knowledge** <br><sub>what we master, what would be a first</sub> | We know HTML, CSS and JavaScript, and have web experience with ASP.NET Core and PHP. We also have Python, PyQt6, FastAPI, PostgreSQL, Docker and CI in the project. | Migration, hosting, web security and privacy may be new for this project. |
| **Technical** <br><sub>stack, environments, CI, hosting, external services</sub> | Existing client, server, database, Docker Compose, CI and local Ollama. | Web frontend, hosting, backups and monitoring. |
| **Financial** <br><sub>budget (say so if it is zero)</sub> | Unknown. | Hosting costs, if free hosting is not enough. |
| **Access to AI** <br><sub>models, plans, who has them, limits; what data may not go into a model</sub> | One member may pay for an AI plan; the others have free/student plans. | Shared AI rules; private student data must not be sent to external models without permission. |

## 5. Feasibility

| Question | Yes / No / Don't know | Why |
|---|---|---|
| Does the direction serve what the stakeholders in section 3 want? | Yes | It gives students browser access and correct results, gives maintainers easy startup and data recovery, protects personal data, and gives future users the main features in a browser. |
| Can it be done by the end of the semester, with the resources in section 4? | Don't know | With only 1–2 hours per week, this depends on the team's web and deployment knowledge, hosting and whether we drop G3. We assume the existing API can be reused, the team can run PostgreSQL/Docker, and G1 and G2 come first. |
| Does it integrate with what already exists in and around the system? | Yes | The API, PostgreSQL database, Docker Compose and CI already exist. We still need to test the web client and data move. |

## 6. Top five risks

| # | Risk | Type | Impact | Likel. | Score | Strategy |
|---|---|---|---|---|---|---|
| R1 | With only 1–2 hours per week, the team does not finish the main web features. | estimation | 3 | 3 | 9 | **Avoid:** build only the six G1 scenarios first; drop G3 and reduce the web scope if needed. |
| R2 | The data move changes or loses grades, weights or owners. | technology | 3 | 2 | 6 | **Minimize:** define the data mapping, test it with sample data, compare every record and keep a backup. |
| R3 | Login, secrets or server settings expose student data. | technology | 3 | 2 | 6 | **Minimize:** use environment secrets, test protected routes and review the data flow; do not publish until these checks pass. |
| R4 | The web version changes existing grade or progress results. | requirements | 3 | 2 | 6 | **Minimize:** compare web results with the current API and desktop behavior in the six G1 scenarios; drop new features if parity fails. |
| R5 | Hosting, backups or monitoring are not ready for the web version. | technology / tools | 2 | 2 | 4 | **Minimize:** test one deployment early; choose a simple hosting option; **contingency:** submit a reproducible Docker deployment instead of public hosting. |

## 7. Candidate requirements (after W4)

| # | Requirement | Priority | Type | Source · confirmed by | Why (rationale) | How we check it |
|---|---|---|---|---|---|---|
| C1 | **The web app must keep** the current subject, assessment, grade, dashboard and progress behavior. | must | functional | Existing `ui/`, `client/`, `server/services/` and tests · confirmed by students | Students need the same results after moving from desktop to web. | Six G1 tests compare the web results with the current API results; all pass in CI. |
| C2 | **The web app must work** in the latest stable Chrome, Firefox and Edge on desktop. | must | product | G1 and stakeholder browser need · confirmed by students | Students need to use the app without installing the desktop client. | Run the six G1 scenarios in all three browsers; 18/18 pass. |
| C3 | **The project must provide** one command that starts the database and server on a clean machine. | must | organizational | `docker-compose.yml`, CI and maintainer need · confirmed by maintainers | The web version must be easy to start and run. | On a clean runner, the command starts the stack within 120 seconds and `GET /health` returns 200. |
| C4 | **The data move must keep** all users, subjects, assessments and grades with the same owners and values. | must | functional | `server/models.py`, schemas and data-owner need · confirmed by data owners | Academic data must not be lost or changed. | A migration test shows 100% equal record counts and values before and after the move. |
| C5 | **The service must require** a valid login token for private data and must block access to another user's records. | must | product | `server/dependencies.py`, auth routes and privacy need · confirmed by data owners | The app stores passwords and academic history. | Requests without a valid token return 401; cross-user requests return 403 or 404. |
| C6 | **The web API should answer** within 2 seconds for at least 95 of 100 requests. | should | product | G1 and maintainer performance need · confirmed by maintainers | The app should feel responsive without needing large-scale hosting. | An automated test measures p95 response time at 2 seconds or less. |
| C7 | **If time allows, the web app could export** one student's subjects, assessments, grades and credits as a CSV file. | could | functional | Possible feature discussed by the team · confirmed by students | Export may be useful, but the main web version comes first. | For test data, the file downloads within 5 seconds and contains all expected rows. |
| C8 | **The project won't add** another AI feature or a paid external AI service this semester. | won't | organizational | Current Ollama setup, time limit and team scope · confirmed by the team | The existing AI features already need maintenance, and the team has limited time. | Before release, check that no new AI service or AI feature was added. |

## 8. Top three architecture characteristics (if you get this far)

| # | Architecture characteristic | Comes from which requirement or domain concern | Explicit / implicit |
|---|---|---|---|
| A1 | **Deployability** — the web system must be easy to start and run, not just work on a developer's computer. | C2, C3; clean-machine setup and hosting | explicit |
| A2 | **Reliability** — grades and progress results must stay correct when users access them through the web or after the data move. | C1, C4; students rely on these results | explicit |
| A3 | **Security** — only the right user should see private academic data, even if there are few users at first. | C5; the app stores private data and passwords | implicit |

## 9. Questions for the workshop

- Do we want to move the whole app to the web this semester, or build only a small web part?
- Where will we host the app, and who will run it?
- How many hours and how much web/hosting knowledge does the team have? Can we fit G3 in the semester?
- Is CSV export the right new feature, or should we wait until G1 and G2 are done?
