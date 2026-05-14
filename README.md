# JMeter JSON to Excel Report Generator

This Streamlit app converts JMeter static `statistics.json` files into Excel reports.


## Final Refinements Included

- `Insights` includes **Top 10 Error APIs** table and chart.
- `APIs` highlights only response-time cells that breach SLA, not the full row.
- `Track_Comparison` excludes any track containing `Select customer`.

## Output Sheets

- `Insights` - KPI summary and charts
- `Track_Comparison` - side-by-side track comparison for all uploaded JSON files
- `Transactions` - only transaction rows starting with `T01`, `T02`, etc.
- `Errors` - rows where `errorCount > 0`
- `APIs` - non-transaction API rows only; original `transaction` column removed
- `Comparison` - raw API comparison when two or more JSON files are uploaded

## Track_Comparison Logic

Track = first part of transaction before `/`.

For each track, the sheet shows three metric rows:
- `Avg` uses `meanResTime`
- `Min` uses `minResTime`
- `Max` uses `maxResTime`

Percentages use **API count**, not sample count.

### Buckets

For tracks where Feature starts with `AskAI`:
- `0-10s`
- `10-20s`
- `20-30s`
- `>30s`

For all other tracks:
- `0-2s`
- `3-4s`
- `4-6s`
- `>6s`

Each uploaded JSON file appears as a side-by-side block with:
- Bucket 1 %
- Bucket 2 %
- Bucket 3 %
- Bucket 4 %
- Max Seconds

## SLA Logic

- AskAI Feature: SLA `< 10 sec`
- Assets, Assessments, Home, Settings and Support Features: SLA `< 2 sec`

PASS/FAIL in the `APIs` sheet is based on Avg Response Time in seconds.

## Run Locally

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Replace your GitHub repo files with:
   - `app.py`
   - `main.py`
   - `requirements.txt`
   - `README.md`

2. Commit and push to GitHub.

3. In Streamlit Cloud, redeploy your app.

## Team Usage

1. Open the Streamlit URL.
2. Upload one JSON for normal report.
3. Upload two or more JSONs for side-by-side comparison.
4. Open the Executive Dashboard for leadership-ready KPIs, filters, trends and drilldowns.
5. Download Excel when detailed evidence is required.

## Dashboard Comparison Workflow

Use this flow when sharing results with team members or higher management:

1. Upload the latest JMeter `statistics.json` file(s).
2. Keep **Save uploaded reports for team visibility** enabled so the latest 5 uploads remain available on the landing page.
3. Click **Generate Results**.
4. Share the Executive Dashboard view for interactive review.
5. For two or more uploaded files, the Overview summary shows each result separately with Diff columns against the first selected result, instead of cumulating all reports.
6. Use Track Comparison to review each Region/Result as rows, with Avg, Min and Max rows for every Total or Track.
7. Download **Excel Report** when detailed evidence is required.


## Latest v13 Updates

- Streamlit UI wording updated for SLA rules and track buckets.
- `Track_Comparison` now includes embedded charts for top slow tracks.
- API percentage calculation remains API-count based.


## v14 Final Polish

- Removed M, N, O and P SLA-helper columns from the `APIs` sheet.
- `APIs` sheet highlights only breaching response-time cells, not full rows.
- `Track_Comparison` removes `Total` and any track containing `Select customer`.
- `Track_Comparison` charts also exclude `Total` and `Select customer`.
- Insights chart sizing/placement improved to reduce title/graph collisions.


## v15 Comparison-Focused Update

When two or more JSON files are uploaded, the generated workbook contains only:
- `Insights`
- `Track_Comparison`
- `APIs_Comparison`

`APIs_Comparison` shows Feature, Scenario and Endpoint separately for every uploaded report, plus side-by-side API metrics and baseline-vs-latest diff columns.


## v16 Final Fixes

- APIs sheet removes M, N, O, P SLA-helper columns.
- APIs sheet highlights only response-time cells that breach SLA.
- Insights charts use external cell titles to avoid title/graph collision.
- Top 10 Error APIs excludes `Total//` and any `Select customer` rows.
- Track_Comparison and its charts exclude `Total` and any track containing `Select customer`.


## v17 Corrections

