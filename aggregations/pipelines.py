"""
MongoDB Aggregation Pipelines for Recruitment Analytics
This module defines genuine, multi-stage aggregation pipelines for:
1. Candidate Outcome Analysis (Status distribution and score profiles)
2. Recruitment Strategy Analysis (Channel efficiency, hiring rates, and candidate volume)
3. Experience Tier Analysis (Performance breakdown across seniority levels)
4. Education Level Analysis (Degree tier outcomes and conversion metrics)

Each pipeline uses standard MongoDB stages: $match, $project, $group, and $sort.
"""
from typing import List, Dict, Any


def get_candidate_outcome_pipeline() -> List[Dict[str, Any]]:
    """
    Aggregation Pipeline 1: Candidate Outcome Distribution Analysis
    Groups candidates by final hiring outcome (Selected, Rejected, Pending),
    computes counts, and calculates average assessment scores for each outcome group.
    
    Stages:
    1. $match: Filter candidates with valid status values.
    2. $group: Group by status and compute total count, average interview,
               skill, and personality scores, plus average experience.
    3. $project: Format the final output document, rounding scores to 1 decimal place.
    4. $sort: Sort by count descending so the largest outcome category is first.
    """
    pipeline = [
        # Stage 1: $match - Filter candidates with valid status strings
        {
            "$match": {
                "status": {"$in": ["Selected", "Rejected", "Pending"]}
            }
        },
        # Stage 2: $group - Group documents by outcome status
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_interview_score": {"$avg": "$interview_score"},
                "avg_skill_score": {"$avg": "$skill_score"},
                "avg_personality_score": {"$avg": "$personality_score"},
                "avg_experience_years": {"$avg": "$experience_years"}
            }
        },
        # Stage 3: $project - Reshape fields and round computed averages
        {
            "$project": {
                "_id": 0,
                "status": "$_id",
                "count": 1,
                "avg_interview_score": {"$round": ["$avg_interview_score", 1]},
                "avg_skill_score": {"$round": ["$avg_skill_score", 1]},
                "avg_personality_score": {"$round": ["$avg_personality_score", 1]},
                "avg_experience_years": {"$round": ["$avg_experience_years", 1]}
            }
        },
        # Stage 4: $sort - Order by candidate count descending
        {
            "$sort": {
                "count": -1
            }
        }
    ]
    return pipeline


def get_recruitment_strategy_pipeline() -> List[Dict[str, Any]]:
    """
    Aggregation Pipeline 2: Recruitment Strategy Efficiency Analysis
    Analyzes hiring metrics across recruitment sourcing channels
    (Aggressive / Direct Sourcing, Moderate / Job Portals, Conservative / Campus & Referrals).
    
    Stages:
    1. $match: Ensure recruitment_strategy and status exist.
    2. $group: Group by strategy ID and strategy label, computing:
       - total applicants sourced
       - count of selected, rejected, and pending candidates
       - average scores and average commute distance
    3. $project: Compute selection rate percentage: (selected / (selected + rejected)) * 100
                 and round averages.
    4. $sort: Sort by strategy ID ascending (1: Aggressive, 2: Moderate, 3: Conservative).
    """
    pipeline = [
        # Stage 1: $match - Select documents with valid recruitment strategy
        {
            "$match": {
                "recruitment_strategy": {"$exists": True, "$ne": None},
                "status": {"$in": ["Selected", "Rejected", "Pending"]}
            }
        },
        # Stage 2: $group - Aggregate metrics per recruitment strategy
        {
            "$group": {
                "_id": {
                    "strategy_id": "$recruitment_strategy",
                    "strategy_label": "$strategy_label"
                },
                "total_candidates": {"$sum": 1},
                "selected_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "Selected"]}, 1, 0]
                    }
                },
                "rejected_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]
                    }
                },
                "pending_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "Pending"]}, 1, 0]
                    }
                },
                "avg_interview_score": {"$avg": "$interview_score"},
                "avg_skill_score": {"$avg": "$skill_score"},
                "avg_experience": {"$avg": "$experience_years"},
                "avg_distance": {"$avg": "$distance_from_company"}
            }
        },
        # Stage 3: $project - Compute conversion rates and round metrics
        {
            "$project": {
                "_id": 0,
                "strategy_id": "$_id.strategy_id",
                "strategy_label": {
                    "$ifNull": ["$_id.strategy_label", {"$concat": ["Strategy ", {"$toString": "$_id.strategy_id"}]}]
                },
                "total_candidates": 1,
                "selected_count": 1,
                "rejected_count": 1,
                "pending_count": 1,
                # Selection rate = (selected / (selected + rejected)) * 100
                "selection_rate": {
                    "$cond": [
                        {"$gt": [{"$add": ["$selected_count", "$rejected_count"]}, 0]},
                        {
                            "$round": [
                                {
                                    "$multiply": [
                                        {
                                            "$divide": [
                                                "$selected_count",
                                                {"$add": ["$selected_count", "$rejected_count"]}
                                            ]
                                        },
                                        100
                                    ]
                                },
                                1
                            ]
                        },
                        0.0
                    ]
                },
                "avg_interview_score": {"$round": ["$avg_interview_score", 1]},
                "avg_skill_score": {"$round": ["$avg_skill_score", 1]},
                "avg_experience": {"$round": ["$avg_experience", 1]},
                "avg_distance": {"$round": ["$avg_distance", 1]}
            }
        },
        # Stage 4: $sort - Order by strategy ID
        {
            "$sort": {
                "strategy_id": 1
            }
        }
    ]
    return pipeline


