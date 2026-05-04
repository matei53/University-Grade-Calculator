# Nature-Minimalist Palette
FOREST_GREEN = "#2D4B1D"
SAGE_GREEN   = "#A8C686"
CREAM_BONE   = "#F4F1EE"
STONE_GREY   = "#C4B7A6"
MIDNIGHT     = "#0A0D08"

DASHBOARD_STYLE = f"""
    QWidget {{
        background-color: {CREAM_BONE};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 13px;
        color: {MIDNIGHT};
    }}

    QLabel {{
        background: transparent;
        border: none;
        padding: 0px;
        margin: 0px;
    }}

    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    QLabel#HeaderTitle {{
        font-size: 24px;
        font-weight: bold;
        color: {FOREST_GREEN};
    }}

    QLabel#HeaderSubtitle {{
        color: #666;
        font-size: 12px;
        font-weight: normal;
    }}

    QPushButton#FilterButton {{
        background-color: #E0DDD9;
        border: none;
        border-radius: 15px;
        padding: 6px 18px;
        font-weight: bold;
        color: #444;
    }}

    QPushButton#FilterButton:hover {{
        background-color: {STONE_GREY};
    }}

    QPushButton#FilterButton[active="true"] {{
        background-color: {FOREST_GREEN};
        color: white;
    }}

    QFrame#StatCard {{
        background-color: white;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 10px;
    }}

    QLabel#CardTitle {{
        color: #777;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    QLabel#CardValue {{
        color: {FOREST_GREEN};
        font-size: 32px;
        font-weight: bold;
    }}

    QLabel#CardSub {{
        color: #999;
        font-size: 11px;
    }}

    QToolButton#YearToggle {{
        background-color: white;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 15px;
        font-weight: bold;
        font-size: 15px;
        text-align: left;
    }}

    QToolButton#YearToggle:checked {{
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
    }}

    QFrame#YearContentArea {{
        background-color: white;
        border: 1px solid #E0E0E0;
        border-top: none;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
    }}

    QFrame#MiniStatCard {{
        background-color: #F0EDE9;
        border: none;
        border-radius: 10px;
        min-height: 60px;
    }}

    QProgressBar {{
        background-color: #E5E5E5;
        border: none;
        border-radius: 6px;
        height: 12px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {FOREST_GREEN};
        border-radius: 6px;
    }}

    QFrame#SubjectRow {{
        background-color: transparent;
        border: none;
        border-bottom: 1px solid #F0F0F0;
    }}

    QFrame#SubjectRow:last-child {{
        border-bottom: none;
    }}

    QLabel#SemesterHeader {{
        color: {FOREST_GREEN};
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
        margin-top: 15px;
        margin-bottom: 5px;
    }}

    QPushButton#SecondaryButton {{
        background-color: {FOREST_GREEN};
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }}

    QPushButton#SecondaryButton:hover {{
        background-color: #3d632a;
    }}
"""