- `APIs` sheet defensively removes SLA helper columns M, N, O and P.
- `Track_Comparison` Max Seconds is now metric-specific:
  - Avg row uses max Avg response time for that track.
  - Min row uses max Min response time for that track.
  - Max row uses max Max response time for that track.
- `Total` and `Select customer` remain excluded from Track_Comparison and its charts.


## v18 Chart and UI Polish

- Removed red highlighting from `Max Seconds` columns in `Track_Comparison`.
- Added value labels to Insights and Track_Comparison charts.
- Removed x/y axis titles from charts to avoid label collisions.
- Added a custom gradient background and styled upload/download controls in Streamlit UI.


## v19 Axis Titles and Samples

- Added `Total Samples` count in Insights.
- API SLA pie chart displays values and percentages.
- Restored x/y axis titles with larger chart sizes and spacing to avoid collisions.
- Track_Comparison charts include values and x/y axis titles with extra spacing.


## v20 Visible Chart Values

- Added Total Samples in Insights.
- SLA chart source table now includes PASS/FAIL count and percent.
- API SLA pie chart displays values and percentages.
- Restored X/Y axis titles with larger chart dimensions and more spacing.
- Track_Comparison charts include visible values and axis titles with more spacing.


## v21 Chart Titles and Visible Values

- API SLA pie chart now has an internal title again.
- Added visible PASS/FAIL/TOTAL count and percentage summary next to the SLA pie chart.
- Top 10 Slow APIs, Top 10 Error APIs, and Track_Comparison charts have internal titles.
- Chart sizes and positions increased to reduce title/plot collision.


## v22 Next-Level Dashboard

- Rebuilt Insights as an executive dashboard with KPI cards, health score, SLA breakdown, ranked slow APIs, ranked error APIs, and top slow tracks.
- Charts now use short rank labels to avoid long API-name collisions.
- Full API/track names are shown in readable side tables next to each chart.
- Track_Comparison charts now use rank-based labels and side tables for readability.


## v23 Clean Track Tables

- Removed Track charts from `Insights`.
- Removed Track charts from `Track_Comparison`.
- Added clean Track-wise summary tables instead.
- Removed cluttered bar chart value labels; values are shown clearly in the tables.
- Slow/Error API charts use Rank numbers while full API details are available in tables.


## v24 Clean Dashboard

- Removed the `Track-wise Slow Summary` table from `Insights`.
- Removed the extra `Track-wise Slow Summary` table from `Track_Comparison`.
- Removed the SLA pie chart because it was visually cluttered.
- SLA PASS/FAIL/TOTAL values remain as a clean table.


## v25 Clean Pie Chart

- Re-added `API SLA Pass vs Fail` pie chart.
- Removed overlapping pie labels from the chart.
- PASS/FAIL/TOTAL values are shown clearly in the SLA Breakdown table next to the chart.
- Track-wise summary remains removed from Insights and Track_Comparison.


## v26 Code and UI Fix

- Clean SLA pie chart code is included in `main.py`.
- Pie chart does not use overlapping internal labels.
- PASS/FAIL/TOTAL values remain visible in the SLA Breakdown table.
- Streamlit UI title changed to `CiscoIQ-SaaS-Support-Services Performance Dashboard`.
- Streamlit title font size reduced.


## v27 Title and Report Context

- Excel Insights title changed to `CiscoIQ-SaaS-Support-Services Performance Dashboard`.
- Streamlit title changed to `CiscoIQ-SaaS-Support-Services Performance Dashboard`.
- Streamlit title font size reduced.
- Insights now includes Report Context parsed from the uploaded filename:
  - Concurrent Users
  - Devices Count
  - Date
  - Duration
  - Region


## v28 Dashboard Final Updates

- Removed Report File from the Insights page.
- Added Health Score explanation in Insights.
- Moved pie chart title outside the chart to prevent overlap.
- Streamlit UI title is centered and smaller.
- Added Generate Report button after upload.
- APIs sheet column names changed:
  - `Feature` -> `Tracks`
  - `Scenario` -> `Transactions`


## v29 Next-Level Comparison Dashboard

- Track_Comparison now separates AskAI tracks and non-AskAI tracks into clear sections.
- AskAI section columns:
  - 0-10sec %
  - 10-20sec %
  - 20-30sec %
  - >30sec %
  - Max Seconds
