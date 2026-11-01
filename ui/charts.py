"""Plotly figures: the pipeline timing diagram and performance charts.  (Member 6)"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import plotly.graph_objects as go

from simulator.models import STAGES, SimulationResult

# Exact Pipeline Stage Colors specified in Midnight Engineering tokens:
STAGE_COLORS: Dict[str, str] = {
    "IF": "#3B82F6",   # Core Blue
    "ID": "#8B5CF6",   # Deep Violet
    "EX": "#F59E0B",   # Warm Amber
    "MEM": "#06B6D4",  # Cyan Blue
    "WB": "#10B981",   # Emerald Green
}
STALL_COLOR = "#EF4444"       # Red
BUBBLE_COLOR = "#64748B"      # Muted Slate
FORWARDING_COLOR = "#22D3EE"  # Primary Cyan Accent
FLUSH_COLOR = "#F43F5E"       # Rose Red
FORWARD_ON_COLOR = "#10B981"  # Success Emerald
FORWARD_OFF_COLOR = "#EF4444" # Warning Red

_STAGE_CODE = {stage: number for number, stage in enumerate(STAGES, start=1)}
_STALL_CODE = 6
_FLUSH_CODE = 7
_COLOR_BY_CODE = [STAGE_COLORS[stage] for stage in STAGES] + [STALL_COLOR, FLUSH_COLOR]


def _discrete_colorscale() -> List[list]:
    """Heatmap colour scale with one flat colour per cell type."""
    count = len(_COLOR_BY_CODE)
    scale: List[list] = []
    for position, color in enumerate(_COLOR_BY_CODE):
        scale.append([position / count, color])
        scale.append([(position + 1) / count, color])
    return scale


def legend_html() -> str:
    """Small HTML legend that explains the colours of the timing diagram."""
    items = [(STAGE_COLORS[stage], stage) for stage in STAGES]
    items += [(STALL_COLOR, "stalled (instruction held, marked *)"), (FLUSH_COLOR, "flushed (wrong-path, ✖)")]
    chips = "".join(
        f'<span class="legend-item"><span class="legend-dot" style="background:{color}"></span>{label}</span>'
        for color, label in items
    )
    return f'<div class="legend">{chips}</div>'


def timing_diagram(
    result: SimulationResult,
    upto_cycle: Optional[int] = None,
    title: str = "",
    highlight_cycle: Optional[int] = None,
    cycle_window: Optional[Tuple[int, int]] = None,
) -> go.Figure:
    """Classic pipeline timing diagram: one row per instruction, one column per cycle."""
    total = result.total_cycles
    figure = go.Figure()
    if total == 0 or not result.instructions:
        figure.add_annotation(text="Nothing to show yet", showarrow=False)
        return figure

    if cycle_window is not None:
        win_start = max(1, cycle_window[0])
        win_end = min(total, cycle_window[1])
        if win_start > win_end:
            win_start, win_end = 1, total
    else:
        win_start = 1
        win_end = total if upto_cycle is None else max(1, min(int(upto_cycle), total))

    cycle_count = win_end - win_start + 1
    # Filter rows that have any activity in this cycle range
    rows = []
    for dyn in result.instructions:
        has_activity = any(win_start <= cyc <= win_end for cyc, _, _ in dyn.history)
        if has_activity or (dyn.fetch_cycle <= win_end and not dyn.history):
            rows.append(dyn)

    if not rows:
        figure.add_annotation(text="No active instructions in this cycle window", showarrow=False)
        return figure

    z: List[List[Optional[int]]] = [[None] * cycle_count for _ in rows]
    text: List[List[str]] = [[""] * cycle_count for _ in rows]
    hover: List[List[str]] = [[""] * cycle_count for _ in rows]

    for row, dyn in enumerate(rows):
        for cycle, stage, state in dyn.history:
            if cycle < win_start or cycle > win_end:
                continue
            column = cycle - win_start
            if state == "flushed":
                z[row][column], text[row][column] = _FLUSH_CODE, "✖"
                hover[row][column] = f"{dyn.label}<br>cycle {cycle}: flushed (wrong-path instruction)"
            elif state == "stall":
                z[row][column], text[row][column] = _STALL_CODE, f"{stage}*"
                hover[row][column] = f"{dyn.label}<br>cycle {cycle}: held in {stage} (stall)"
            else:
                z[row][column], text[row][column] = _STAGE_CODE[stage], stage
                hover[row][column] = f"{dyn.label}<br>cycle {cycle}: {stage}"

    x_values = list(range(win_start, win_end + 1))
    figure.add_trace(go.Heatmap(
        z=z, x=x_values, y=list(range(len(rows))),
        text=text, texttemplate="%{text}", textfont=dict(color="#F1F5F9", size=12),
        hovertext=hover, hoverinfo="text",
        colorscale=_discrete_colorscale(), zmin=0.5, zmax=len(_COLOR_BY_CODE) + 0.5,
        showscale=False, xgap=3, ygap=3, hoverongaps=False,
    ))

    # Add vertical highlight line or box if highlight_cycle is within window
    shapes = []
    if highlight_cycle is not None and win_start <= highlight_cycle <= win_end:
        shapes.append(dict(
            type="rect",
            x0=highlight_cycle - 0.45,
            x1=highlight_cycle + 0.45,
            y0=-0.5,
            y1=len(rows) - 0.5,
            line=dict(color="#22D3EE", width=2.5),
            fillcolor="rgba(34, 211, 238, 0.18)",
        ))

    figure.update_layout(
        title=title or None,
        height=max(220, min(800, 38 * len(rows) + 90)),
        margin=dict(l=10, r=10, t=50 if title else 40, b=10),
        hoverlabel=dict(bgcolor="#111C2E", bordercolor="#22D3EE", font_size=12, font_family="JetBrains Mono"),
        xaxis=dict(
            title="Clock cycle", side="top", dtick=1 if cycle_count <= 40 else max(1, cycle_count // 20),
            tickmode="linear", tick0=win_start, fixedrange=True,
            gridcolor="rgba(39, 54, 75, 0.5)",
            color="#94A3B8",
        ),
        yaxis=dict(tickmode="array", tickvals=list(range(len(rows))), ticktext=[dyn.label for dyn in rows],
                   autorange="reversed", fixedrange=True,
                   gridcolor="rgba(39, 54, 75, 0.5)",
                   color="#94A3B8"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        shapes=shapes,
    )
    return figure


def bar_chart(labels: List[str], values: List[float], colors: List[str], title: str, y_title: str) -> go.Figure:
    figure = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, text=values, textposition="outside"))
    figure.update_layout(
        title=title, yaxis_title=y_title, height=340, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F1F5F9"),
        xaxis=dict(gridcolor="rgba(39, 54, 75, 0.5)", color="#94A3B8"),
        yaxis=dict(gridcolor="rgba(39, 54, 75, 0.5)", color="#94A3B8"),
    )
    return figure


def utilization_chart(
    data: Union[Dict[str, Dict[str, float]], Any],
    colors: Optional[Dict[str, str]] = None,
) -> go.Figure:
    """Grouped bars: share of cycles each stage did useful work, per configuration."""
    from simulator.metrics import PerformanceMetrics

    if isinstance(data, PerformanceMetrics):
        util_dict = {"Active Execution": data.stage_utilization}
        color_dict = {"Active Execution": "#10B981"}
    elif isinstance(data, dict):
        util_dict = data
        color_dict = colors or {"Forwarding ON": "#10B981", "Forwarding OFF": "#EF4444"}
    else:
        util_dict = {}
        color_dict = {}

    figure = go.Figure()
    for name, utilization in util_dict.items():
        bar_color = color_dict.get(name, "#22D3EE")
        figure.add_trace(go.Bar(
            name=name,
            x=STAGES,
            y=[round(100 * utilization.get(stage, 0.0), 1) for stage in STAGES],
            marker_color=bar_color,
            marker_line=dict(color="rgba(255,255,255,0.2)", width=1),
        ))

    figure.update_layout(
        barmode="group",
        title="Hardware Stage Utilization (% useful cycles)",
        yaxis=dict(title="%", range=[0, 105], gridcolor="rgba(39, 54, 75, 0.5)", color="#94A3B8"),
        xaxis=dict(gridcolor="rgba(39, 54, 75, 0.5)", color="#94A3B8"),
        height=340,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=-0.2, font=dict(color="#F1F5F9")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F1F5F9"),
    )
    return figure
