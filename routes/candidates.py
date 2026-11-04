"""
Candidate Management Routes
Demonstrates:
- insert_one() for individual candidate manual entry
- find() with filtering, pagination, and sorting
- update_one() to update candidate outcome status (e.g., from Pending to Selected/Rejected)
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from bson import ObjectId

from database.connection import get_db
from database.validators import (
    validate_and_sanitize_candidate,
    EDUCATION_MAPPING,
    STRATEGY_MAPPING
)

candidates_bp = Blueprint("candidates", __name__)


@candidates_bp.route("/api/candidates", methods=["GET"])
def list_candidates():
    """
    Retrieves candidates with optional status filter, search query, and pagination.
    Uses MongoDB find(), count_documents(), sort(), skip(), and limit().
    """
    try:
        db = get_db()
        candidates_col = db["candidates"]

        # Query parameters
        status_filter = request.args.get("status", "All").strip()
        search_query = request.args.get("search", "").strip()
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(5, int(request.args.get("per_page", 10))))

        # Build MongoDB filter query
        query = {}
        if status_filter in ["Selected", "Rejected", "Pending"]:
            query["status"] = status_filter

        if search_query:
            query["$or"] = [
                {"candidate_name": {"$regex": search_query, "$options": "i"}},
                {"candidate_id": {"$regex": search_query, "$options": "i"}},
                {"source": {"$regex": search_query, "$options": "i"}}
            ]

        total_matching = candidates_col.count_documents(query)
        total_pages = max(1, (total_matching + per_page - 1) // per_page)
        skip = (page - 1) * per_page

        cursor = candidates_col.find(
            query,
            {"fingerprint": 0}
        ).sort("created_at", -1).skip(skip).limit(per_page)

        candidates = []
        for doc in cursor:
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M")
            candidates.append(doc)

        return jsonify({
            "success": True,
            "data": candidates,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total_matching,
                "total_pages": total_pages
            }
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to retrieve candidates",
            "message": str(exc)
        }), 500


@candidates_bp.route("/api/candidates", methods=["POST"])
def add_candidate():
    """
    Adds a single candidate manually through the website.
    Demonstrates MongoDB insert_one().
    Allows the hiring outcome to be Pending when not yet finalized.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                "success": False,
                "error": "Missing JSON request body."
            }), 400

        # Validate and sanitize
        cleaned, error = validate_and_sanitize_candidate(data, source="manual_entry")
        if error:
            return jsonify({
                "success": False,
                "error": "Validation Error",
                "message": error
            }), 400

        db = get_db()
        candidates_col = db["candidates"]

        # Generate candidate ID if not provided
        if not cleaned["candidate_id"]:
            count = candidates_col.count_documents({}) + 1
            cleaned["candidate_id"] = f"CAND-{count:04d}"

        # Insert single document using PyMongo insert_one()
        insert_result = candidates_col.insert_one(cleaned)

        cleaned["_id"] = str(insert_result.inserted_id)
        if "created_at" in cleaned and hasattr(cleaned["created_at"], "isoformat"):
            cleaned["created_at"] = cleaned["created_at"].strftime("%Y-%m-%d %H:%M")

        # Exclude fingerprint from response
        cleaned.pop("fingerprint", None)

        return jsonify({
            "success": True,
            "message": "Candidate added successfully using insert_one()",
            "candidate": cleaned
        }), 201

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to add candidate",
            "message": str(exc)
        }), 500


@candidates_bp.route("/api/candidates/<candidate_id>/status", methods=["PATCH", "PUT"])
def update_candidate_status(candidate_id: str):
    """
    Updates a candidate's outcome status (e.g. from Pending to Selected or Rejected).
    Demonstrates MongoDB update_one().
    Once verified, candidate becomes eligible for future ML model training!
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        new_status = data.get("status", "").strip().capitalize()

        if new_status not in ["Selected", "Rejected", "Pending"]:
            return jsonify({
                "success": False,
                "error": "Invalid status. Must be 'Selected', 'Rejected', or 'Pending'."
            }), 400

        hiring_decision = 1 if new_status == "Selected" else (0 if new_status == "Rejected" else None)

        db = get_db()
        candidates_col = db["candidates"]

        # Locate by candidate_id string or ObjectId
        filter_query = {"candidate_id": candidate_id}
        if ObjectId.is_valid(candidate_id):
            filter_query = {"$or": [{"candidate_id": candidate_id}, {"_id": ObjectId(candidate_id)}]}

        update_fields = {
            "status": new_status,
            "hiring_decision": hiring_decision,
            "updated_at": datetime.now(timezone.utc)
        }

        # MongoDB update_one() execution
        result = candidates_col.update_one(
            filter_query,
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            return jsonify({
                "success": False,
                "error": f"Candidate '{candidate_id}' not found."
            }), 404

        return jsonify({
            "success": True,
            "message": f"Candidate status successfully updated to {new_status} via update_one()",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "new_status": new_status,
            "eligible_for_training": new_status in ["Selected", "Rejected"]
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to update candidate status",
            "message": str(exc)
        }), 500