- Other tracks section columns:
  - 0-2sec %
  - 3-4sec %
  - 4-6sec %
  - >6sec %
  - Max Seconds
- Transactions and Errors sheets now use capitalized column names:
  - Transaction
  - SampleCount
  - ErrorCount
  - ErrorPct


## v30 Verified Track Comparison

This package has been verified from the actual project code.

### Track_Comparison
The workbook now has separate sections:
- AskAI Tracks
  - 0-10sec %
  - 10-20sec %
  - 20-30sec %
  - >30sec %
  - Max Seconds

- Assets / Assessments / Home / Settings / Support Tracks
  - 0-2sec %
  - 3-4sec %
  - 4-6sec %
  - >6sec %
  - Max Seconds

### Transactions / Errors headers
- Transaction
- SampleCount
- ErrorCount
- ErrorPct


## v31 Clean Track Headers

- Removed duplicate `Track / Metric / Report Name` row in `Track_Comparison`.
- Section title now includes report name:
  - `AskAI Tracks - <report name>`
  - `Assets / Assessments / Home / Settings / Support Tracks - <report name>`
- Kept the bucket header row directly below the section title.
- Removed Streamlit version caption from UI.


## v33 Clean Headers and UI Fonts

- Removed duplicate Track/Metric/report row defensively in `write_track_comparison_sheet`.
- `Track_Comparison` now has only:
  - Section title row
  - Bucket header row
  - Data rows
- Reduced Streamlit `SLA Rules` and `Track Comparison Buckets` font sizes.
- Removed version caption from Streamlit UI.


## v34 Force Clean Track Headers

- Hard removed duplicate `Track | Metric | report name` rows in code.
- Added a defensive post-write cleanup in `write_track_comparison_sheet`.
- UI text changed from `Track Comparison Buckets` to `Track Comparison Metrics`.
- SLA Rules / Track Comparison Metrics font size reduced.


## v35 Spacing, Metadata, UI Font Restore

- Added larger vertical gap between `Top 10 Slow APIs` and `Top 10 Error APIs` charts.
- Restored normal Streamlit font size for SLA Rules and Track Comparison Metrics bullet text.
- UI text uses `Track Comparison Metrics`.
- Filename parser now extracts:
  - Month-Day-Year / MonthDayYear dates such as `April-19-2026`
  - Epoch timestamps when present
  - Duration values such as `1_Hour`, `2_Hour`, `1Hour`, `90_Min`


## v36 Duration Parser Fix

- Duration extraction now supports filenames like:
  - `1Hour`
  - `1_Hour`
  - `2-Hour`
  - `90Min`


## v37 Chart Gap and UI Font Updates

- Reduced vertical gap between SLA pie chart, Top 10 Slow APIs, and Top 10 Error APIs.
- Top 10 Error APIs now starts shortly after Top 10 Slow APIs instead of far below.
- Reduced Streamlit font size for SLA Rules and Track Comparison Metrics.
- Removed bold styling from SLA/Track metric bullet items.
- Date/duration parser from v36 is retained.


## v38 Track Totals, Context Color, UI Pills

- Added `Total` rows for both AskAI and non-AskAI sections in `Track_Comparison`.
- `Report Context` heading now uses a dark colored heading style.
- Added better spacing between SLA pie, Top 10 Slow APIs, and Top 10 Error APIs charts.
- UI metric ranges are green pills again:
  - 0-10s, 10-20s, 20-30s, >30s
  - 0-2s, 3-4s, 4-6s, >6s
- SLA/Track metric bullet text remains smaller and not bold.


## v39 Final Polish

- Total rows in Track_Comparison are placed immediately below each section header.
- Report Context heading is dark colored and centered.
- Charts are spaced apart so they do not touch.
- UI title and subtitle font sizes reduced.
- Green metric pills retained for bucket ranges.


## v41 Clean Insights and Compact UI Title

- Rebuilt Insights layout:
  - Report Context is text-only, properly spaced.
  - SLA Breakdown columns are aligned in H:J.
  - Removed stray/misaligned Status/Count/Percent cells.
  - Charts are separated and readable.
- Streamlit title box now fits the text instead of spanning full width.