def get_experience_tier_pipeline() -> List[Dict[str, Any]]:
    """
    Aggregation Pipeline 3: Experience Tier Recruitment Analysis
    Categorizes candidates into seniority bands (Entry, Mid, Senior, Lead)
    using $switch within $project, then aggregates hiring metrics per tier.
    """
    pipeline = [
        # Stage 1: $match
        {
            "$match": {
                "experience_years": {"$exists": True, "$ne": None},
                "status": {"$in": ["Selected", "Rejected", "Pending"]}
            }
        },
        # Stage 2: $project - Categorize into experience tiers
        {
            "$project": {
                "status": 1,
                "interview_score": 1,
                "skill_score": 1,
                "tier": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lte": ["$experience_years", 2]}, "then": "Entry-Level (0-2 yrs)"},
                            {"case": {"$lte": ["$experience_years", 5]}, "then": "Mid-Level (3-5 yrs)"},
                            {"case": {"$lte": ["$experience_years", 9]}, "then": "Senior (6-9 yrs)"}
                        ],
                        "default": "Lead / Executive (10+ yrs)"
                    }
                },
                "tier_order": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lte": ["$experience_years", 2]}, "then": 1},
                            {"case": {"$lte": ["$experience_years", 5]}, "then": 2},
                            {"case": {"$lte": ["$experience_years", 9]}, "then": 3}
                        ],
                        "default": 4
                    }
                }
            }
        },
        # Stage 3: $group - Calculate counts and averages per tier
        {
            "$group": {
                "_id": {
                    "tier": "$tier",
                    "order": "$tier_order"
                },
                "total_candidates": {"$sum": 1},
                "selected_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Selected"]}, 1, 0]}
                },
                "rejected_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]}
                },
                "pending_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Pending"]}, 1, 0]}
                },
                "avg_interview_score": {"$avg": "$interview_score"},
                "avg_skill_score": {"$avg": "$skill_score"}
            }
        },
        # Stage 4: $project - Format final fields and selection rate
        {
            "$project": {
                "_id": 0,
                "tier": "$_id.tier",
                "tier_order": "$_id.order",
                "total_candidates": 1,
                "selected_count": 1,
                "rejected_count": 1,
                "pending_count": 1,
                "selection_rate": {
                    "$cond": [
                        {"$gt": [{"$add": ["$selected_count", "$rejected_count"]}, 0]},
                        {
                            "$round": [
                                {
                                    "$multiply": [
                                        {
                                            "$divide": [
                                                "$selected_count",
                                                {"$add": ["$selected_count", "$rejected_count"]}
                                            ]
                                        },
                                        100
                                    ]
                                },
                                1
                            ]
                        },
                        0.0
                    ]
                },
                "avg_interview_score": {"$round": ["$avg_interview_score", 1]},
                "avg_skill_score": {"$round": ["$avg_skill_score", 1]}
            }
        },
        # Stage 5: $sort - Order by tier order (Entry -> Mid -> Senior -> Lead)
        {
            "$sort": {
                "tier_order": 1
            }
        }
    ]
    return pipeline


def run_pipeline(collection, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executes a given aggregation pipeline on a PyMongo collection and returns documents as list.
    """
    cursor = collection.aggregate(pipeline)
    return list(cursor)
