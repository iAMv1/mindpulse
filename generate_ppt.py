from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation("D:/another-project/mini.pptx")

DARK_GRAY = RGBColor(0x2C, 0x2C, 0x2C)
ACCENT_TEAL = RGBColor(0x27, 0x78, 0x84)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0x99, 0x99, 0x99)
RED = RGBColor(0xCC, 0x33, 0x33)


def set_text(
    shape,
    text,
    font_name="Arial",
    font_size=Pt(14),
    bold=False,
    color=DARK_GRAY,
    alignment=PP_ALIGN.LEFT,
):
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = font_size
    run.font.bold = bold
    run.font.color.rgb = color


def add_para(
    text_frame,
    text,
    font_size=Pt(14),
    bold=False,
    color=DARK_GRAY,
    alignment=PP_ALIGN.LEFT,
    space_before=Pt(4),
    space_after=Pt(2),
):
    p = text_frame.add_paragraph()
    p.alignment = alignment
    p.space_before = space_before
    p.space_after = space_after
    run = p.add_run()
    run.text = text
    run.font.name = "Arial"
    run.font.size = font_size
    run.font.bold = bold
    run.font.color.rgb = color
    return p


def add_shape_with_text(
    slide,
    left,
    top,
    width,
    height,
    text,
    font_size=Pt(12),
    bold=False,
    color=DARK_GRAY,
    fill_color=None,
):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.shadow.inherit = False
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.name = "Arial"
    run.font.size = font_size
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def add_accent_bar(slide, left, top, width=Inches(0.08), height=Inches(0.5)):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = ACCENT_TEAL
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_notes(slide, notes_text):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = notes_text


def get_layout(idx):
    return prs.slide_layouts[min(idx, len(prs.slide_layouts) - 1)]


# ===== SLIDE 1: TITLE =====
slide = prs.slides.add_slide(get_layout(1))
add_shape_with_text(
    slide,
    Inches(0.8),
    Inches(1.2),
    Inches(8.4),
    Inches(1.2),
    "MindPulse: Privacy-First Behavioral Stress Detection System",
    font_size=Pt(28),
    bold=True,
    color=ACCENT_TEAL,
)
add_shape_with_text(
    slide,
    Inches(0.8),
    Inches(2.5),
    Inches(8.4),
    Inches(0.6),
    "Detecting Stress from HOW You Type, Not WHAT You Type",
    font_size=Pt(18),
    bold=False,
    color=DARK_GRAY,
)
add_accent_bar(slide, Inches(0.8), Inches(3.3), Inches(8.4), Inches(0.04))
add_shape_with_text(
    slide,
    Inches(0.8),
    Inches(3.6),
    Inches(8.4),
    Inches(2.0),
    "Team Members: Neha (01111502723) | Anand Misra (04011502723) | Pratham Nahar (05311502723)\n\n"
    "Mentored by: Dr. Jolly Parikh\n\nMini Project Review - Academic Year 2024-25",
    font_size=Pt(16),
    color=DARK_GRAY,
)
add_notes(
    slide,
    "Welcome to our Mini Project Review on MindPulse - a privacy-first behavioral stress detection system. "
    "Our system detects workplace stress from typing patterns, mouse movements, and app-switching behavior "
    "without ever capturing what the user types, ensuring complete privacy.",
)