## v42 Tableau-like Dashboard + Chatbot

This version adds an interactive Streamlit dashboard and a built-in performance chatbot.

### New UI features
- KPI cards: Health Score, SLA Pass %, SLA Fail %, Avg Sec, P95 Sec, Errors
- Interactive filters:
  - Track
  - SLA Status
  - Track Type
  - Minimum Errors
- Plotly charts:
  - SLA Pass vs Fail
  - Top 10 Slow APIs
  - Top 10 Error APIs
  - Track analysis
- Multi-file comparison dashboard:
  - Health by run
  - Avg response by run
  - SLA fail % by run
  - Latest vs baseline API regression table
- Built-in chatbot:
  - Top slow APIs
  - Top error APIs
  - SLA breaches
  - Worst tracks
  - Overall health
  - Compare runs

### Local run
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
streamlit run app.py
```

### Deploy for team on Streamlit Community Cloud
1. Push these files to GitHub:
   - `app.py`
   - `main.py`
   - `requirements.txt`
   - `README.md`
2. Go to Streamlit Community Cloud.
3. Click **New app**.
4. Select your GitHub repo.
5. Main file path: `app.py`.
6. Click **Deploy**.
7. Share the generated app URL with your team.

### Notes
- The chatbot is deterministic and runs locally inside Streamlit.
- No OpenAI API key is required.
- The Excel report download still works exactly as before.


## v43 Smart Report Chatbot

The chatbot has been upgraded to answer a wider range of report questions locally, without an external AI key.

It can answer:
- SLA pass/fail and SLA breach questions
- Top slow APIs by avg/min/max/P90/P95/P99
- Top error APIs by error count or error %
- Track/feature summaries
- AskAI and non-AskAI questions
- Sample count and volume questions
- Report context: users, devices, date, duration, region
- Multi-file comparison and regression questions
- Keyword searches for any track, scenario, endpoint, or API name


## v44 Removed Min Errors Filter

- Removed the `Min Errors` filter from the Streamlit dashboard.
- Error analysis remains available through:
  - ErrorCount
  - ErrorPct
  - Top Error APIs chart
  - Chatbot questions like `top error APIs`


## v45 Tableau-Style Executive Dashboard

This version upgrades the Streamlit UI to a Tableau-style executive dashboard like the reference layout.

### Dashboard sections
- Aggregated Performance Overview
- KPI cards
- SLA donut chart
- Within-run comparison
- Cross-run comparison when two or more files are uploaded
- Performance heatmap
- Metrics distribution
- Auto insight box
- Drilldown table
- Smart chatbot

### Open dashboard in new tab
After deployment, add your deployed URL in Streamlit secrets:

```toml
DASHBOARD_URL = "https://your-dashboard-name.streamlit.app"
```

The app will show an **Open Dashboard in New Tab ↗** link.

### Deploy to Streamlit Community Cloud
1. Push these files to GitHub:
   - `app.py`
   - `main.py`
   - `requirements.txt`
   - `README.md`
2. Go to Streamlit Community Cloud.
3. Click **New app**.
4. Select repo and branch.
5. Main file path: `app.py`.
6. Click **Deploy**.
7. Copy the generated URL and share it with your team.

### Local run
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
streamlit run app.py
```


## v46 Region Comparison + SLA-based Colors

- Added Region Comparison panel.
- Upload multiple files with region in filename, for example:
  - `..._US_1Hour_April-19-2026_Report.json`
  - `..._EMEA_1Hour_April-19-2026_Report.json`
  - `..._APJC_1Hour_April-19-2026_Report.json`
- Region comparison supports:
  - Region P95 response time
  - Region error rate
  - Track x Region heatmap
- Heatmap colors now mean:
  - Green = P95 meets SLA
  - Red = P95 breaches SLA
- Added an `Open Dashboard in New Tab` button in the UI.
  - If `DASHBOARD_URL` is configured in Streamlit secrets, it opens that URL.
  - Otherwise, it opens the current app URL in a new browser tab.


## v48 Dashboard-only view, Insights KPIs, Chatbot on right

- Main upload page no longer shows the dashboard metrics.
- After report generation, main page shows:
  - Download Excel Report
  - Open Dashboard in New Tab ↗
