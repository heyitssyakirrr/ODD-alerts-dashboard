from dash import html


def build_trend_insights(df, trend_mode="total"):
    if df.is_empty():
        return [html.Li("No trend insight available.")]

    pdf = df.to_pandas().copy()

    if trend_mode == "compare" and "NAME" in pdf.columns:
        summary = (
            pdf.groupby("NAME", as_index=False)["Count"]
            .sum()
            .sort_values("Count", ascending=False)
        )

        top_rows = summary.head(3).to_dict("records")
        items = []

        for idx, row in enumerate(top_rows, start=1):
            items.append(
                html.Li(
                    f"Top {idx} trend contributor: {row['NAME']} accounts for {int(row['Count']):,} alerts in the selected period."
                )
            )

        if len(summary) > 1:
            leader = summary.iloc[0]
            runner_up = summary.iloc[1]
            gap = int(leader["Count"] - runner_up["Count"])
            items.append(
                html.Li(
                    f"Comparison signal: {leader['NAME']} leads the next selected status by {gap:,} alerts."
                )
            )

        return items

    monthly = (
        pdf.groupby(["period_label", "period_order"], as_index=False)["Count"]
        .sum()
        .sort_values("period_order")
    )

    peak_row = monthly.sort_values("Count", ascending=False).iloc[0]
    items = [
        html.Li(
            f"Peak workload period: {peak_row['period_label']} recorded the highest total with {int(peak_row['Count']):,} alerts."
        )
    ]

    if len(monthly) > 1:
        first = monthly.iloc[0]
        last = monthly.iloc[-1]
        diff = int(last["Count"] - first["Count"])
        direction = "increased" if diff >= 0 else "decreased"
        items.append(
            html.Li(
                f"Trend direction: selected alert volume {direction} by {abs(diff):,} from {first['period_label']} to {last['period_label']}."
            )
        )

        avg_count = monthly["Count"].mean()
        items.append(
            html.Li(
                f"Average monthly workload across the selected period is {avg_count:,.0f} alerts."
            )
        )

    return items


def build_status_insights(df):
    if df.is_empty():
        return [html.Li("No status insight available.")]

    pdf = df.to_pandas().copy()
    total = pdf["Count"].sum()
    top_rows = pdf.head(3).to_dict("records")

    items = []

    for idx, row in enumerate(top_rows, start=1):
        pct = (row["Count"] / total * 100) if total else 0
        items.append(
            html.Li(
                f"Top {idx} status: {row['NAME']} contributes {int(row['Count']):,} alerts ({pct:.1f}% of selected workload)."
            )
        )

    if not pdf.empty:
        closed_total = pdf[pdf["NAME"].astype(str).str.startswith("Closed")]["Count"].sum()
        open_total = pdf[~pdf["NAME"].astype(str).str.startswith("Closed")]["Count"].sum()

        if open_total > closed_total:
            items.append(
                html.Li(
                    "Operational signal: open-stage alerts exceed closed-stage alerts, which may indicate backlog pressure."
                )
            )
        else:
            items.append(
                html.Li(
                    "Operational signal: closed-stage alerts remain higher than open-stage alerts, suggesting stronger completion throughput."
                )
            )

    return items


def build_yearly_insights(df):
    if df.is_empty():
        return [html.Li("No yearly insight available.")]

    pdf = df.to_pandas().copy()
    totals = (
        pdf.groupby("year_creation", as_index=False)["Count"]
        .sum()
        .sort_values("year_creation")
    )

    top_year = totals.sort_values("Count", ascending=False).iloc[0]

    items = [
        html.Li(
            f"Highest year: {int(top_year['year_creation'])} recorded the largest total with {int(top_year['Count']):,} alerts."
        )
    ]

    if len(totals) > 1:
        first = totals.iloc[0]
        last = totals.iloc[-1]
        change = int(last["Count"] - first["Count"])
        direction = "increased" if change >= 0 else "decreased"

        items.append(
            html.Li(
                f"Long-term direction: yearly workload {direction} by {abs(change):,} from {int(first['year_creation'])} to {int(last['year_creation'])}."
            )
        )

        totals["prev"] = totals["Count"].shift(1)
        growth_df = totals.dropna().copy()
        growth_df["change"] = growth_df["Count"] - growth_df["prev"]

        if not growth_df.empty:
            strongest_growth = growth_df.sort_values("change", ascending=False).iloc[0]
            items.append(
                html.Li(
                    f"Biggest year-on-year jump: {int(strongest_growth['year_creation'])} rose by {int(strongest_growth['change']):,} versus the previous year."
                )
            )

    return items