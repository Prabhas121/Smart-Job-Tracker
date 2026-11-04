# Dataset Documentation

## Dataset Name
**Predicting Hiring Decisions in Recruitment Data**

## Source and Provenance
- **Original Author**: Rabie El Kharoua
- **Original Source**: Kaggle Dataset (`rabieelkharoua/predicting-hiring-decisions-in-recruitment-data`)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Permissions**: Free to share, copy, distribute, transform, and build upon for any purpose (academic or commercial) with attribution.

## Dataset Overview
- **Total Records**: 1,500 candidate applications
- **Total Features**: 10 input attributes + 1 target variable
- **Missing Values**: 0 (Clean baseline dataset)
- **Duplicate Records**: 0
- **Classification Target**: `HiringDecision`
  - `0`: Not Hired / Rejected (1,035 candidates, ~69.0%)
  - `1`: Hired / Selected (465 candidates, ~31.0%)

## Feature Definitions
| Feature Name | Type | Range / Values | Description |
|---|---|---|---|
| `Age` | Numerical | 20 – 50 | Age of the candidate |
| `Gender` | Categorical | 0 (Male), 1 (Female) | Candidate gender (*excluded from ML model features to prevent demographic bias and maintain ethical AI standards*) |
| `EducationLevel` | Categorical | 1, 2, 3, 4 | 1: High School / Diploma, 2: Bachelor's Degree, 3: Master's Degree, 4: PhD |
| `ExperienceYears` | Numerical | 0 – 15 | Total professional experience in years |
| `PreviousCompanies`| Numerical | 1 – 5 | Number of previous companies worked at |
| `DistanceFromCompany` | Numerical | 1.0 – 50.0 km | Distance from candidate residence to office in kilometers |
| `InterviewScore` | Numerical | 0 – 100 | Technical and behavioral interview evaluation score |
| `SkillScore` | Numerical | 0 – 100 | Pre-employment assessment and technical test score |
| `PersonalityScore` | Numerical | 0 – 100 | Psychometric and cultural fit assessment score |
| `RecruitmentStrategy` | Categorical | 1, 2, 3 | Sourcing channel / pipeline style: 1: Aggressive (Headhunting/Direct), 2: Moderate (Job Portals/Agencies), 3: Conservative (Campus/Internal Referrals) |
| `HiringDecision` | Binary Target | 0 or 1 | 0: Rejected, 1: Selected |

## Ethical AI & Fairness Safeguards
- In accordance with AI ethics guidelines, sensitive personal attributes such as `Gender` are **omitted from the predictive feature set** to avoid proxy bias.
- The machine learning model uses merit-based performance indicators (`SkillScore`, `InterviewScore`, `PersonalityScore`, `ExperienceYears`, `EducationLevel`, `PreviousCompanies`, `DistanceFromCompany`, `RecruitmentStrategy`).
