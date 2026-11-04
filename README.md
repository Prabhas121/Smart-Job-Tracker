# Smart Job Application Intelligence Dashboard

A modern, full-stack recruitment analytics and predictive intelligence web platform built from scratch. Powered by **MongoDB** for document storage and aggregation pipelines, and a **Random Forest Classifier (Scikit-Learn)** for hiring outcome prediction.

Designed specifically as an independent, modular, and professional **B.Tech Computer Science & Engineering Final-Year Capstone Project**.

---

## 1. Project Introduction

In contemporary talent acquisition, human resources departments process hundreds of candidate applications for competitive job openings. Traditional recruitment management systems act as passive repositories, storing candidate resumes without providing actionable intelligence. 

The **Smart Job Application Intelligence Dashboard** transforms raw applicant data into strategic recruitment intelligence. It allows recruiters to:
- Audit and bulk-import applicant datasets with automated schema validation and duplicate prevention.
- Compute multi-stage recruitment metrics using **native MongoDB aggregation pipelines** (`$match`, `$group`, `$project`, `$sort`).
- Interactively input candidate assessments and track evaluation statuses (`Pending`, `Selected`, `Rejected`).
- Predict candidate selection probability with high confidence using a trained **Random Forest Machine Learning model**, adhering to strict ethical AI guidelines (omitting demographic bias).

---

## 2. Problem Statement

Modern HR teams face key operational challenges:
1. **Data Inconsistency and Duplicates**: Repeated uploads of candidate CSV files cause duplicate records, inflating candidate numbers and distorting hiring metrics.
2. **Slow Analytic Processing**: Calculating conversion rates across sourcing channels and seniority tiers in application memory rather than at the database layer creates performance bottlenecks.
3. **Subjective Hiring Decisions**: Recruiters often lack data-backed benchmarks for assessing how a candidate's combination of interview, technical skill, and personality scores compares to historical hiring patterns.
4. **Demographic Bias in AI**: Many algorithmic screening tools inadvertently discriminate based on sensitive attributes such as gender or age.

---

## 3. Project Objectives

- **Database-Driven Analytics**: Implement high-performance, real-time analytics computed directly inside MongoDB using native aggregation pipelines rather than hardcoded metrics.
- **Robust Data Ingestion**: Provide an interactive CSV upload and validation workflow with PyMongo `insert_many()` bulk insertion and cryptographic fingerprint deduplication.
- **Candidate Lifecycle Management**: Support manual candidate entry using `insert_one()`, allow initial `Pending` outcomes, and update statuses using `update_one()` as interviews conclude.
- **Fair & Ethical Machine Learning**: Train an interpretable Random Forest classifier on real recruitment data while strictly omitting protected attributes (`Gender`) and preventing data leakage.
- **Intuitive Web Interface**: Deliver a clean, responsive single-page dashboard built with vanilla JavaScript, CSS3, and Chart.js without heavyweight frontend frameworks.

---

