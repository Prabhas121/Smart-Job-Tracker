"""
Data Validators and Sanitizers
Validates candidate records from CSV uploads and manual web entries before insertion.
"""
from datetime import datetime, timezone
import hashlib


EDUCATION_MAPPING = {
    1: "High School / Diploma",
    2: "Bachelor's Degree",
    3: "Master's Degree",
    4: "Doctorate (PhD)"
}

STRATEGY_MAPPING = {
    1: "Aggressive (Direct Sourcing)",
    2: "Moderate (Job Portals)",
    3: "Conservative (Campus/Referrals)"
}


def compute_record_fingerprint(record: dict) -> str:
    """
    Computes a deterministic hash fingerprint based on core applicant attributes.
    Used for safe duplicate prevention when the same CSV is uploaded repeatedly.
    """
    key_fields = [
        str(record.get("age", "")),
        str(record.get("gender", "")),
        str(record.get("education_level", "")),
        str(record.get("experience_years", "")),
        str(record.get("previous_companies", "")),
        str(round(float(record.get("distance_from_company", 0)), 2)),
        str(record.get("interview_score", "")),
        str(record.get("skill_score", "")),
        str(record.get("personality_score", "")),
        str(record.get("recruitment_strategy", ""))
    ]
    raw_str = "|".join(key_fields)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]


def validate_and_sanitize_candidate(data: dict, source: str = "manual_entry") -> tuple[dict | None, str | None]:
    """
    Validates, parses and cleans a single candidate record.
    Returns (cleaned_dict, None) on success, or (None, error_message) on failure.
    """
    try:
        # Age
        age = int(data.get("Age") if "Age" in data else data.get("age", 25))
        if not (18 <= age <= 75):
            return None, f"Age must be between 18 and 75, got {age}."

        # Gender (0 = Male, 1 = Female, default 0)
        gender_raw = data.get("Gender") if "Gender" in data else data.get("gender", 0)
        if str(gender_raw).strip().lower() in ["female", "f", "1"]:
            gender = 1
        else:
            gender = 0

        # Education Level (1 to 4)
        edu_raw = data.get("EducationLevel") if "EducationLevel" in data else data.get("education_level", 2)
        edu_val = int(edu_raw)
        if edu_val not in [1, 2, 3, 4]:
            return None, f"EducationLevel must be 1, 2, 3, or 4, got {edu_val}."

        # Experience Years (>= 0)
        exp_raw = data.get("ExperienceYears") if "ExperienceYears" in data else data.get("experience_years", 0)
        exp_years = float(exp_raw)
        if not (0 <= exp_years <= 50):
            return None, f"ExperienceYears must be between 0 and 50, got {exp_years}."

        # Previous Companies (>= 0)
        prev_raw = data.get("PreviousCompanies") if "PreviousCompanies" in data else data.get("previous_companies", 0)
        prev_comp = int(prev_raw)
        if not (0 <= prev_comp <= 30):
            return None, f"PreviousCompanies must be between 0 and 30, got {prev_comp}."

        # Distance From Company (>= 0)
        dist_raw = data.get("DistanceFromCompany") if "DistanceFromCompany" in data else data.get("distance_from_company", 10.0)
        distance = round(float(dist_raw), 2)
        if distance < 0:
            return None, f"DistanceFromCompany cannot be negative, got {distance}."

        # Interview Score (0 to 100)
        int_raw = data.get("InterviewScore") if "InterviewScore" in data else data.get("interview_score", 0)
        interview_score = float(int_raw)
        if not (0 <= interview_score <= 100):
            return None, f"InterviewScore must be between 0 and 100, got {interview_score}."

        # Skill Score (0 to 100)
        skill_raw = data.get("SkillScore") if "SkillScore" in data else data.get("skill_score", 0)
        skill_score = float(skill_raw)
        if not (0 <= skill_score <= 100):
            return None, f"SkillScore must be between 0 and 100, got {skill_score}."

        # Personality Score (0 to 100)
        pers_raw = data.get("PersonalityScore") if "PersonalityScore" in data else data.get("personality_score", 0)
        personality_score = float(pers_raw)
        if not (0 <= personality_score <= 100):
            return None, f"PersonalityScore must be between 0 and 100, got {personality_score}."

        # Recruitment Strategy (1 to 3)
        strat_raw = data.get("RecruitmentStrategy") if "RecruitmentStrategy" in data else data.get("recruitment_strategy", 2)
        strategy = int(strat_raw)
        if strategy not in [1, 2, 3]:
            return None, f"RecruitmentStrategy must be 1, 2, or 3, got {strategy}."

        # Hiring Decision / Status
        # Supported: 1 / "Selected", 0 / "Rejected", "Pending" / None / -1
        decision_raw = data.get("HiringDecision") if "HiringDecision" in data else data.get("hiring_decision")
        status_raw = data.get("status")

        if status_raw and str(status_raw).strip().capitalize() in ["Selected", "Rejected", "Pending"]:
            status = str(status_raw).strip().capitalize()
            hiring_decision = 1 if status == "Selected" else (0 if status == "Rejected" else None)
        elif decision_raw is not None and str(decision_raw).strip() != "":
            try:
                dec_val = int(float(str(decision_raw).strip()))
                if dec_val == 1:
                    status = "Selected"
                    hiring_decision = 1
                elif dec_val == 0:
                    status = "Rejected"
                    hiring_decision = 0
                else:
                    status = "Pending"
                    hiring_decision = None
            except ValueError:
                status = "Pending"
                hiring_decision = None
        else:
            status = "Pending"
            hiring_decision = None

        candidate_name = data.get("candidate_name", "").strip()
        candidate_id = data.get("candidate_id", "").strip()

        cleaned = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "age": age,
            "gender": gender,
            "education_level": edu_val,
            "education_label": EDUCATION_MAPPING.get(edu_val, f"Level {edu_val}"),
            "experience_years": round(exp_years, 1),
            "previous_companies": prev_comp,
            "distance_from_company": distance,
            "interview_score": round(interview_score, 1),
            "skill_score": round(skill_score, 1),
            "personality_score": round(personality_score, 1),
            "recruitment_strategy": strategy,
            "strategy_label": STRATEGY_MAPPING.get(strategy, f"Strategy {strategy}"),
            "hiring_decision": hiring_decision,
            "status": status,
            "source": source,
            "created_at": datetime.now(timezone.utc)
        }

        # Generate fingerprint for duplicate prevention
        cleaned["fingerprint"] = compute_record_fingerprint(cleaned)

        if not cleaned["candidate_name"]:
            cleaned["candidate_name"] = f"Candidate {cleaned['fingerprint'][:6].upper()}"

        return cleaned, None

    except Exception as exc:
        return None, f"Invalid data format: {str(exc)}"
