"""
Recruitment Analytics Routes
Executes genuine MongoDB aggregation pipelines and returns structured analytics
for visual rendering in Chart.js and statistical data tables.
"""
from flask import Blueprint, jsonify
from database.connection import get_db
from aggregations.pipelines import (
    get_candidate_outcome_pipeline,
    get_recruitment_strategy_pipeline,
    get_experience_tier_pipeline,
    run_pipeline
)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/outcome-distribution", methods=["GET"])
def get_outcome_distribution():
    """
    Aggregation Pipeline 1: Candidate outcome distribution analysis.
    Groups candidates by hiring outcome (Selected, Rejected, Pending),
    computing counts and score averages.
    """
    try:
        db = get_db()
        candidates_col = db["candidates"]
        pipeline = get_candidate_outcome_pipeline()
        results = run_pipeline(candidates_col, pipeline)

        return jsonify({
            "success": True,
            "pipeline_name": "Candidate Outcome Analysis",
            "stages_used": ["$match", "$group", "$project", "$sort"],
            "data": results
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to run outcome aggregation pipeline",
            "message": str(exc)
        }), 500


@analytics_bp.route("/api/analytics/strategy-efficiency", methods=["GET"])
def get_strategy_efficiency():
    """
    Aggregation Pipeline 2: Recruitment Strategy Efficiency Analysis.
    Calculates candidate volume, outcomes, conversion/selection rates,
    and average scores per recruitment channel.
    """
    try:
        db = get_db()
        candidates_col = db["candidates"]
        pipeline = get_recruitment_strategy_pipeline()
        results = run_pipeline(candidates_col, pipeline)

        return jsonify({
            "success": True,
            "pipeline_name": "Recruitment Strategy Efficiency",
            "stages_used": ["$match", "$group", "$project", "$sort"],
            "data": results
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to run strategy aggregation pipeline",
            "message": str(exc)
        }), 500


@analytics_bp.route("/api/analytics/experience-tiers", methods=["GET"])
def get_experience_tiers():
    """
    Aggregation Pipeline 3: Experience Tier Recruitment Analysis.
    Categorizes applicants into experience levels (Entry, Mid, Senior, Lead)
    and computes hiring conversion metrics.
    """
    try:
        db = get_db()
        candidates_col = db["candidates"]
        pipeline = get_experience_tier_pipeline()
        results = run_pipeline(candidates_col, pipeline)

        return jsonify({
            "success": True,
            "pipeline_name": "Experience Tier Analysis",
            "stages_used": ["$match", "$project ($switch)", "$group", "$project", "$sort"],
            "data": results
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to run experience tier aggregation pipeline",
            "message": str(exc)
        }), 500


@analytics_bp.route("/api/analytics/overview", methods=["GET"])
def get_analytics_overview():
    """
    Returns combined aggregation pipeline results for the Analytics dashboard tab.
    """
    try:
        db = get_db()
        candidates_col = db["candidates"]

        outcome_res = run_pipeline(candidates_col, get_candidate_outcome_pipeline())
        strategy_res = run_pipeline(candidates_col, get_recruitment_strategy_pipeline())
        tier_res = run_pipeline(candidates_col, get_experience_tier_pipeline())

        return jsonify({
            "success": True,
            "data": {
                "outcomes": outcome_res,
                "strategies": strategy_res,
                "experience_tiers": tier_res
            }
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to compute analytics overview",
            "message": str(exc)
        }), 500