## 4. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        WEB BROWSER (CLIENT)                            │
│   HTML5 / CSS3 / Vanilla JavaScript / Chart.js Data Visualizations     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST API (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FLASK BACKEND CONTROLLER                          │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Dashboard APIs  │  │  Candidates APIs │  │   Dataset Import     │  │
│  │ (KPIs & Metrics) │  │(insert_one/find) │  │ (CSV & insert_many)  │  │
│  └─────────┬────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│            │                    │                       │              │
│  ┌─────────┴────────┐  ┌────────┴─────────┐             │              │
│  │  Analytics APIs  │  │ Prediction APIs  │             │              │
│  │(MongoDB Pipelines│  │ (RF Inference)   │             │              │
│  └─────────┬────────┘  └────────┬─────────┘             │              │
└────────────┼────────────────────┼───────────────────────┼──────────────┘
             │                    │                       │
             │                    ▼                       │
             │         ┌─────────────────────┐            │
             │         │   Scikit-Learn ML   │            │
             │         │RandomForest (Joblib)│            │
             │         └─────────────────────┘            │
             ▼                                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   MONGODB SERVER (localhost:27017)                     │
│                   Database: smartJobIntelligenceDB                     │
│                                                                        │
│   ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│   │     candidates      │  │ dataset_imports  │  │  model_versions  │  │
│   │ (Applicant Records) │  │  (Audit Logs)    │  │(Metrics & Params)│  │
│   └─────────────────────┘  └──────────────────┘  └──────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | HTML5 / CSS3 | Modern standards | Clean, responsive light-themed dashboard UI |
| **Frontend Scripting** | Vanilla JavaScript (ES6+) | Native | DOM manipulation, REST communication, state management |
| **Data Visualization** | Chart.js | 4.4.1 | Doughnut, bar, and dual-axis charts |
| **Backend Framework** | Python / Flask | 3.12 / 3.1.3 | RESTful API controllers and routing |
| **Database** | MongoDB Community Server | 7.0+ / 8.0+ | Document database storage and aggregation engine |
| **Database Driver** | PyMongo | 4.19.0 | Python MongoDB connector |
| **Machine Learning** | Scikit-Learn | 1.9.1 | Random Forest Classifier, stratified splits, evaluation |
| **Data Processing** | Pandas & NumPy | 3.1.0 / 2.5.4 | Dataset preprocessing, CSV parsing, matrix operations |
| **Model Persistence** | Joblib | 1.6.0 | Serializing and loading trained machine learning models |
| **Automated Testing** | Pytest | 9.2.0 | Unit and integration test suite (24 automated tests) |

---

## 6. Dataset Source and Description

- **Dataset Name**: Predicting Hiring Decisions in Recruitment Data
- **Original Author**: Rabie El Kharoua
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Source**: Kaggle Public Dataset Repository
- **Total Records**: 1,500 candidate applications (Clean baseline, 0 missing values, 0 duplicates)
- **Target Variable**: `HiringDecision` (0: Not Hired / Rejected, 1: Hired / Selected)

### Feature Attributes & Descriptions

| Feature Name | Type | Value Range | Recruiter Definition |
|---|---|---|---|
| `Age` | Numerical | 20 – 50 | Age of applicant in years |
| `Gender` | Categorical | 0 (Male), 1 (Female) | **Excluded from ML model** to enforce non-discriminatory ethical AI standards |
| `EducationLevel` | Categorical | 1, 2, 3, 4 | 1: High School, 2: Bachelor's, 3: Master's, 4: PhD |
| `ExperienceYears` | Numerical | 0.0 – 15.0 | Total years of relevant professional experience |
| `PreviousCompanies` | Numerical | 1 – 5 | Number of previous companies worked at |
| `DistanceFromCompany` | Numerical | 1.0 – 50.0 km | Distance from candidate residence to office in km |
| `InterviewScore` | Numerical | 0 – 100 | Score achieved in technical and HR interview rounds |
| `SkillScore` | Numerical | 0 – 100 | Score from pre-employment technical assessments |
| `PersonalityScore` | Numerical | 0 – 100 | Psychometric and cultural alignment rating |
| `RecruitmentStrategy` | Categorical | 1, 2, 3 | 1: Aggressive (Headhunting), 2: Moderate (Portals), 3: Conservative (Campus/Referrals) |
| `HiringDecision` | Target | 0 or 1 | 0: Rejected, 1: Selected |

---

## 7. MongoDB Database & Collections

The application runs on a dedicated, isolated database: **`smartJobIntelligenceDB`**.

### Collections:
1. **`candidates`**: Stores both imported and manually entered applicant profiles. Includes fields: `candidate_id`, `candidate_name`, `age`, `gender`, `education_level`, `experience_years`, `previous_companies`, `distance_from_company`, `interview_score`, `skill_score`, `personality_score`, `recruitment_strategy`, `hiring_decision`, `status` (`Selected`, `Rejected`, `Pending`), `source` (`real_dataset` or `manual_entry`), and `fingerprint`.
2. **`dataset_imports`**: Audit log recording CSV uploads, file names, timestamps, total rows, inserted counts, and skipped duplicate counts.
3. **`model_versions`**: Records trained ML model versions (`v1.0.0`), training timestamps, hyperparameter settings, dataset sample counts, and evaluation metrics.

---

## 8. Explanation of `insert_one()` and `insert_many()`

### PyMongo `insert_one()`
Used when a recruiter manually enters an applicant's details through the website (**Add Candidate** page).
```python
# database/candidates.py
insert_result = candidates_col.insert_one(cleaned_document)
generated_id = insert_result.inserted_id
```
- Inserts a single document atomically.
- Allows candidates to be registered as `Pending` before interview outcomes are finalized.

### PyMongo `insert_many()`
Used during CSV dataset uploads (**Dataset Management** page) for high-performance bulk ingestion.
```python
# routes/dataset.py
insert_result = candidates_col.insert_many(documents_to_insert, ordered=False)
inserted_count = len(insert_result.inserted_ids)
```
- Sends multiple BSON documents to MongoDB in a single network packet rather than individual round trips.
- `ordered=False` allows valid documents to continue inserting even if an individual document encounters a unique constraint violation.
- **Safe Duplicate Prevention**: Before calling `insert_many()`, candidate documents are checked against existing SHA-256 fingerprints to ensure existing records are skipped without silent duplicates.

---

## 9. Explanation of MongoDB Aggregation Pipelines

All recruitment statistics are computed directly inside MongoDB using multi-stage aggregation pipelines defined in `aggregations/pipelines.py`.

### Aggregation Pipeline 1: Candidate Outcome Analysis
Computes count distribution and score profiles across `Selected`, `Rejected`, and `Pending` candidate groups.
```python
pipeline = [
    # Stage 1: $match - Filter candidates with valid status values
    {"$match": {"status": {"$in": ["Selected", "Rejected", "Pending"]}}},
    
    # Stage 2: $group - Group by outcome status and compute average scores
    {"$group": {
        "_id": "$status",
        "count": {"$sum": 1},
        "avg_interview_score": {"$avg": "$interview_score"},
        "avg_skill_score": {"$avg": "$skill_score"},
        "avg_personality_score": {"$avg": "$personality_score"},
        "avg_experience_years": {"$avg": "$experience_years"}
    }},
    
    # Stage 3: $project - Reshape output document and round averages
    {"$project": {
        "_id": 0,
        "status": "$_id",
        "count": 1,
        "avg_interview_score": {"$round": ["$avg_interview_score", 1]},
        "avg_skill_score": {"$round": ["$avg_skill_score", 1]},
        "avg_personality_score": {"$round": ["$avg_personality_score", 1]}
    }},
    
    # Stage 4: $sort - Sort by candidate volume descending
    {"$sort": {"count": -1}}
]
```

### Aggregation Pipeline 2: Recruitment Strategy Efficiency
Analyzes hiring conversion metrics per recruitment sourcing channel.
```python
pipeline = [
    # Stage 1: $match - Ensure strategy exists
    {"$match": {"recruitment_strategy": {"$exists": True, "$ne": None}}},
    
    # Stage 2: $group - Aggregate candidate counts and outcome conditions
    {"$group": {
        "_id": {
            "strategy_id": "$recruitment_strategy",
            "strategy_label": "$strategy_label"
        },
        "total_candidates": {"$sum": 1},
        "selected_count": {"$sum": {"$cond": [{"$eq": ["$status", "Selected"]}, 1, 0]}},
        "rejected_count": {"$sum": {"$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]}},
        "avg_interview_score": {"$avg": "$interview_score"},
        "avg_skill_score": {"$avg": "$skill_score"}
    }},
    
    # Stage 3: $project - Calculate selection rate percentage: (selected / (selected + rejected)) * 100
    {"$project": {
        "_id": 0,
        "strategy_id": "$_id.strategy_id",
        "strategy_label": "$_id.strategy_label",
        "total_candidates": 1,
        "selected_count": 1,
        "rejected_count": 1,
        "selection_rate": {
            "$cond": [
                {"$gt": [{"$add": ["$selected_count", "$rejected_count"]}, 0]},
                {"$round": [
                    {"$multiply": [
                        {"$divide": ["$selected_count", {"$add": ["$selected_count", "$rejected_count"]}]},
                        100
                    ]},
                    1
                ]},
                0.0
            ]
        }
    }},
    
    # Stage 4: $sort - Order by strategy ID
    {"$sort": {"strategy_id": 1}}
]
```

---

## 10. Machine Learning Algorithm & Prediction Target

- **Algorithm**: `RandomForestClassifier` (Scikit-Learn Ensemble)
- **Hyperparameters**: `n_estimators=100`, `max_depth=10`, `min_samples_split=4`, `class_weight='balanced'`, `random_state=42`.
- **Target**: `HiringDecision` (1 = Selected, 0 = Rejected).
- **Features Used**: `EducationLevel`, `ExperienceYears`, `PreviousCompanies`, `DistanceFromCompany`, `InterviewScore`, `SkillScore`, `PersonalityScore`, `RecruitmentStrategy`.
- **Ethical AI Guarantee**: Sensitive demographic features such as `Gender` are **excluded** to eliminate demographic proxy bias.
- **Data Leakage Safeguard**: Candidates with `Pending` status are excluded from training until verified by a recruiter.

---

## 11. Model Evaluation Results

Evaluated on an independent stratified test split (20% holdout, 300 test candidates):

| Metric | Score | Faculty Explanation |
|---|---|---|
| **Accuracy** | **93.67%** | Overall correct predictions out of total holdout cases |
| **Precision** | **0.9111** | True positive rate among all candidates predicted as Selected |
| **Recall** | **0.8817** | Proportion of actual Selected candidates correctly identified |
| **F1-Score** | **0.8962** | Harmonic mean of precision and recall |
| **ROC-AUC** | **0.9335** | Area under the Receiver Operating Characteristic curve |

### 2x2 Confusion Matrix (300 Test Samples)
```
                          Predicted: Rejected     Predicted: Selected
Actual: Rejected (0)             199 (TN)                  8 (FP)
Actual: Selected (1)              11 (FN)                 82 (TP)
```

### Feature Importance Weights
1. **Recruitment Strategy**: 34.3%
2. **Technical Skill Score**: 12.8%
3. **Personality / Cultural Fit**: 12.7%
4. **Interview Score**: 12.2%
5. **Education Level**: 10.1%
6. **Experience in Years**: 7.9%
7. **Commute Distance**: 7.2%
8. **Previous Companies**: 2.8%

---

## 12. How to Install Dependencies

### Prerequisites
- macOS, Linux, or Windows with **Python 3.10+** (Python 3.12 recommended).
- **MongoDB Community Server** installed and running locally on port `27017`.

### Setup Steps
```bash
# 1. Navigate to the project directory
cd ~/Desktop/Smart-Job-Application-Intelligence-Dashboard

# 2. Create Python virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install required dependencies
pip install -r requirements.txt
```

---

## 13. How to Configure MongoDB

Create or verify the `.env` configuration file in the project root:
```env
# MongoDB Connection (Isolated for Smart Job Application Intelligence Dashboard)
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=smartJobIntelligenceDB
TEST_DATABASE_NAME=smartJobIntelligenceDB_test

# Flask Application Settings
PORT=5001
DEBUG=True
SECRET_KEY=smart-job-intelligence-super-secret-key-3.12
```

> **Note on Database Isolation**: The application strictly validates database connections so it will never touch or interfere with any other database on your MongoDB server.

---

## 14. How to Run the Project

### Step 1: Start MongoDB
Ensure the MongoDB server daemon is running:
```bash
# macOS (if installed via brew / standard path):
/usr/local/mongodb/bin/mongod --dbpath ~/data/db
# or via brew service:
# brew services start mongodb-community
```

### Step 2: Start the Flask Application
```bash
cd ~/Desktop/Smart-Job-Application-Intelligence-Dashboard
source venv/bin/activate
python3 app.py
```

Open your browser and navigate to:
**`http://127.0.0.1:5001`**

### Step 3: Run Automated Tests
```bash
cd ~/Desktop/Smart-Job-Application-Intelligence-Dashboard
source venv/bin/activate
PYTHONPATH=. pytest -v
```
All **24 automated unit and integration tests** will execute and pass.

---

## 15. College Faculty Demonstration Sequence

When presenting this project to your university faculty or external examiner, follow this 5-minute walkthrough:

1. **Overview Page (`http://127.0.0.1:5001`)**:
   - Highlight the live KPI cards: Total Candidates (1,500), Selected (465), Rejected (1,035), Selection Rate (31.0%).
   - Explain that all values are fetched dynamically from MongoDB collection `candidates`.
   - Point out the recent candidates table and Chart.js doughnut chart.
2. **Dataset Management Tab**:
   - Click **Download Sample CSV** to demonstrate the file structure.
   - Drag & drop or select a CSV to demonstrate the automated pre-import audit (rows, columns, null check, schema check).
   - Explain the PyMongo `insert_many()` bulk insertion with SHA-256 fingerprint deduplication.
3. **Add Candidate Tab**:
   - Enter a new applicant (e.g., "Aarav Sharma", 5 years experience, Interview: 88, Skill: 92, Strategy: Aggressive, Outcome: **Pending**).
   - Submit the form and explain PyMongo `insert_one()`.
   - Show how the overview dashboard immediately updates to reflect 1 Pending candidate.
4. **Candidate Directory Tab**:
   - Locate the Pending candidate.
   - Click the green **Select** button.
   - Explain how PyMongo `update_one()` modifies the status in MongoDB, making the record eligible for future ML retraining.
5. **Recruitment Analytics Tab**:
   - Walk faculty through the two genuine MongoDB aggregation pipelines (`get_candidate_outcome_pipeline` and `get_recruitment_strategy_pipeline`).
   - Explain how `$match`, `$group`, `$project`, and `$sort` stages process data directly on the database engine.
6. **ML Hiring Prediction Tab**:
   - Review model evaluation metrics: **93.67% Accuracy**, **0.9111 Precision**, and the 2x2 Confusion Matrix.
   - Demonstrate real-time inference: enter scores and click **Predict Hiring Outcome**.
   - Show the resulting outcome badge, confidence probability bar, and key factors list.
   - Emphasize the **Ethical AI Disclaimer** and explain that sensitive attributes like `Gender` were intentionally excluded to prevent bias.
