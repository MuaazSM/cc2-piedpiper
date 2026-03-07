"""
OptimizationOutcome ORM model.

Records the full result of every optimization run for historical tracking,
auditing, and ML model retraining. Each row captures:
- Which plan was generated
- What constraint violations were detected
- All scenario simulation results
- Final metrics (utilization, savings, etc.)
- Pipeline metadata (which solver was used, how long it took)

The retraining hook reads from this table — after N outcomes are logged,
it triggers the compatibility model to retrain using actual optimization
results as signal for what worked and what didn't.
"""

from sqlalchemy import Column, Integer, Float, Text, DateTime, String
from sqlalchemy.sql import func
from backend.app.db.base import Base


class OptimizationOutcome(Base):
    """
    One row per optimization run. Stores everything the Learn phase produces.

    All complex data (violations, scenarios, metrics, assignments) is stored
    as JSON strings in Text columns. This keeps the schema simple and avoids
    needing separate tables for each nested structure. SQLite and PostgreSQL
    both handle Text columns efficiently.
    """
    __tablename__ = "optimization_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp of when this outcome was recorded
    created_at = Column(DateTime, server_default=func.now())

    # Reference to the consolidation plan that was generated.
    # Nullable because the plan might not have been persisted yet
    # when the outcome is logged (or the run might have failed).
    plan_id = Column(Integer, nullable=True)

    # Which solver was used: "MIP", "HEURISTIC", or "NONE" if failed
    solver_used = Column(String, nullable=True)

    # Solver status: "OPTIMAL", "FEASIBLE", "INFEASIBLE", "TIMEOUT", etc.
    solver_status = Column(String, nullable=True)

    # Whether the solver found a feasible solution
    is_feasible = Column(Integer, default=1)  # 1=True, 0=False (SQLite friendly)

    # How many times the solver retried after infeasibility
    retry_count = Column(Integer, default=0)

    # --- Key metrics (stored as columns for easy querying) ---

    # Number of shipments in the input
    total_shipments = Column(Integer, nullable=True)

    # Number of vehicles available
    total_vehicles = Column(Integer, nullable=True)

    # Number of trucks used in the plan
    trucks_used = Column(Integer, nullable=True)

    # Average truck utilization (0-100)
    utilization_achieved = Column(Float, nullable=True)

    # Cost savings percentage vs baseline
    cost_saving_pct = Column(Float, nullable=True)

    # Carbon savings percentage vs baseline
    carbon_saving_pct = Column(Float, nullable=True)

    # Trip reduction percentage
    trip_reduction_pct = Column(Float, nullable=True)

    # Pipeline execution time in milliseconds
    pipeline_duration_ms = Column(Float, nullable=True)

    # --- JSON blobs for complex nested data ---

    # Full constraint violations list from guardrail + relaxation
    # Format: JSON array of violation dicts
    constraint_violations = Column(Text, nullable=True)

    # All 4 scenario simulation results
    # Format: JSON array of scenario result dicts
    scenario_results = Column(Text, nullable=True)

    # Full before/after metrics from the metrics engine
    # Format: JSON dict with before, after, savings, fleet, per_truck
    metrics_json = Column(Text, nullable=True)

    # Plan assignments (vehicle → shipment mappings)
    # Format: JSON array of assignment dicts
    assignments_json = Column(Text, nullable=True)

    # Compatibility graph stats
    # Format: JSON dict with pair counts, compatibility rate, etc.
    compatibility_stats = Column(Text, nullable=True)

    # Pipeline step timings
    # Format: JSON array of {step, status, duration_ms} dicts
    pipeline_steps = Column(Text, nullable=True)