- New-tab dashboard opens with `?view=dashboard&run_id=<id>`.
- Dashboard KPI strip now matches Insights Excel metrics:
  - Health Score
  - SLA Pass %
  - SLA Fail %
  - Total APIs
  - Total Samples
  - Total Errors
- Dashboard section title changed to `AGGREGATED PERFORMANCE OVERVIEW METRICS`.
- Chatbot is shown on the right side of the dashboard view.


## v49 Region dropdowns + comparison Insights

- Dashboard-only view now has three dropdown filters:
  - Result Files
  - Date
  - Region
- Dashboard charts/metrics use the selected files/date/region filters.
- Performance heatmap is larger for comparison mode.
- Metrics compare APJC/EMEA/US when multiple region files are uploaded.
- Excel `Insights` in comparison mode now aggregates all uploaded report files instead of showing only the latest report.


## v50 Top Slow Tracks visibility

- Expanded `Top Slow Tracks (P95)` table.
- Added `Max Response Sec` along with `95th Perc Sec` and `Avg Sec`.
- Added a full-width `TOP SLOW TRACKS DETAILS (P95 / AVG / MAX)` dashboard section so metrics are readable.


## v51 Executive UI

- Rebuilt Streamlit UI into executive-dashboard style.
- Main page is now clean upload-only page.
- Dashboard metrics only open in a separate dashboard tab.
- Added dark top navigation/header.
- Added executive KPI cards:
  - Health Score
  - SLA Pass %
  - SLA Fail %
  - Total APIs
  - Total Samples
  - Total Errors
- Added right-side Data & Filters panel.
- Added right-side Insights panel.
- Added right-side AI Assistant.
- Improved chart spacing and dashboard layout.
- Added region comparison table/heatmap.
- Added readable Top Slow Tracks Details table with P95 / Avg / Max.


## v52 Fix dashboard rendering and main page

- Fixed raw KPI HTML showing in dashboard by rendering KPI cards as HTML.
- Main page simplified:
  - Removed confusing fake tabs.
  - Added simple upload message.
- Open Dashboard button now opens the dashboard route cleanly using the current app base URL.


## v53 KPI rendering and action links fixed

- KPI raw HTML issue fixed by using native Streamlit metric cards.
- Main page now shows real action links after report generation:
  - Executive Dashboard
  - Excel Report
  - AI Chatbot
- Removed non-clickable static cards.
- Removed the extra success/info text after generation.


## v54 Clickable tabs + dashboard Track Comparison

- Dashboard title changed to CiscoIQ-SaaS-SupportServices Performance Dashboard.
- Top navigation tabs are now real clickable Streamlit tabs:
  - Overview
  - Compare
  - Trends
  - Drilldown
  - Reports
  - Chatbot
- View all links are now clickable buttons and route to the correct dashboard section.
- Dashboard Compare tab now shows Track Comparison tables using the same logic as Excel Track_Comparison.
- Chatbot examples expanded and irrelevant questions get a report-focused response.


## v57 Main UI fixed

- Rebuilt from stable v55.
- Main hero now fits text and removes `Upload JSON → Generate Report`.
- Removed `Upload performance report files` heading.
- Main message now says:
  `Upload one JMeter statistics.json file for a normal dashboard report. Upload two or more files for comparison.`
- Executive Dashboard / Excel Report / AI Chatbot cards are visible by default.
- Excel download button is inside the Excel Report card after generation.
- Dashboard title corrected to CiscoIQ-SaaS-Support-Services Performance Dashboard.


## v76 - v71 UI + Save Reports only

Base: v71_chatbot_top_tab_restore

Changes added only:
- Latest Team Uploads panel.
- Save uploaded reports checkbox.
- Saves latest 5 uploaded JSON files under `saved_reports/`.
- Allows team members to download latest saved uploads.


## v77 Saved uploads can generate full report options

- Latest saved JSON uploads are no longer only downloadable.
- Each saved upload has `Generate Results`.
- Latest saved uploads group has `Generate Results From Latest Saved Uploads`.
- After generation, the normal Executive Dashboard / Excel Report / AI Chatbot options become available.


## v78 Saved Upload Enhancements

