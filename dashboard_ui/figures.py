import plotly.express as px
import plotly.graph_objects as go

# Public Bank Enterprise Color Palette
PB_RED = "#E2001A"
PB_DARK_RED = "#990012"
PB_YELLOW = "#FFC220"
PB_DARK_GREY = "#374151"
PB_LIGHT_GREY = "#9CA3AF"

PB_COLOR_SEQUENCE = [PB_RED, PB_YELLOW, PB_DARK_GREY, PB_DARK_RED, PB_LIGHT_GREY, "#D1D5DB", "#1F2937"]

def empty_figure(title: str):
    fig = go.Figure()
    fig.update_layout(
        title=None,
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": "No data available in current filter scope",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 15, "color": "#9CA3AF", "family": "-apple-system, sans-serif"},
            }
        ],
        margin=dict(l=30, r=20, t=15, b=30),
    )
    return fig


def apply_base_layout(fig, x_title=None, y_title=None, margin=None, show_legend=False):
    fig.update_layout(
        title=None,
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", "color": "#1f2937"},
        margin=margin or dict(l=50, r=20, t=15, b=40),
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend_title_text="",
        showlegend=show_legend,
        hovermode="closest",
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F3F4F6",
        zeroline=False,
        linecolor="#E5E7EB",
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#F3F4F6",
        zeroline=False,
        linecolor="#E5E7EB",
        automargin=True,
    )
    return fig


def build_trend_chart(df, trend_mode="total"):
    if df.is_empty():
        return empty_figure("Monthly Trend")

    pdf = df.to_pandas().copy()
    pdf = pdf.sort_values(["period_order"] + (["NAME"] if "NAME" in pdf.columns else []))

    ordered_periods = pdf["period_label"].drop_duplicates().tolist()
    tick_step = max(1, len(ordered_periods) // 8)
    tickvals = ordered_periods[::tick_step]

    if trend_mode == "compare" and "NAME" in pdf.columns:
        fig = px.line(
            pdf,
            x="period_label",
            y="Count",
            color="NAME",
            markers=True,
            category_orders={"period_label": ordered_periods},
            color_discrete_sequence=PB_COLOR_SEQUENCE
        )

        fig.update_traces(
            line=dict(width=2.5),
            marker=dict(size=6),
            hovertemplate="<b>%{fullData.name}</b><br>Period: %{x}<br>Total: %{y:,}<extra></extra>",
        )

        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(size=11),
            )
        )

        apply_base_layout(
            fig,
            x_title="Monitoring Period",
            y_title="Alert Volume",
            margin=dict(l=55, r=20, t=30, b=55),
            show_legend=True,
        )
    else:
        fig = px.line(
            pdf,
            x="period_label",
            y="Count",
            markers=True,
            category_orders={"period_label": ordered_periods},
        )

        fig.update_traces(
            line=dict(width=3, color=PB_RED),
            marker=dict(size=8, color=PB_YELLOW, line=dict(width=1, color=PB_DARK_RED)),
            hovertemplate="<b>%{x}</b><br>Total: %{y:,}<extra></extra>",
        )

        apply_base_layout(
            fig,
            x_title="Monitoring Period",
            y_title="Total Alert Volume",
            margin=dict(l=55, r=20, t=10, b=55),
            show_legend=False,
        )

    fig.update_xaxes(
        tickmode="array",
        tickvals=tickvals,
        ticktext=tickvals,
        tickangle=-20,
    )

    return fig


def build_status_chart(df):
    if df.is_empty():
        return empty_figure("Status Distribution")

    pdf = df.to_pandas().copy()
    pdf = pdf.sort_values("Count", ascending=False)

    fig = px.bar(
        pdf,
        x="NAME",
        y="Count",
    )
    fig.update_traces(
        marker_color=PB_RED,
        hovertemplate="<b>%{x}</b><br>Total: %{y:,}<extra></extra>",
    )

    apply_base_layout(
        fig,
        x_title="Alert Status",
        y_title="Volume",
        margin=dict(l=60, r=20, t=10, b=110),
        show_legend=False,
    )

    fig.update_xaxes(
        tickangle=-45,
        automargin=True,
    )
    fig.update_yaxes(showgrid=True)

    return fig


def build_yearly_chart(df):
    if df.is_empty():
        return empty_figure("Yearly Breakdown")

    pdf = df.to_pandas().copy()
    pdf["year_creation"] = pdf["year_creation"].astype(str)
    pdf = pdf.sort_values(["year_creation", "NAME"])

    total_per_year = (
        pdf.groupby("year_creation", as_index=False)["Count"]
        .sum()
        .rename(columns={"Count": "YearTotal"})
        .sort_values("year_creation")
    )

    max_total = total_per_year["YearTotal"].max() if not total_per_year.empty else 0

    fig = px.bar(
        pdf,
        y="year_creation",
        x="Count",
        color="NAME",
        orientation="h",
        color_discrete_sequence=PB_COLOR_SEQUENCE
    )

    fig.update_layout(
        barmode="stack",
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", "color": "#1f2937"},
        margin=dict(l=55, r=35, t=10, b=105),
        xaxis_title="Accumulated Volume",
        yaxis_title="Financial Year",
        yaxis=dict(categoryorder="category descending"),
        hovermode="closest",
        legend_title_text="",
        legend=dict(
            title=None,
            orientation="h",
            yanchor="top",
            y=-0.24,
            xanchor="left",
            x=0,
            font=dict(size=11),
            itemwidth=65,
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F3F4F6",
        zeroline=False,
        automargin=True,
        # Extended range to give generous space for the text label on the right
        range=[0, max_total * 1.25 if max_total else 1],
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        automargin=True,
    )

    # Placing the text strictly outside the bar using middle right
    fig.add_scatter(
        y=total_per_year["year_creation"],
        x=total_per_year["YearTotal"],
        text=[f"  {int(v):,}" for v in total_per_year["YearTotal"]], # Extra spacing via string formatting
        mode="text",
        textposition="middle right",
        showlegend=False,
        hoverinfo="skip",
        textfont=dict(color="#111827", size=14, weight="bold") # High visibility dark text
    )

    fig.update_traces(
        hovertemplate="Year: %{y}<br>Status: %{fullData.name}<br>Total: %{x:,}<extra></extra>"
    )

    return fig