"""Pipeline Analytics and Microarchitectural Instrumentation Package."""

from simulator.analytics.control_analytics import ControlSummary, analyze_control_flow
from simulator.analytics.event_tracker import DetailedPipelineEvent, EventTracker
from simulator.analytics.forwarding_analytics import ForwardingSummary, analyze_forwarding
from simulator.analytics.hazard_analytics import HazardSummary, analyze_hazards
from simulator.analytics.report_builder import PipelineAnalyticsReport, build_analytics_report
from simulator.analytics.stall_analytics import StallSummary, analyze_stalls

__all__ = [
    "DetailedPipelineEvent",
    "EventTracker",
    "HazardSummary",
    "StallSummary",
    "ForwardingSummary",
    "ControlSummary",
    "PipelineAnalyticsReport",
    "analyze_hazards",
    "analyze_stalls",
    "analyze_forwarding",
    "analyze_control_flow",
    "build_analytics_report",
]
