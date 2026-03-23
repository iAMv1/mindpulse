# MindPulse Project Status & Knowledge Base

## Project Overview
MindPulse is a privacy-first behavioral stress detection system that predicts stress from interaction patterns (keyboard timing, mouse behavior, app-switch dynamics).

## Current State: DONE ✅

| Component | File | Status |
|-----------|------|--------|
| Data Collector | `tmp_repo/data_collector.py` | ✅ Thread-safe, privacy-safe, press-release pairing |
| Feature Extractor | `tmp_repo/feature_extractor.py` | ✅ 23 features (keyboard 11, mouse 6, context 3, temporal 3) |
| Synthetic Data Gen | `tmp_repo/synthetic_data.py` | ✅ Research-backed distributions |
| XGBoost Model | `tmp_repo/model.py` | ✅ DualNormalizer, PersonalBaseline, hardened load |
| Evaluation | `tmp_repo/evaluate_model.py` | ✅ Real CSV + synthetic modes |
| Dashboard | `tmp_repo/app.py` | ✅ Streamlit MVP with live tracking |
| Research Docs | `stress_detection_research.md` | ✅ Complete |
| ML Pipeline Docs | `ml_pipeline_part1_*.md`, `ml_pipeline_part2_*.md` | ✅ Complete |

## Current Eval (Synthetic Only - Inflated)
- Accuracy: 99.7%
- F1 Macro: 99.6%
- **Problem**: Trained on synthetic, tested on synthetic from same distribution

## PENDING (Priority Order)

### 1. Real Dataset - CMU Keystroke Stress Dataset
- 116 subjects, neutral + stressed states
- Hold/flight timings, demographic/psychological data
- Available from CMU InfSci

### 2. Retrain on Real Data
- Replace synthetic training with CMU data
- Expect real accuracy: 65-75% (per literature)

### 3. Stratified Group K-Fold Evaluation
- Currently uses random split (data leakage risk)
- Need user-level held-out validation

### 4. 1D-CNN Branch
- Designed in Part 2, not implemented
- Captures local temporal patterns (digraphs/trigraphs)

### 5. MindPulse-Former (Transformer)
- Circadian Embedding + attention
- Novel component, designed but not coded

### 6. Meta-Learner
- 3-branch ensemble combiner
- Designed, not implemented

### 7. Next.js Frontend
- Port from Streamlit to production UI
- Use AlgoQuest components as base

---

## AlgoQuest Integration Analysis

### AlgoQuest Frontend (algoquest-frontend)
- Next.js 16 + TypeScript + Tailwind + shadcn/ui
- D3.js network visualization, Recharts, Framer Motion
- Real-time WebSocket updates
- Key reusable components:
  - `RiskMeter` - Visual risk level gauge
  - `TimelineChart` - Historical trend charts
  - `MetricCard` - KPI display cards
  - `WebSocketStatus` - Connection indicator
  - `NetworkGraph` - D3 force-directed graph
  - `CultureThermometer` - Team health gauge

### AlgoQuest Backend (algoquest-backend)
- FastAPI + SQLAlchemy + PostgreSQL
- Three Engines:
  1. Safety Valve: sentiment velocity, circadian entropy, belongingness
  2. Talent Scout: betweenness/eigenvector centrality, unblocking count
  3. Culture Thermometer: graph fragmentation, contagion risk
- Two-Vault Privacy: Vault A (analytics hashes) + Vault B (encrypted identity)
- Simulation personas: alex_burnout, sarah_gem, jordan_steady, maria_contagion

### How AlgoQuest Helps MindPulse
| AlgoQuest | MindPulse Use |
|-----------|---------------|
| Safety Valve engine | Blueprint for stress detection architecture |
| Network centrality | Features #24-26 for team-aware stress |
| Simulation personas | Generate labeled edge-case training data |
| Next.js UI components | Production dashboard replacement |
| WebSocket pattern | Real-time stress updates |
| Two-Vault privacy | Enterprise deployment pattern |

---

## Available Datasets (Research Document)
1. CMU Keystroke Stress Dataset - 116 subjects
2. OSF Work Stress Dataset - ~50 subjects, mouse+keyboard+HRV
3. Multimodal Stress Dataset - 30 participants
4. KeyRecs - 100 participants
5. IKDD - 164 volunteers

## Novel Features (Competitive Edge)
1. Rage clicks / dead clicks (UX → stress biomarkers)
2. Scroll depth/velocity patterns
3. Hesitation mapping (pre-click hover time)
4. Context-switch entropy
5. Circadian rhythm deviation detection
6. Digital Stress Phenotype score (0-100 composite)
7. Micro-break quality classification
8. Typing rhythm entropy (Shannon entropy of inter-key intervals)
9. Mouse gesture vocabulary

## Feature Vector (23 raw → 46 after DualNormalizer)
Keyboard (11): hold_time_mean/std/median, flight_time_mean/std, typing_speed_wpm, error_rate, pause_frequency/duration_mean, burst_length_mean, rhythm_entropy
Mouse (6): mouse_speed_mean/std, direction_change_rate, click_count, rage_click_count, scroll_velocity_std
Context (3): tab_switch_freq, switch_entropy, session_fragmentation
Temporal (3): hour_of_day, day_of_week, session_duration_min

## Model Architecture (Designed)
- Branch 1: XGBoost (tabular, 46 features)
- Branch 2: 1D-CNN (raw timing sequences, 4 channels)
- Branch 3: MindPulse-Former (Transformer + circadian embedding)
- Meta-Learner: learned weighted combination
- Target: F1 > 0.70, AUC > 0.80 on real data

## Deployment
- ONNX Runtime (INT8 quantized: 0.7MB, 4ms inference)
- 100% local processing
- SQLite for baselines
- Streamlit MVP → Electron/React production
