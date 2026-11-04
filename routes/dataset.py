"""
Dataset Management Routes
Demonstrates:
- CSV upload, validation, parsing, and preview
- Checking missing values, duplicates, and schema validation
- MongoDB bulk insertion using PyMongo insert_many()
- Safe duplicate prevention using applicant fingerprints
- Import history logging in dataset_imports collection
"""
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
import pandas as pd
from werkzeug.utils import secure_filename

from config import Config
from database.connection import get_db
from database.validators import (
    validate_and_sanitize_candidate,
    compute_record_fingerprint
)

dataset_bp = Blueprint("dataset", __name__)

ALLOWED_EXTENSIONS = {"csv"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@dataset_bp.route("/api/dataset/upload", methods=["POST"])
def upload_and_validate_csv():
    """
    Accepts CSV upload, inspects structure, computes row/column counts,
    identifies missing values and internal duplicates, validates required fields,
    and returns a preview (first 8 rows) with valid/invalid record counts.
    """
    try:
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No file uploaded. Please select a recruitment CSV file."
            }), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({
                "success": False,
                "error": "Empty filename."
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Invalid file type. Only .csv files are supported."
            }), 400

        # Save to uploads directory
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        safe_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{timestamp}_{safe_name}"
        saved_path = Config.UPLOAD_FOLDER / saved_filename
        file.save(saved_path)

        # Parse CSV with pandas
        try:
            df = pd.read_csv(saved_path)
        except Exception as read_err:
            return jsonify({
                "success": False,
                "error": f"Failed to parse CSV file: {str(read_err)}"
            }), 400

        total_rows, total_cols = df.shape
        missing_count = int(df.isnull().sum().sum())
        csv_duplicates = int(df.duplicated().sum())
        columns = list(df.columns)

        # Expected core fields (flexible casing)
        expected_candidates = {
            "InterviewScore", "SkillScore", "EducationLevel",
            "ExperienceYears", "RecruitmentStrategy"
        }
        lower_cols = {c.lower() for c in columns}
        missing_required_cols = [
            req for req in expected_candidates
            if req.lower() not in lower_cols
        ]

        # Preview first 8 rows
        preview_data = df.head(8).fillna("").to_dict(orient="records")

        # Row-level validation simulation
        valid_count = 0
        invalid_count = 0
        invalid_samples = []

        for idx, row in df.iterrows():
            record = row.to_dict()
            cleaned, error = validate_and_sanitize_candidate(record, source="real_dataset")
            if cleaned is not None:
                valid_count += 1
            else:
                invalid_count += 1
                if len(invalid_samples) < 5:
                    invalid_samples.append({
                        "row_number": idx + 2,  # 1-indexed header offset
                        "reason": error
                    })

        return jsonify({
            "success": True,
            "data": {
                "filename": saved_filename,
                "original_name": safe_name,
                "total_rows": total_rows,
                "total_columns": total_cols,
                "columns": columns,
                "missing_values_count": missing_count,
                "csv_duplicates_count": csv_duplicates,
                "missing_required_fields": missing_required_cols,
                "is_schema_valid": len(missing_required_cols) == 0,
                "valid_records_count": valid_count,
                "invalid_records_count": invalid_count,
                "invalid_samples": invalid_samples,
                "preview_rows": preview_data
            }
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Dataset processing failed",
            "message": str(exc)
        }), 500