- Duplicate JSON reports are skipped automatically.
- Latest Team Uploads now shows Region instead of Size.
- Saved reports show Date / Duration and generate tooltip info.
- Generate Results buttons identify which saved report is used.
- Latest Team Uploads box and main title font/height reduced.


## v79 Saved Reports cleanup + executive UI polish

- Existing duplicate saved reports are cleaned automatically.
- New duplicate uploads are skipped using file hash and file name.
- Added Remove option for saved reports.
- Removed JSON download button from saved reports table.
- Saved reports show Region, Date/Duration and Generate action.
- Main UI background updated with a more executive visual style.


## v81 Devices + Dashboard Comparison Fix

- Fixed device parsing for new saved uploads:
  - 100KDevices
  - 100K_Devices
  - 100000Devices
  - Devices100K
- Saved report tooltip now backfills Devices when old metadata has N/A.
- Dashboard Track Comparison now compares multiple reports correctly using a Run column and clean metric columns.
- Overview Track Comparison Total section now shows total rows for every selected run/report.


## v82 Dashboard comparison pivot + filters

- Track Comparison dashboard changed from row-wise report stacking to side-by-side report comparison.
- Run headers use Region + Users + Devices instead of full file names.
- Overview Track Comparison Total section shows only 3 rows: Total Avg, Min, Max.
- Data & Filters now use parsed filename fallback for Region, Date, Duration and preserve selected values with stable keys.
- Empty filters now show a warning instead of silently returning all reports.


## v83 Final Dashboard Comparison Header Fix

- Track Comparison dashboard headers are forced to short format:
  - APJC 50VU-100K
  - EMEA 100VU-100K
  - US 150VU-100K
- Added VU format parsing, for filenames like 50VU-100K.
- Added safety cleanup so full file names cannot appear as comparison headers.
- Removed Run column from Track Comparison rendering if present.
- Data & Filters continue to use clean display labels and no fallback-all behavior on empty filter selections.


## v84 Dashboard row comparison

- Removed duplicate `Management Summary` and `Leadership Actions` panels from the Streamlit UI.
- Multi-file Overview no longer cumulates uploaded reports in the top dashboard summary.
- Multi-file Overview now shows each result separately with Diff columns against the first selected result.
- Dashboard Track Comparison now shows Region and Result as row fields instead of putting regions in column names.
- Every Total/Track has three rows per Region/Result: Avg, Min and Max.


## v85 Aggregate KPI cards + comparison summary

- Restored the top `AGGREGATED PERFORMANCE OVERVIEW METRICS` strip in the same icon-card format.
- For multiple uploaded files, the KPI strip shows the latest selected result and `vs prev` deltas against the previous selected result.
- Kept the detailed `COMPARISON SUMMARY` table and chart below the KPI strip.


## v86 Track Comparison grouped rows

- Removed the separate Region column from dashboard Track Comparison because Region is already shown in Result.
- Grouped repeated Track and Result values by leaving duplicate cells blank across Avg, Min and Max rows.


## v87 Overview total metric rows fix

- Fixed Overview Track Comparison Total tables so Avg, Min and Max rows all remain visible after grouped-row formatting.
- Added an internal track key for filtering while keeping the displayed table clean.


## v88 Executive UI polish

- Renamed the saved uploads action to `Generate Comparison Dashboard` when multiple saved reports are available.
- Improved dashboard tab styling with stronger active-tab highlighting and compact icon markers.
- Updated dashboard header, panels, side cards, tables and buttons with a more management-ready executive look.


## v89 Management view and restricted upload

- The default app page now shows a username/password login for team upload and report generation.
- Configure team login with Streamlit secrets `UPLOAD_USERNAME` and `UPLOAD_PASSWORD`.
- Dashboard URLs using `?view=dashboard&run_id=...` remain view-only for management and do not show upload controls.
- After generation, the team upload page shows an `Open Management Dashboard` link that can be shared with management.
- Removed the Dashboard `Comparison` and `Reports` tabs.
- Renamed `Drilldown` to `Detailed Report`.
- Overview KPI strip now hides Total APIs, Total Samples and Total Errors.
- Excel report download moved to the right-side `Report Actions` panel.


## v90 App title cleanup

- Renamed the app header and browser page title to `CiscoIQ Performance Report App`.
- Renamed the Excel dashboard title to `CiscoIQ Performance Report App`.
