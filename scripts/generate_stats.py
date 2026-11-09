#!/usr/bin/env python3
"""
Zero-dependency GitHub stats and vector graphic generator for RAJ-A58.
Queries GitHub GraphQL API and renders self-hosted, theme-adaptive SVGs:
- stats.svg   : Hero yearly total + weekly aggregate column sparkline
- streak.svg  : Current streak & longest streak with exact date ranges
- langs.svg   : Top languages by bytes & percentage
- year.svg    : 52-week year contribution matrix as an ASCII ramp
- hd-*.svg    : Monospace section header SVGs with hairline rules
"""

import os
import sys
import re
import json
import math
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

GRAPHQL_URL = "https://api.github.com/graphql"

GRAPHQL_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
    repositories(first: 100, privacy: PUBLIC, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes {
        name
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""

def get_theme_css():
    return """
    <style>
      .bg { fill: #0d1117; stroke: #30363d; }
      .title { fill: #58a6ff; font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }
      .hero { fill: #f0f6fc; font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace; font-size: 26px; font-weight: 800; }
      .label { fill: #8b949e; font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace; font-size: 10px; }
      .subtext { fill: #7d8590; font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace; font-size: 11px; }
      .bar-active { fill: #388bfd; }
      .bar-max { fill: #39d353; }
      .bar-zero { fill: #21262d; }
      .ascii-text { font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace; font-size: 11px; fill: #8b949e; }
      .ascii-hi { fill: #39d353; font-weight: bold; }
      .ascii-med { fill: #58a6ff; }
      .ascii-low { fill: #484f58; }
      .rule { stroke: #30363d; stroke-width: 1; }

      @media (prefers-color-scheme: light) {
        .bg { fill: #ffffff; stroke: #d0d7de; }
        .title { fill: #0969da; }
        .hero { fill: #1f2328; }
        .label { fill: #656d76; }
        .subtext { fill: #656d76; }
        .bar-active { fill: #0969da; }
        .bar-max { fill: #1a7f37; }
        .bar-zero { fill: #eaeef2; }
        .ascii-text { fill: #656d76; }
        .ascii-hi { fill: #1a7f37; }
        .ascii-med { fill: #0969da; }
        .ascii-low { fill: #d0d7de; }
        .rule { stroke: #d0d7de; }
      }
    </style>
    """

def query_github_graphql(token: str, login: str, from_dt: datetime, to_dt: datetime):
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "RAJ-A58-stats-generator"
    }
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "login": login,
            "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    }
    req = urllib.request.Request(GRAPHQL_URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        if "errors" in res:
            raise RuntimeError(f"GraphQL Errors: {res['errors']}")
        return res["data"]["user"]

def get_fallback_data(login: str, from_dt: datetime, to_dt: datetime):
    """Fallback data for local development or sandbox runs without GITHUB_TOKEN."""
    print("Using fallback dataset for initial rendering (workflow will update live with GITHUB_TOKEN)...")
    weeks = []
    cur_date = from_dt
    day_counts = [0, 1, 3, 0, 4, 2, 0, 5, 8, 3, 0, 2, 0, 0, 6, 9, 12, 4, 1, 0, 7]
    idx = 0
    while cur_date <= to_dt:
        week = {"contributionDays": []}
        for w in range(7):
            if cur_date > to_dt:
                break
            count = day_counts[idx % len(day_counts)] if (idx % 3 != 0) else 0
            week["contributionDays"].append({
                "date": cur_date.strftime("%Y-%m-%d"),
                "contributionCount": count,
                "weekday": w
            })
            cur_date += timedelta(days=1)
            idx += 1
        weeks.append(week)

    return {
        "contributionsCollection": {
            "totalCommitContributions": 239,
            "totalIssueContributions": 4,
            "totalPullRequestContributions": 6,
            "totalPullRequestReviewContributions": 1,
            "restrictedContributionsCount": 35,
            "contributionCalendar": {
                "totalContributions": 295,
                "weeks": weeks
            }
        },
        "repositories": {
            "nodes": [
                {
                    "name": "FX-Arbitrage-Detector",
                    "languages": {"edges": [
                        {"size": 340000, "node": {"name": "C++", "color": "#f34b7d"}},
                        {"size": 15000, "node": {"name": "CMake", "color": "#ccc"}}
                    ]}
                },
                {
                    "name": "cpp-concurrency-journey",
                    "languages": {"edges": [
                        {"size": 420000, "node": {"name": "C++", "color": "#f34b7d"}}
                    ]}
                },
                {
                    "name": "Blinkit-concurrency-poc",
                    "languages": {"edges": [
                        {"size": 190000, "node": {"name": "Python", "color": "#3572A5"}},
                        {"size": 45000, "node": {"name": "SQL", "color": "#e38c00"}}
                    ]}
                },
                {
                    "name": "route_optmisation",
                    "languages": {"edges": [
                        {"size": 280000, "node": {"name": "Python", "color": "#3572A5"}}
                    ]}
                },
                {
                    "name": "BAH26_Exoplanet_Detection",
                    "languages": {"edges": [
                        {"size": 510000, "node": {"name": "Python", "color": "#3572A5"}}
                    ]}
                }
            ]
        }
    }

def calculate_metrics(user_data):
    cal = user_data["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total_contribs = cal["totalContributions"]
    total_commits = user_data["contributionsCollection"].get("totalCommitContributions", 0)
    total_issues = user_data["contributionsCollection"].get("totalIssueContributions", 0)
    total_prs = user_data["contributionsCollection"].get("totalPullRequestContributions", 0)
    total_reviews = user_data["contributionsCollection"].get("totalPullRequestReviewContributions", 0)

    # Flatten all days
    all_days = []
    weekly_sums = []
    for w in weeks:
        w_sum = sum(d["contributionCount"] for d in w["contributionDays"])
        weekly_sums.append(w_sum)
        for d in w["contributionDays"]:
            all_days.append(d)

    # Streaks calculation
    cur_streak = 0
    cur_streak_start = None
    cur_streak_end = None
    
    max_streak = 0
    max_streak_start = None
    max_streak_end = None

    temp_streak = 0
    temp_start = None
    temp_end = None

    active_days = 0

    for d in all_days:
        c = d["contributionCount"]
        dt = d["date"]
        if c > 0:
            active_days += 1
            if temp_streak == 0:
                temp_start = dt
            temp_streak += 1
            temp_end = dt
            if temp_streak > max_streak:
                max_streak = temp_streak
                max_streak_start = temp_start
                max_streak_end = temp_end
        else:
            temp_streak = 0
            temp_start = None

    # Current streak ending at the end of all_days
    # If today is 0, check yesterday
    idx = len(all_days) - 1
    if idx >= 0 and all_days[idx]["contributionCount"] == 0 and idx > 0 and all_days[idx - 1]["contributionCount"] > 0:
        idx -= 1

    while idx >= 0 and all_days[idx]["contributionCount"] > 0:
        if cur_streak == 0:
            cur_streak_end = all_days[idx]["date"]
        cur_streak += 1
        cur_streak_start = all_days[idx]["date"]
        idx -= 1

    # Languages breakdown
    lang_bytes = {}
    lang_colors = {}
    total_bytes = 0

    for repo in user_data["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            size = edge["size"]
            color = edge["node"].get("color") or "#8b949e"
            lang_bytes[name] = lang_bytes.get(name, 0) + size
            lang_colors[name] = color
            total_bytes += size

    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_contributions": total_contribs,
        "total_commits": total_commits,
        "total_issues": total_issues,
        "total_prs": total_prs,
        "total_reviews": total_reviews,
        "weeks": weeks,
        "weekly_sums": weekly_sums,
        "all_days": all_days,
        "active_days": active_days,
        "cur_streak": cur_streak,
        "cur_streak_start": cur_streak_start,
        "cur_streak_end": cur_streak_end,
        "max_streak": max_streak,
        "max_streak_start": max_streak_start,
        "max_streak_end": max_streak_end,
        "languages": sorted_langs,
        "lang_colors": lang_colors,
        "total_bytes": total_bytes
    }

def update_ascii_svg(svg_path, metrics):
    if not os.path.exists(svg_path):
        return
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()

    contribs = metrics["total_contributions"]
    commits = metrics.get("total_commits", 0)
    prs = metrics.get("total_prs", 0)
    issues = metrics.get("total_issues", 0)
    reviews = metrics.get("total_reviews", 0)

    # Replace Contributions
    content = re.sub(
        r'(\. Contributions:\s*</tspan><tspan[^>]*>\.+?</tspan><tspan[^>]*>\s*)\d+',
        rf'\g<1>{contribs}',
        content
    )
    # Replace Commits (if commits > 0)
    if commits > 0:
        content = re.sub(
            r'(\. Commits:\s*</tspan><tspan[^>]*>\.+?</tspan><tspan[^>]*>\s*)\d+',
            rf'\g<1>{commits}',
            content
        )
    if prs > 0:
        content = re.sub(
            r'(\. PRs:\s*</tspan><tspan[^>]*>\.+?</tspan><tspan[^>]*>\s*)\d+',
            rf'\g<1>{prs}',
            content
        )
    content = re.sub(
        r'(\. Issues:\s*</tspan><tspan[^>]*>\.+?</tspan><tspan[^>]*>\s*)\d+',
        rf'\g<1>{issues}',
        content
    )
    content = re.sub(
        r'(\. Reviews:\s*</tspan><tspan[^>]*>\.+?</tspan><tspan[^>]*>\s*)\d+',
        rf'\g<1>{reviews}',
        content
    )

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(content)

def format_date_range(start_str, end_str):
    if not start_str or not end_str:
        return "—"
    try:
        s = datetime.strptime(start_str, "%Y-%m-%d").strftime("%b %d")
        e = datetime.strptime(end_str, "%Y-%m-%d").strftime("%b %d, %Y")
        return f"{s} — {e}"
    except Exception:
        return f"{start_str} - {end_str}"

def render_stats_svg(metrics, from_dt, to_dt):
    width, height = 460, 170
    weekly = metrics["weekly_sums"]
    # Take last 52 weeks
    if len(weekly) > 52:
        weekly = weekly[-52:]
    max_w = max(weekly) if weekly and max(weekly) > 0 else 1

    chart_x = 24
    chart_y = 100
    chart_h = 44
    col_w = 5.2
    gap = 2.4

    bars_svg = []
    for i, count in enumerate(weekly):
        x = chart_x + i * (col_w + gap)
        if count == 0:
            bars_svg.append(f'<rect x="{x:.1f}" y="{chart_y + chart_h - 1}" width="{col_w}" height="1.5" rx="0.75" class="bar-zero"/>')
        else:
            h = max(3.0, (count / max_w) * chart_h)
            y = chart_y + chart_h - h
            cls = "bar-max" if count == max_w else "bar-active"
            bars_svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{col_w}" height="{h:.1f}" rx="1" class="{cls}"/>')

    date_label = f"{from_dt.strftime('%b %Y')} — {to_dt.strftime('%b %Y')}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Yearly contribution stats">
  {get_theme_css()}
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" class="bg"/>
  <text x="24" y="32" class="title">// TELEMETRY · YEARLY CONTRIBUTIONS</text>
  <text x="24" y="68" class="hero">{metrics['total_contributions']:,}</text>
  <text x="24" y="86" class="subtext">Recorded contributions across 52 weeks ({date_label})</text>
  <g id="weekly-sparkline">
    {''.join(bars_svg)}
  </g>
  <text x="{chart_x}" y="{chart_y + chart_h + 16}" class="label">{from_dt.strftime('%b')}</text>
  <text x="{width - 50}" y="{chart_y + chart_h + 16}" class="label">{to_dt.strftime('%b')}</text>
</svg>"""

def render_streak_svg(metrics):
    width, height = 460, 170
    cur_s = metrics["cur_streak"]
    max_s = metrics["max_streak"]
    cur_range = format_date_range(metrics["cur_streak_start"], metrics["cur_streak_end"])
    max_range = format_date_range(metrics["max_streak_start"], metrics["max_streak_end"])

    active_days = metrics["active_days"]
    pct = round((active_days / 365) * 100, 1)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Contribution streak stats">
  {get_theme_css()}
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" class="bg"/>
  <text x="24" y="32" class="title">// DISCIPLINE · CONTRIBUTION STREAKS</text>

  <!-- Current Streak -->
  <g transform="translate(24, 48)">
    <text x="0" y="14" class="label">CURRENT STREAK</text>
    <text x="0" y="42" class="hero">{cur_s} <tspan font-size="14" font-weight="500">days</tspan></text>
    <text x="0" y="58" class="subtext">{cur_range}</text>
  </g>

  <!-- Longest Streak -->
  <g transform="translate(230, 48)">
    <text x="0" y="14" class="label">LONGEST STREAK</text>
    <text x="0" y="42" class="hero">{max_s} <tspan font-size="14" font-weight="500">days</tspan></text>
    <text x="0" y="58" class="subtext">{max_range}</text>
  </g>

  <line x1="24" y1="126" x2="{width - 24}" y2="126" class="rule"/>
  <text x="24" y="148" class="subtext">Consistency rate: <tspan class="title">{active_days} active days</tspan> ({pct}% of the year)</text>
</svg>"""

def render_langs_svg(metrics):
    width, height = 460, 170
    langs = metrics["languages"][:5]
    total_b = metrics["total_bytes"]
    colors = metrics["lang_colors"]

    bar_x = 24
    bar_y = 60
    bar_w = 412
    bar_h = 10

    # Stacked progress bar
    progress_rects = []
    cur_x = bar_x
    for name, b in langs:
        pct = (b / total_b) if total_b > 0 else 0
        w = max(2.0, pct * bar_w)
        c = colors.get(name, "#8b949e")
        progress_rects.append(f'<rect x="{cur_x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" fill="{c}"/>')
        cur_x += w

    # Legend items in 2 rows
    legend_svg = []
    col1 = langs[:3]
    col2 = langs[3:]

    for i, (name, b) in enumerate(col1):
        pct = (b / total_b * 100) if total_b > 0 else 0
        y = 96 + (i * 20)
        c = colors.get(name, "#8b949e")
        legend_svg.append(f'<circle cx="28" cy="{y - 4}" r="4" fill="{c}"/>')
        legend_svg.append(f'<text x="40" y="{y}" class="ascii-text">{name} <tspan class="label">({pct:.1f}%)</tspan></text>')

    for i, (name, b) in enumerate(col2):
        pct = (b / total_b * 100) if total_b > 0 else 0
        y = 96 + (i * 20)
        c = colors.get(name, "#8b949e")
        legend_svg.append(f'<circle cx="230" cy="{y - 4}" r="4" fill="{c}"/>')
        legend_svg.append(f'<text x="242" y="{y}" class="ascii-text">{name} <tspan class="label">({pct:.1f}%)</tspan></text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Top programming languages">
  {get_theme_css()}
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" class="bg"/>
  <text x="24" y="32" class="title">// WORKSPACE · REPOSITORY COMPOSITION</text>

  <g id="progress-bar" clip-path="url(#bar-clip)">
    <clipPath id="bar-clip">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5"/>
    </clipPath>
    {''.join(progress_rects)}
  </g>

  <g id="legend">
    {''.join(legend_svg)}
  </g>
</svg>"""

def render_year_svg(metrics, from_dt, to_dt):
    width, height = 930, 175
    weeks = metrics["weeks"]
    if len(weeks) > 53:
        weeks = weeks[-53:]

    # ASCII density ramp
    # 0 -> '·', 1-2 -> ':', 3-5 -> '+', 6-9 -> '*', 10+ -> '#'
    def get_char_and_class(cnt):
        if cnt == 0:
            return '·', 'ascii-low'
        elif cnt <= 2:
            return ':', 'ascii-low'
        elif cnt <= 5:
            return '+', 'ascii-med'
        elif cnt <= 9:
            return '*', 'ascii-med'
        else:
            return '#', 'ascii-hi'

    month_labels = []
    # Build columns
    start_x = 44
    start_y = 62
    cell_w = 16.5
    cell_h = 13.5

    # Month labels on top
    last_month = None
    for col_idx, w in enumerate(weeks):
        if w["contributionDays"]:
            m_str = datetime.strptime(w["contributionDays"][0]["date"], "%Y-%m-%d").strftime("%b")
            if m_str != last_month and col_idx < len(weeks) - 2:
                month_labels.append(f'<text x="{start_x + col_idx * cell_w:.1f}" y="46" class="label">{m_str}</text>')
                last_month = m_str

    cells = []
    for col_idx, w in enumerate(weeks):
        x = start_x + col_idx * cell_w
        for day in w["contributionDays"]:
            row_idx = day["weekday"]
            y = start_y + row_idx * cell_h
            ch, cls = get_char_and_class(day["contributionCount"])
            cells.append(f'<text x="{x:.1f}" y="{y:.1f}" class="ascii-text {cls}">{ch}</text>')

    day_labels = [
        f'<text x="14" y="{start_y + 1 * cell_h:.1f}" class="label">Mon</text>',
        f'<text x="14" y="{start_y + 3 * cell_h:.1f}" class="label">Wed</text>',
        f'<text x="14" y="{start_y + 5 * cell_h:.1f}" class="label">Fri</text>',
    ]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Year in ASCII">
  {get_theme_css()}
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" class="bg"/>
  <text x="24" y="28" class="title">// 365-DAY CHRONOLOGY (ASCII RAMP: · : + * #)</text>
  <text x="{width - 240}" y="28" class="label">Intensity: <tspan class="ascii-low">·</tspan> <tspan class="ascii-low">:</tspan> <tspan class="ascii-med">+</tspan> <tspan class="ascii-med">*</tspan> <tspan class="ascii-hi">#</tspan></text>

  <g id="months">
    {''.join(month_labels)}
  </g>

  <g id="day-labels">
    {''.join(day_labels)}
  </g>

  <g id="ascii-cells">
    {''.join(cells)}
  </g>
</svg>"""

def render_heading_svg(label: str, width=900, height=26):
    text_w = len(label) * 8.5 + 20
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  {get_theme_css()}
  <text x="0" y="17" class="title">{label.upper()}</text>
  <line x1="{text_w:.1f}" y1="14" x2="{width}" y2="14" class="rule"/>
</svg>"""

def main():
    login = os.environ.get("GH_LOGIN", "RAJ-A58")
    token = os.environ.get("GITHUB_TOKEN")

    now = datetime.now(timezone.utc)
    to_dt = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc)
    from_dt = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc) - timedelta(days=364)

    user_data = None
    if token:
        try:
            print(f"Querying GitHub GraphQL API for user '{login}'...")
            user_data = query_github_graphql(token, login, from_dt, to_dt)
            print("Successfully fetched live GitHub telemetry data.")
        except Exception as e:
            print(f"Warning: Failed to fetch from GitHub API: {e}", file=sys.stderr)

    if not user_data:
        user_data = get_fallback_data(login, from_dt, to_dt)

    metrics = calculate_metrics(user_data)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Generate stats.svg
    stats_svg = render_stats_svg(metrics, from_dt, to_dt)
    with open(os.path.join(root, "stats.svg"), "w", encoding="utf-8") as f:
        f.write(stats_svg)
    print("Generated stats.svg")

    # Generate streak.svg
    streak_svg = render_streak_svg(metrics)
    with open(os.path.join(root, "streak.svg"), "w", encoding="utf-8") as f:
        f.write(streak_svg)
    print("Generated streak.svg")

    # Generate langs.svg
    langs_svg = render_langs_svg(metrics)
    with open(os.path.join(root, "langs.svg"), "w", encoding="utf-8") as f:
        f.write(langs_svg)
    print("Generated langs.svg")

    # Generate year.svg
    year_svg = render_year_svg(metrics, from_dt, to_dt)
    with open(os.path.join(root, "year.svg"), "w", encoding="utf-8") as f:
        f.write(year_svg)
    print("Generated year.svg")

    # Generate section heading SVGs
    headings = {
        "hd-about.svg": "// 01. about me",
        "hd-stack.svg": "// 02. tech stack & systems",
        "hd-projects.svg": "// 03. highlighted projects",
        "hd-telemetry.svg": "// 04. live telemetry & activity"
    }
    for filename, label in headings.items():
        hd_svg = render_heading_svg(label)
        with open(os.path.join(root, filename), "w", encoding="utf-8") as f:
            f.write(hd_svg)
        print(f"Generated {filename}")

    # Update ASCII cards with live stats
    update_ascii_svg(os.path.join(root, "dark_mode.svg"), metrics)
    update_ascii_svg(os.path.join(root, "light_mode.svg"), metrics)
    print("Updated dark_mode.svg and light_mode.svg with live stats")

if __name__ == "__main__":
    main()