@dataset_bp.route("/api/dataset/import", methods=["POST"])
def bulk_import_dataset():
    """
    Converts valid CSV records into MongoDB candidate documents and performs
    bulk insertion using PyMongo insert_many().
    Safely avoids duplicate records using applicant fingerprints.
    Records import event in dataset_imports collection.
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        filename = payload.get("filename")

        if not filename:
            # Default to bundled recruitment_data.csv if none specified
            csv_path = Config.DEFAULT_DATASET_PATH
            import_source_name = "recruitment_data.csv (Official Dataset)"
        else:
            csv_path = Config.UPLOAD_FOLDER / secure_filename(filename)
            import_source_name = secure_filename(filename)

        if not csv_path.exists():
            return jsonify({
                "success": False,
                "error": f"Dataset file '{csv_path.name}' not found on server."
            }), 404

        df = pd.read_csv(csv_path)
        total_rows = len(df)

        db = get_db()
        candidates_col = db["candidates"]
        imports_col = db["dataset_imports"]

        # Fetch existing fingerprints from database to guarantee safe duplicate prevention
        existing_fps = set(candidates_col.distinct("fingerprint"))

        documents_to_insert = []
        skipped_duplicate_count = 0
        invalid_count = 0

        current_count = candidates_col.count_documents({})

        for idx, row in df.iterrows():
            record = row.to_dict()
            cleaned, error = validate_and_sanitize_candidate(record, source="real_dataset")

            if error:
                invalid_count += 1
                continue

            fp = cleaned["fingerprint"]
            if fp in existing_fps:
                skipped_duplicate_count += 1
                continue

            # Assign sequential candidate identifier
            current_count += 1
            cleaned["candidate_id"] = f"CAND-{current_count:05d}"

            documents_to_insert.append(cleaned)
            existing_fps.add(fp)

        # Bulk insertion using PyMongo insert_many()
        inserted_count = 0
        if documents_to_insert:
            # ordered=False allows valid documents to continue inserting even if a single one encounters an issue
            insert_result = candidates_col.insert_many(documents_to_insert, ordered=False)
            inserted_count = len(insert_result.inserted_ids)

        # Log import event in dataset_imports collection
        import_record = {
            "source_file": import_source_name,
            "total_rows": total_rows,
            "valid_records": len(documents_to_insert) + skipped_duplicate_count,
            "invalid_records": invalid_count,
            "inserted_count": inserted_count,
            "skipped_duplicates": skipped_duplicate_count,
            "imported_at": datetime.now(timezone.utc),
            "status": "completed" if inserted_count > 0 or skipped_duplicate_count > 0 else "empty"
        }
        imports_col.insert_one(import_record)

        return jsonify({
            "success": True,
            "message": (
                f"Dataset import complete: {inserted_count} new candidate documents inserted into MongoDB "
                f"using insert_many(). {skipped_duplicate_count} duplicate records safely skipped."
            ),
            "import_summary": {
                "source_file": import_source_name,
                "total_rows": total_rows,
                "inserted_count": inserted_count,
                "skipped_duplicates": skipped_duplicate_count,
                "invalid_count": invalid_count,
                "database_total_candidates": candidates_col.count_documents({})
            }
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Bulk import failed",
            "message": str(exc)
        }), 500


@dataset_bp.route("/api/dataset/history", methods=["GET"])
def get_import_history():
    """
    Returns history of CSV imports from dataset_imports collection.
    """
    try:
        db = get_db()
        imports_col = db["dataset_imports"]

        cursor = imports_col.find(
            {},
            {"_id": 0}
        ).sort("imported_at", -1).limit(20)

        history = []
        for doc in cursor:
            if "imported_at" in doc and hasattr(doc["imported_at"], "isoformat"):
                doc["imported_at"] = doc["imported_at"].strftime("%Y-%m-%d %H:%M:%S")
            history.append(doc)

        return jsonify({
            "success": True,
            "data": history
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to fetch import history",
            "message": str(exc)
        }), 500


@dataset_bp.route("/api/dataset/sample", methods=["GET"])
def download_sample_dataset():
    """
    Provides sample recruitment CSV for testing.
    """
    if Config.DEFAULT_DATASET_PATH.exists():
        return send_file(
            Config.DEFAULT_DATASET_PATH,
            as_attachment=True,
            download_name="recruitment_dataset_sample.csv",
            mimetype="text/csv"
        )
    return jsonify({"success": False, "error": "Sample dataset file not available"}), 404
