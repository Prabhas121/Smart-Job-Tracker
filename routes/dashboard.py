"""
Dashboard Summary Routes
Computes real-time overview metrics and distributions directly from MongoDB.
"""
from flask import Blueprint, jsonify
from database.connection import get_db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/summary", methods=["GET"])
def get_dashboard_summary():
    """
    Computes primary KPI metrics from MongoDB:
    - Total candidates
    - Selected count
    - Rejected count
    - Pending count
    - Selection rate (%)
    - Recent candidates table (last 8 records)
    """
    try:
        db = get_db()
        candidates_col = db["candidates"]

        # Counts by status
        total_candidates = candidates_col.count_documents({})
        selected_count = candidates_col.count_documents({"status": "Selected"})
        rejected_count = candidates_col.count_documents({"status": "Rejected"})
        pending_count = candidates_col.count_documents({"status": "Pending"})

        # Selection Rate: (Selected / (Selected + Rejected)) * 100
        decided_count = selected_count + rejected_count
        if decided_count > 0:
            selection_rate = round((selected_count / decided_count) * 100, 1)
        else:
            selection_rate = 0.0

        # Recent candidates (most recent 8 documents)
        cursor = candidates_col.find(
            {},
            {"_id": 0, "fingerprint": 0}
        ).sort("created_at", -1).limit(8)
        recent_candidates = []
        for doc in cursor:
            # Format datetime for JSON serialization
            if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M")
            recent_candidates.append(doc)

        # Dataset imports count
        total_imports = db["dataset_imports"].count_documents({})

        # Latest model version
        latest_model = db["model_versions"].find_one(
            {},
            {"_id": 0, "version": 1, "metrics.accuracy_pct": 1, "trained_at": 1},
            sort=[("trained_at", -1)]
        )

        return jsonify({
            "success": True,
            "data": {
                "total_candidates": total_candidates,
                "selected_count": selected_count,
                "rejected_count": rejected_count,
                "pending_count": pending_count,
                "selection_rate": selection_rate,
                "decided_count": decided_count,
                "total_imports": total_imports,
                "latest_model": latest_model,
                "recent_candidates": recent_candidates
            }
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to fetch dashboard metrics",
            "message": str(exc)
        }), 500