# ===== SLIDE 2: INTRODUCTION =====
slide = prs.slides.add_slide(get_layout(2))
set_text(
    slide.placeholders[0],
    "Introduction / Problem Statement",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
body = slide.placeholders[1].text_frame
body.word_wrap = True
body.clear()
add_para(
    body,
    "The Workplace Stress Crisis",
    font_size=Pt(16),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(
    body,
    "83% of US workers experience workplace stress (American Institute of Stress, 2023)",
    font_size=Pt(13),
)
add_para(
    body,
    "Annual cost to employers: $300 billion in absenteeism, turnover, reduced productivity",
    font_size=Pt(13),
)
add_para(body, "", font_size=Pt(8))
add_para(
    body, "Current Detection Methods", font_size=Pt(16), bold=True, color=ACCENT_TEAL
)
add_para(
    body,
    "Self-report questionnaires - subjective, infrequent, recall bias",
    font_size=Pt(13),
)
add_para(
    body,
    "Wearable sensors - invasive, expensive, requires specialized hardware",
    font_size=Pt(13),
)
add_para(
    body,
    "Physiological monitoring - impractical for continuous workplace use",
    font_size=Pt(13),
)
add_para(body, "", font_size=Pt(8))
add_para(body, "The Research Gap", font_size=Pt(16), bold=True, color=ACCENT_TEAL)
add_para(
    body,
    "No existing system detects stress from computer interaction while preserving privacy",
    font_size=Pt(13),
)
add_notes(
    slide,
    "Workplace stress affects 83% of US workers and costs $300B annually. Current methods are subjective, invasive, or expensive. MindPulse addresses the gap of privacy-preserving behavioral stress detection.",
)

# ===== SLIDE 3: SOLUTION =====
slide = prs.slides.add_slide(get_layout(2))
set_text(
    slide.placeholders[0],
    "Our Solution: MindPulse",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
body = slide.placeholders[1].text_frame
body.word_wrap = True
body.clear()
add_para(
    body,
    "Desktop-First Behavioral Stress Analytics System",
    font_size=Pt(16),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(body, "", font_size=Pt(6))
add_para(body, "Predicts stress levels: NEUTRAL / MILD / STRESSED", font_size=Pt(14))
add_para(body, "Zero content capture - never records what you type", font_size=Pt(14))
add_para(body, "On-device processing - all inference happens locally", font_size=Pt(14))
add_para(
    body,
    "Personal adaptation - learns your individual baseline over time",
    font_size=Pt(14),
)
add_para(
    body,
    "Real-time monitoring - WebSocket streaming with 5-minute windows",
    font_size=Pt(14),
)
add_para(body, "", font_size=Pt(6))
add_para(body, "Core Innovation", font_size=Pt(16), bold=True, color=ACCENT_TEAL)
add_para(
    body,
    "23-feature behavioral vector (vs. typical 8-12 in literature)",
    font_size=Pt(13),
)
add_para(
    body,
    "Dual normalization: global z-score + per-user circadian deviation",
    font_size=Pt(13),
)
add_para(
    body,
    "3 novel features: session_fragmentation, rage_click_count, switch_entropy",
    font_size=Pt(13),
)
add_notes(
    slide,
    "MindPulse detects stress from interaction metadata only. Key innovations: 23 features, dual normalization, 3 novel features not found in existing literature.",
)

# ===== SLIDE 4: OBJECTIVES =====
slide = prs.slides.add_slide(get_layout(2))
set_text(
    slide.placeholders[0],
    "Project Objectives",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
body = slide.placeholders[1].text_frame
body.word_wrap = True
body.clear()
objectives = [
    "1. Design a privacy-preserving stress detection system - Completed",
    "2. Analyze user behavioral patterns (keyboard, mouse, context switching) - Completed",
    "3. Extract key stress-related features (typing irregularity, error rate, rage clicks) - Completed",
    "4. Develop a hybrid machine learning model for stress classification - Completed",
    "5. Enable real-time, on-device stress monitoring - Completed",
    "6. Implement personalized calibration with adaptive stress interventions - Completed",
]
for obj in objectives:
    add_para(body, obj, font_size=Pt(13))
add_notes(
    slide,
    "All six original project objectives have been completed. Privacy system designed, behavioral patterns analyzed, 23 features extracted, XGBoost model trained, real-time monitoring via WebSocket, personal calibration with EMA baselines.",
)

# ===== SLIDE 5: ROADMAP =====
slide = prs.slides.add_slide(get_layout(4))
set_text(
    slide.placeholders[0],
    "Project Roadmap / Stages",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
phases = [
    (
        "Phase 1",
        "Research & Design",
        "Literature review, behavioral indicators, feature design, privacy architecture",
        "Completed",
    ),
    (
        "Phase 2",
        "Data Collection & Engineering",
        "pynput collector, 23-feature pipeline, synthetic data, realistic simulator",
        "Completed",
    ),
    (
        "Phase 3",
        "Model Development",
        "XGBoost, DualNormalizer, PersonalBaseline, 1D-CNN, Group K-Fold",
        "Completed",
    ),
    (
        "Phase 4",
        "Application Development",
        "FastAPI backend, Next.js frontend, WebSocket streaming, dashboard",
        "Completed",
    ),
    (
        "Phase 5",
        "Evaluation & Calibration",
        "Leave-One-User-Out, calibration eval, benchmark comparison",
        "Completed",
    ),
    (
        "Phase 6",
        "Real-User Deployment",
        "15-20 real users, per-user calibration testing, browser extension",
        "Next",
    ),
]
for i, (phase, title, desc, status) in enumerate(phases):
    y = Inches(1.6) + Inches(i * 0.9)
    add_shape_with_text(
        slide,
        Inches(0.5),
        y,
        Inches(1.2),
        Inches(0.7),
        f"{phase}\n{status}",
        font_size=Pt(10),
        bold=True,
        color=WHITE if status == "Completed" else DARK_GRAY,
        fill_color=ACCENT_TEAL if status == "Completed" else RGBColor(0xE0, 0xE0, 0xE0),
    )
    add_shape_with_text(
        slide,
        Inches(1.9),
        y,
        Inches(2.5),
        Inches(0.7),
        title,
        font_size=Pt(11),
        bold=True,
        color=DARK_GRAY,
    )
    add_shape_with_text(
        slide,
        Inches(4.6),
        y,
        Inches(5.0),
        Inches(0.7),
        desc,
        font_size=Pt(10),
        color=DARK_GRAY,
    )
add_notes(
    slide,
    "Six phases total. Phases 1-5 complete: research, data collection, model development, app development, evaluation. Phase 6 (real-user deployment) is next.",
)

# ===== SLIDE 6: ARCHITECTURE =====
slide = prs.slides.add_slide(get_layout(4))
set_text(
    slide.placeholders[0],
    "System Architecture",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
components = [
    (
        Inches(0.5),
        Inches(1.8),
        "Desktop App\n(Python/pynput)\n\npynput collector\nKeyboard/Mouse/Context",
    ),
    (
        Inches(3.0),
        Inches(1.8),
        "ML Engine\n(XGBoost + CNN)\n\n23-feature extraction\nDualNormalizer",
    ),
    (Inches(5.5), Inches(1.8), "Backend API\n(FastAPI)\n\nREST + WebSocket\nPort 5000"),
    (
        Inches(5.5),
        Inches(4.2),
        "Frontend\n(Next.js 15)\n\nRiskMeter gauge\nTimelineChart",
    ),
]
for left, top, text in components:
    add_shape_with_text(
        slide,
        left,
        top,
        Inches(2.2),
        Inches(1.8),
        text,
        font_size=Pt(10),
        bold=False,
        color=WHITE,
        fill_color=ACCENT_TEAL,
    )
add_notes(
    slide,
    "Four components: Desktop App captures events via pynput. ML Engine extracts features and runs XGBoost. FastAPI backend serves predictions. Next.js frontend provides real-time visualization.",
)

# ===== SLIDE 7: DATA COLLECTION =====
slide = prs.slides.add_slide(get_layout(3))
set_text(
    slide.placeholders[0],
    "Data Collection (Privacy-First)",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
left_body = slide.placeholders[1].text_frame
left_body.word_wrap = True
left_body.clear()
add_para(
    left_body,
    "What We Record",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(left_body, "Keyboard:", font_size=Pt(12), bold=True, space_before=Pt(8))
add_para(left_body, "timestamp_press, timestamp_release", font_size=Pt(11))
add_para(left_body, "key_category (alpha/digit/special)", font_size=Pt(11))
add_para(left_body, "Mouse:", font_size=Pt(12), bold=True, space_before=Pt(8))
add_para(left_body, "x, y position, timestamp", font_size=Pt(11))
add_para(left_body, "click_type, scroll_delta", font_size=Pt(11))
add_para(left_body, "Context:", font_size=Pt(12), bold=True, space_before=Pt(8))
add_para(left_body, "switch_timestamp", font_size=Pt(11))
add_para(left_body, "app_category_hash (SHA-256)", font_size=Pt(11))
right_body = slide.placeholders[2].text_frame
right_body.word_wrap = True
right_body.clear()
add_para(
    right_body,
    "What We DON'T Record",
    font_size=Pt(14),
    bold=True,
    color=RED,
    space_before=Pt(0),
)
add_para(right_body, "Actual key characters", font_size=Pt(12), space_before=Pt(8))
add_para(right_body, "Screen content or URLs", font_size=Pt(12))
add_para(right_body, "Application names (hashed)", font_size=Pt(12))
add_para(right_body, "File contents or messages", font_size=Pt(12))
add_para(right_body, "", font_size=Pt(6))
add_para(
    right_body,
    "Privacy Guarantees",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(8),
)
add_para(right_body, "Zero content capture", font_size=Pt(12))
add_para(right_body, "On-device processing", font_size=Pt(12))
add_para(right_body, "SHA-256 app hashing", font_size=Pt(12))
add_notes(
    slide,
    "Privacy is our core design principle. We capture only timing metadata, never actual content. App names are SHA-256 hashed.",
)

# ===== SLIDE 8: FEATURES =====
slide = prs.slides.add_slide(get_layout(4))
set_text(
    slide.placeholders[0],
    "Feature Extraction (23 Dimensions)",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
categories = [
    (
        "Keyboard (11)",
        "hold_time_mean/std/median\nflight_time_mean/std\ntyping_speed_wpm\nerror_rate\npause_frequency/duration\nburst_length_mean\nrhythm_entropy",
        Inches(0.5),
        Inches(1.6),
    ),
    (
        "Mouse (6)",
        "mouse_speed_mean/std\ndirection_change_rate\nclick_count\nrage_click_count\nscroll_velocity_std",
        Inches(3.3),
        Inches(1.6),
    ),
    (
        "Context (3)",
        "tab_switch_freq\nswitch_entropy\nsession_fragmentation",
        Inches(5.5),
        Inches(1.6),
    ),
    (
        "Temporal (3)",
        "hour_of_day\nday_of_week\nsession_duration_min",
        Inches(7.5),
        Inches(1.6),
    ),
]
for title, features, left, top in categories:
    add_shape_with_text(
        slide,
        left,
        top,
        Inches(2.0),
        Inches(3.5),
        f"{title}\n\n{features}",
        font_size=Pt(10),
        bold=False,
        color=DARK_GRAY,
    )
add_shape_with_text(
    slide,
    Inches(0.5),
    Inches(5.3),
    Inches(9.0),
    Inches(1.2),
    "Dual Normalization: [23 global z-scores] + [23 per-user circadian z-scores] -> 46 features for model input",
    font_size=Pt(12),
    bold=False,
    color=DARK_GRAY,
)
add_notes(
    slide,
    "23 features across 4 categories. Dual normalization creates 46-dimensional input by concatenating global and per-user z-scores.",
)

# ===== SLIDE 9: MODEL =====
slide = prs.slides.add_slide(get_layout(3))
set_text(
    slide.placeholders[0],
    "Machine Learning Model & Calibration",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
left_body = slide.placeholders[1].text_frame
left_body.word_wrap = True
left_body.clear()
add_para(
    left_body,
    "XGBoost Classifier",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(
    left_body,
    "Objective: multi:softprob (3-class)",
    font_size=Pt(12),
    space_before=Pt(6),
)
add_para(left_body, "Max depth: 6", font_size=Pt(12))
add_para(left_body, "Estimators: 350", font_size=Pt(12))
add_para(left_body, "Learning rate: 0.08", font_size=Pt(12))
add_para(left_body, "Subsample: 0.9", font_size=Pt(12))
add_para(left_body, "Class weights: Balanced", font_size=Pt(12))
add_para(left_body, "", font_size=Pt(6))
add_para(
    left_body,
    "1D-CNN (Secondary Branch)",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
)
add_para(
    left_body, "Processes raw keystroke sequences", font_size=Pt(12), space_before=Pt(6)
)
add_para(left_body, "Captures digraph/trigraph patterns", font_size=Pt(12))
right_body = slide.placeholders[2].text_frame
right_body.word_wrap = True
right_body.clear()
add_para(
    right_body,
    "DualNormalizer",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(
    right_body, "Global z-score: (x - mu) / sigma", font_size=Pt(12), space_before=Pt(6)
)
add_para(right_body, "Per-user circadian: hourly baselines", font_size=Pt(12))
add_para(right_body, "Output: 46-dimensional feature vector", font_size=Pt(12))
add_para(right_body, "", font_size=Pt(6))
add_para(
    right_body,
    "PersonalBaseline (SQLite + EMA)",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
)
add_para(
    right_body,
    "Tracks per-user feature means per hour",
    font_size=Pt(12),
    space_before=Pt(6),
)
add_para(right_body, "Exponential Moving Average updates", font_size=Pt(12))
add_para(right_body, "Enables calibration: +1.9% F1 improvement", font_size=Pt(12))
add_notes(
    slide,
    "XGBoost with 350 estimators, balanced class weights. DualNormalizer creates 46 features. PersonalBaseline uses SQLite with EMA for per-user calibration.",
)

# ===== SLIDE 10: LITERATURE REVIEW =====
slide = prs.slides.add_slide(get_layout(4))
set_text(
    slide.placeholders[0],
    "Literature Review",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
rows, cols = 6, 5
table_shape = slide.shapes.add_table(
    rows, cols, Inches(0.3), Inches(1.4), Inches(9.4), Inches(4.8)
)
table = table_shape.table
headers = ["Year & Citation", "Technology", "Dataset", "Key Finding", "Result"]
for i, h in enumerate(headers):
    cell = table.cell(0, i)
    cell.text = h
    for p in cell.text_frame.paragraphs:
        p.runs[0].font.size = Pt(10)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = WHITE
        p.runs[0].font.name = "Arial"
    cell.fill.solid()
    cell.fill.fore_color.rgb = ACCENT_TEAL
data = [
    [
        "Naegelin et al.\n(2025) ETH Zurich",
        "Keyboard+mouse\nML analysis",
        "OSF: qpekf\n36 employees, 8wk",
        "Universal models\nperform poorly",
        "F1 = 7.8%",
    ],
    [
        "VTT Finland\n(2024)",
        "AI mouse movement\nanalysis",
        "Proprietary\nworkplace dataset",
        "Mouse > heart rate\nfor stress",
        "71% accuracy",
    ],
    [
        "Pepa et al.\n(2021)",
        "Keystroke dynamics\nRandom Forest",
        "Zenodo\n62 users",
        "In-the-wild feasible\nkeyboard only",
        "F1 = 60%",
    ],
    [
        "CMU (2023)",
        "Hold time + latency\nanalysis",
        "CMU InfSci\n116 subjects",
        "Fits-and-starts\npattern under stress",
        "76% accuracy",
    ],
    [
        "ETH Zurich\n(2023)",
        "Neuromotor noise\ntheory",
        "OSF: qpekf\nLab study",
        "Typing > heart rate\nfor office stress",
        "F1 = 62.5%",
    ],
]
for r, row_data in enumerate(data):
    for c, val in enumerate(row_data):
        cell = table.cell(r + 1, c)
        cell.text = val
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.name = "Arial"
                run.font.color.rgb = DARK_GRAY
table.columns[0].width = Inches(1.8)
table.columns[1].width = Inches(1.8)
table.columns[2].width = Inches(1.8)
table.columns[3].width = Inches(2.2)
table.columns[4].width = Inches(1.8)
add_notes(
    slide,
    "Literature review covers 5 key studies. ETH Zurich 2025 found universal models perform poorly (F1=7.8%). VTT Finland showed mouse alone achieves 71%. Pepa et al. demonstrated in-the-wild feasibility (60% F1).",
)

# ===== SLIDE 11: PROGRESS =====
slide = prs.slides.add_slide(get_layout(4))
set_text(
    slide.placeholders[0],
    "Progress Since Last Review",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
rows, cols = 7, 3
table_shape = slide.shapes.add_table(
    rows, cols, Inches(0.5), Inches(1.4), Inches(9.0), Inches(4.5)
)
table = table_shape.table
headers = ["Component", "Status", "Details"]
for i, h in enumerate(headers):
    cell = table.cell(0, i)
    cell.text = h
    for p in cell.text_frame.paragraphs:
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = WHITE
        p.runs[0].font.name = "Arial"
    cell.fill.solid()
    cell.fill.fore_color.rgb = ACCENT_TEAL
progress = [
    [
        "ML Core",
        "Complete",
        "4 Python modules: data_collector, feature_extractor, model, synthetic_data",
    ],
    ["Backend API", "Complete", "FastAPI with 7 REST endpoints + WebSocket streaming"],
    [
        "Frontend Dashboard",
        "Complete",
        "Next.js 15 with 6 pages, 7 components, real-time WebSocket",
    ],
    [
        "Evaluation Pipeline",
        "Complete",
        "Group K-Fold, calibration eval, realistic simulator",
    ],
    [
        "Documentation",
        "Complete",
        "Research report, ML pipeline design, results summary",
    ],
    ["GitHub Repository", "Live", "53 files, clean structure at iAMv1/mindpulse"],
]
for r, row_data in enumerate(progress):
    for c, val in enumerate(row_data):
        cell = table.cell(r + 1, c)
        cell.text = val
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                run.font.size = Pt(10)
                run.font.name = "Arial"
                run.font.color.rgb = DARK_GRAY
table.columns[0].width = Inches(2.0)
table.columns[1].width = Inches(1.5)
table.columns[2].width = Inches(5.5)
add_notes(
    slide,
    "All major components completed since last review. ML core, backend API, frontend dashboard, evaluation pipeline, documentation, and GitHub repository are all done.",
)

# ===== SLIDE 12: CHALLENGES =====
slide = prs.slides.add_slide(get_layout(4))
set_text(
    slide.placeholders[0],
    "Challenges Faced & Overcome",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
challenges = [
    (
        "Feature Shape Mismatch",
        "Model expected 46, inference passed 23",
        "Implemented DualNormalizer",
    ),
    (
        "Import Failures",
        "Relative imports broke in __main__",
        "Converted to relative imports",
    ),
    (
        "Duplicate Servers",
        "Two separate FastAPI implementations",
        "Consolidated into single backend",
    ),
    (
        "Unrealistic Metrics",
        "99%+ F1 from separable classes",
        "Created overlap simulator",
    ),
    ("Unicode Errors", "Box-drawing chars caused codec errors", "Replaced with ASCII"),
    (
        "Path Resolution",
        "Artifacts pointed to wrong directory",
        "Module-relative paths",
    ),
]
for i, (problem, detail, solution) in enumerate(challenges):
    y = Inches(1.5) + Inches(i * 0.85)
    add_shape_with_text(
        slide,
        Inches(0.5),
        y,
        Inches(2.5),
        Inches(0.7),
        problem,
        font_size=Pt(10),
        bold=True,
        color=DARK_GRAY,
    )
    add_shape_with_text(
        slide,
        Inches(3.2),
        y,
        Inches(3.3),
        Inches(0.7),
        detail,
        font_size=Pt(9),
        color=RED,
    )
    add_shape_with_text(
        slide,
        Inches(6.7),
        y,
        Inches(2.8),
        Inches(0.7),
        solution,
        font_size=Pt(9),
        color=ACCENT_TEAL,
    )
add_notes(
    slide,
    "Six major challenges: feature shape mismatch, import failures, duplicate servers, unrealistic metrics, Unicode errors, path resolution. All successfully resolved.",
)

# ===== SLIDE 13: METRICS =====
slide = prs.slides.add_slide(get_layout(3))
set_text(
    slide.placeholders[0],
    "Performance Comparison & Metrics",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
left_body = slide.placeholders[1].text_frame
left_body.word_wrap = True
left_body.clear()
add_para(
    left_body,
    "Evaluation Results",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(left_body, "", font_size=Pt(4))
add_para(
    left_body, "Evaluation          F1-Macro   Accuracy", font_size=Pt(10), bold=True
)
add_para(left_body, "Universal (no cal)   46.8%      48.0%", font_size=Pt(10))
add_para(left_body, "Calibrated (40)      48.7%      50.0%", font_size=Pt(10))
add_para(
    left_body,
    "Improvement          +1.9%      +2.0%",
    font_size=Pt(10),
    color=ACCENT_TEAL,
    bold=True,
)
add_para(left_body, "", font_size=Pt(6))
add_para(
    left_body, "Per-Class Performance", font_size=Pt(13), bold=True, color=ACCENT_TEAL
)
add_para(
    left_body, "NEUTRAL  - Precision: 0.54  Recall: 0.71  F1: 0.62", font_size=Pt(10)
)
add_para(
    left_body, "MILD     - Precision: 0.31  Recall: 0.11  F1: 0.17", font_size=Pt(10)
)
add_para(
    left_body, "STRESSED - Precision: 0.28  Recall: 0.33  F1: 0.30", font_size=Pt(10)
)
right_body = slide.placeholders[2].text_frame
right_body.word_wrap = True
right_body.clear()
add_para(
    right_body,
    "Research Benchmark Comparison",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(right_body, "", font_size=Pt(4))
add_para(right_body, "Study                     F1-Macro", font_size=Pt(10), bold=True)
add_para(right_body, "ETH Zurich 2025 (Univ.)    7.8%", font_size=Pt(10))
add_para(
    right_body, "MindPulse (Universal)     46.8%", font_size=Pt(10), color=ACCENT_TEAL
)
add_para(
    right_body, "MindPulse (Calibrated)    48.7%", font_size=Pt(10), color=ACCENT_TEAL
)
add_para(right_body, "ETH Zurich 2023 (Lab)     62.5%", font_size=Pt(10))
add_para(right_body, "Pepa et al. 2021          60.0%", font_size=Pt(10))
add_para(right_body, "", font_size=Pt(6))
add_para(
    right_body,
    "MILD class is bottleneck (F1=0.17)",
    font_size=Pt(11),
    bold=True,
    color=RED,
)
add_notes(
    slide,
    "Universal model: 46.8% F1 matching ETH Zurich 2025. Calibrated: 48.7% (+1.9%). MILD class is the bottleneck at F1=0.17.",
)

# ===== SLIDE 14: GAPS =====
slide = prs.slides.add_slide(get_layout(3))
set_text(
    slide.placeholders[0],
    "Research Gaps",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
left_body = slide.placeholders[1].text_frame
left_body.word_wrap = True
left_body.clear()
add_para(
    left_body,
    "Gaps We Overcame",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
gaps = [
    "Limited feature sets (8-12) -> 23 features with 3 novel",
    "No personal calibration -> DualNormalizer + EMA",
    "Privacy concerns -> Zero content capture",
    "Simplified evaluation -> Group K-Fold honest validation",
    "No self-report noise modeling -> 76.8% accuracy sim",
]
for g in gaps:
    add_para(left_body, f"  {g}", font_size=Pt(11), space_before=Pt(4))
right_body = slide.placeholders[2].text_frame
right_body.word_wrap = True
right_body.clear()
add_para(
    right_body,
    "New Research Gaps",
    font_size=Pt(14),
    bold=True,
    color=RED,
    space_before=Pt(0),
)
new_gaps = [
    "No real-user data (all simulated)",
    "MILD class detection weak (F1=0.17)",
    "Desktop-only (pynput dependency)",
    "Calibration cold start problem",
    "Long-term concept drift untested",
]
for g in new_gaps:
    add_para(right_body, f"  {g}", font_size=Pt(11), space_before=Pt(4))
add_notes(
    slide,
    "Overcame 5 major gaps. 5 new gaps identified: real-user data, MILD detection, platform, cold start, concept drift.",
)

# ===== SLIDE 15: NEW CHALLENGES =====
slide = prs.slides.add_slide(get_layout(4))
set_text(
    slide.placeholders[0],
    "New Challenges & Tackling Strategy",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
challenges_new = [
    (
        "Real-User Data",
        "All eval on simulated data",
        "Deploy 15-20 volunteers, 2-4 weeks",
        "2-3 months",
    ),
    (
        "MILD Class F1=0.17",
        "Overlaps with NEUTRAL/STRESSED",
        "Ordinal regression",
        "1 month",
    ),
    ("Cross-Platform", "Desktop-only (pynput)", "Chrome extension", "2 months"),
    (
        "Cold Start",
        "New users have no baseline",
        "Population -> personal model",
        "Implemented",
    ),
    ("Concept Drift", "Behavior changes over time", "SPC + retraining", "3 months"),
]
for i, (challenge, problem, strategy, timeline) in enumerate(challenges_new):
    y = Inches(1.5) + Inches(i * 1.0)
    add_shape_with_text(
        slide,
        Inches(0.3),
        y,
        Inches(2.0),
        Inches(0.8),
        challenge,
        font_size=Pt(10),
        bold=True,
        color=WHITE,
        fill_color=RED,
    )
    add_shape_with_text(
        slide,
        Inches(2.5),
        y,
        Inches(2.2),
        Inches(0.8),
        problem,
        font_size=Pt(9),
        color=DARK_GRAY,
    )
    add_shape_with_text(
        slide,
        Inches(4.9),
        y,
        Inches(3.0),
        Inches(0.8),
        strategy,
        font_size=Pt(9),
        color=DARK_GRAY,
    )
    add_shape_with_text(
        slide,
        Inches(8.1),
        y,
        Inches(1.5),
        Inches(0.8),
        timeline,
        font_size=Pt(10),
        bold=True,
        color=ACCENT_TEAL,
    )
add_notes(
    slide,
    "Five new challenges with strategies: real-user deployment, MILD class ordinal regression, Chrome extension, population-to-personal transition, concept drift retraining.",
)

# ===== SLIDE 16: CONCLUSION =====
slide = prs.slides.add_slide(get_layout(3))
set_text(
    slide.placeholders[0],
    "Conclusion & References",
    font_size=Pt(24),
    bold=True,
    color=ACCENT_TEAL,
)
left_body = slide.placeholders[1].text_frame
left_body.word_wrap = True
left_body.clear()
add_para(
    left_body,
    "Key Takeaways",
    font_size=Pt(14),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
add_para(
    left_body,
    "Privacy-first stress detection is feasible",
    font_size=Pt(11),
    space_before=Pt(6),
)
add_para(left_body, "46.8% F1 universal, 48.7% calibrated", font_size=Pt(11))
add_para(left_body, "23 features with 3 novel ones", font_size=Pt(11))
add_para(left_body, "Complete full-stack implementation", font_size=Pt(11))
add_para(left_body, "Honest evaluation (Group K-Fold)", font_size=Pt(11))
add_para(left_body, "", font_size=Pt(6))
add_para(left_body, "Next Steps", font_size=Pt(14), bold=True, color=ACCENT_TEAL)
add_para(left_body, "Real-user deployment (15-20 users)", font_size=Pt(11))
add_para(left_body, "Browser extension development", font_size=Pt(11))
add_para(left_body, "Multi-modal fusion", font_size=Pt(11))
right_body = slide.placeholders[2].text_frame
right_body.word_wrap = True
right_body.clear()
add_para(
    right_body,
    "References",
    font_size=Pt(12),
    bold=True,
    color=ACCENT_TEAL,
    space_before=Pt(0),
)
refs = [
    "[1] Naegelin et al. (2025) ETH Zurich - osf.io/qpekf",
    "[2] VTT Finland (2024) AI mouse movement",
    "[3] Pepa et al. (2021) Keystroke - Zenodo",
    "[4] CMU (2023) Keystroke stress - CMU InfSci",
    "[5] ETH Zurich (2023) Neuromotor - OSF",
    "[6] XGBoost - github.com/dmlc/xgboost",
    "[7] FastAPI - github.com/tiangolo/fastapi",
    "[8] Next.js - github.com/vercel/next.js",
    "[9] pynput - pypi.org/project/pynput",
    "[10] scikit-learn - github.com/scikit-learn",
    "[11] Amer. Inst. Stress (2023) - stress.org",
]
for ref in refs:
    add_para(right_body, ref, font_size=Pt(8), space_before=Pt(2))
add_notes(
    slide,
    "MindPulse demonstrates privacy-first stress detection is feasible. 46.8% F1 universal, 48.7% calibrated. Complete full-stack with honest evaluation. Next: real deployment, browser extension, multi-modal.",
)

# ===== SAVE =====
output = "D:/another-project/MindPulse_Review.pptx"
prs.save(output)
print(f"Saved: {output}")
print(f"Slides: {len(prs.slides)}")
