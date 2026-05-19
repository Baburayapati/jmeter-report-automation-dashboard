
from __future__ import annotations

from pathlib import Path
import html
import re
import json
import hashlib
import tempfile
import uuid
from io import BytesIO
from typing import Dict, List, Tuple
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from main import build_report, build_comparison_report, build_single_report_frames

APP_TITLE = "CiscoIQ Performance Report App"
APP_NAME_TOKEN = "CiscoIQ"


SAVED_REPORT_LIMIT = 15
PROGRAM_SAAS = "Cisco IQ SaaS Support Services"
TRACK_API = "API"
TRACK_UI = "UI"
TRACK_CLOUD = "Cloud Assist Connector"
TRACK_INVENTORY = "Customer Inventory Benchmarking"

UI_SLA_THRESHOLDS = {
    "FCP": 3.0,
    "LCP": 3.0,
    "TBT": 3.0,
    "CLS": 3.0,
    "SI": 3.0,
    "PERFORMANCE": 90.0,
}
UI_EXCLUDED_METRICS = {
    "assets",
    "assessments",
    "home",
    "settings",
    "support",
    "askai",
    "ask_ai",
}
NON_API_LATENCY_SLA_SEC = {
    TRACK_CLOUD: 2.0,
    TRACK_INVENTORY: 2.0,
}

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")


st.markdown("""
<style>
.stFileUploader {
    background: white;
    border-radius: 18px;
    padding: 14px;
    border: 1px solid #dbe4f0;
    box-shadow: 0 8px 24px rgba(15,23,42,.05);
}
.stButton>button[kind="primary"] {
    background: linear-gradient(90deg,#2563eb,#7c3aed) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    height: 48px !important;
}
.stButton>button {
    white-space: nowrap !important;
}
.stCheckbox input[type="checkbox"] {
    accent-color: #2563eb !important;
}
[data-testid="stCheckbox"] div[role="checkbox"] {
    border-color: #93c5fd !important;
}
[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
    background: #2563eb !important;
    border-color: #2563eb !important;
}

/* v59 main page exact polish */
.hero-title-box {
    display: table;
    margin: 12px auto 8px auto;
    width: auto;
    max-width: fit-content;
    background: linear-gradient(135deg,#07132f 0%, #102a63 55%, #2d2b7f 100%);
    color: white;
    border-radius: 13px;
    padding: 10px 16px;
    box-shadow: 0 10px 22px rgba(7,19,47,.16);
}
.hero-title-box h1 {
    margin: 0;
    font-size: 19px;
    line-height: 1.12;
    font-weight: 850;
    white-space: nowrap;
}
.hero-subtitle {
    text-align: center;
    color: #334155;
    font-size: 14px;
    margin: 0 auto 16px auto;
    max-width: 980px;
}

/* v61 dashboard header + tabs polish */
.top-nav {
    background: linear-gradient(90deg,#06122f 0%, #081a3f 54%, #0b1f55 100%) !important;
    color:white !important;
    border-radius: 0 0 16px 16px !important;
    padding: 14px 22px !important;
    margin: -0.6rem -1rem 12px -1rem !important;
    box-shadow: 0 10px 28px rgba(6,18,47,.22) !important;
}
.brand-icon {
    width:40px !important;
    height:40px !important;
    border-radius:12px !important;
    background:linear-gradient(135deg,#2563eb,#7c3aed) !important;
    font-size:20px !important;
}
.brand-title {
    font-size:22px !important;
    font-weight:900 !important;
    letter-spacing:-.35px !important;
}
.brand-sub {
    font-size:12px !important;
    opacity:.82 !important;
}
.nav-time {
    font-size:12px !important;
    opacity:.88 !important;
}

.region-field-label {
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #0f2b68 !important;
    margin: 0 0 6px 2px !important;
}

.track-upload-card {
    background: #ffffff;
    border: 1px solid #dbe4f0;
    border-radius: 14px;
    padding: 12px 14px;
    box-shadow: 0 8px 24px rgba(15,23,42,.05);
    margin-bottom: 10px;
}

/* Streamlit radio used as dashboard tabs */
div[role="radiogroup"] {
    display:flex !important;
    justify-content:center !important;
    gap:14px !important;
    background: #ffffff !important;
    border: 1px solid #dbe4f0 !important;
    border-radius: 14px !important;
    padding: 10px !important;
    margin: 0 0 14px 0 !important;
    box-shadow: 0 8px 20px rgba(15,23,42,.045) !important;
}
div[role="radiogroup"] label {
    background: #f8fbff !important;
    border: 1px solid #e0e7f3 !important;
    border-radius: 12px !important;
    padding: 8px 14px !important;
    min-width: 118px !important;
    text-align: center !important;
    font-weight: 800 !important;
    color: #0f2b68 !important;
    transition: .15s ease-in-out !important;
}
div[role="radiogroup"] label:hover {
    border-color:#2563eb !important;
    box-shadow:0 8px 18px rgba(37,99,235,.12) !important;
}
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
    display:none !important;
}
div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg,#4f46e5,#2563eb) !important;
    color: white !important;
    border-color: transparent !important;
    box-shadow: 0 12px 24px rgba(37,99,235,.28) !important;
}

/* Overview title strip */
.overview-title-card {
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:16px;
    padding:0;
    box-shadow:0 8px 22px rgba(15,23,42,.05);
    margin-bottom:12px;
}
.overview-title-pill {
    display:inline-block;
    background:linear-gradient(90deg,#2333a3,#3152d9);
    color:white;
    padding:9px 18px;
    border-radius:12px 12px 12px 0;
    font-size:15px;
    font-weight:900;
    letter-spacing:.2px;
    margin:0 0 8px 0;
}
.overview-title-sub {
    color:#667085;
    font-size:13px;
    padding:0 18px 12px 18px;
}


/* v62 Aggregated summary cards like reference image */
.agg-summary-card {
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:18px;
    padding:0 0 12px 0;
    box-shadow:0 18px 42px rgba(15,23,42,.075);
    margin-bottom:16px;
    overflow:hidden;
}
.agg-summary-title {
    display:inline-block;
    background:linear-gradient(90deg,#0f2b68,#2563eb 60%,#7c3aed);
    color:#ffffff;
    padding:9px 18px;
    border-radius:0 0 14px 0;
    font-size:15px;
    font-weight:900;
    letter-spacing:.2px;
    margin:0 0 8px 0;
}
.agg-kpi-row {
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap:0;
    padding:10px 16px 0 16px;
}
.agg-kpi {
    display:flex;
    align-items:center;
    gap:14px;
    min-height:122px;
    padding:10px 18px;
    border-right:1px solid #e5edf7;
}
.agg-kpi:last-child {
    border-right:none;
}
.agg-icon {
    width:48px;
    height:48px;
    border-radius:14px;
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:23px;
    font-weight:900;
    box-shadow:0 10px 20px rgba(15,23,42,.16);
    flex:0 0 48px;
}
.agg-label {
    font-size:13px;
    font-weight:850;
    color:#111827;
    margin-bottom:8px;
}
.agg-value {
    font-size:28px;
    font-weight:900;
    color:#111827;
    line-height:1.0;
    letter-spacing:-.4px;
}
.agg-suffix {
    font-size:13px;
    color:#667085;
    font-weight:650;
    margin-left:5px;
}
.agg-delta {
    font-size:12px;
    margin-top:10px;
    color:#667085;
    font-weight:650;
}
.agg-delta.good { color:#15803d; }
.agg-delta.bad { color:#ef4444; }
.agg-spark {
    width:132px;
    height:24px;
    margin-top:9px;
}
@media(max-width:1100px){
  .agg-kpi-row {grid-template-columns: repeat(2, 1fr);}
  .agg-kpi:nth-child(2n){border-right:none;}
}


/* v66 clickable top dashboard buttons */
.nav-button-row {
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:14px;
    padding:10px;
    margin-bottom:14px;
    box-shadow:0 8px 20px rgba(15,23,42,.045);
}
.nav-button-row + div button, .stButton > button {
    border-radius:12px !important;
    font-weight:800 !important;
}

/* v79 Executive main background polish */
.stApp {
  background:
    radial-gradient(circle at 8% 8%, rgba(37,99,235,.10), transparent 28%),
    radial-gradient(circle at 92% 10%, rgba(124,58,237,.12), transparent 24%),
    linear-gradient(135deg,#eef5ff 0%, #f8fbff 44%, #f2f5ff 100%) !important;
}
.main-page-card, .upload-card {
  border: 1px solid rgba(37,99,235,.12) !important;
  box-shadow: 0 14px 34px rgba(15,23,42,.08) !important;
}
.main-page-card {
  background:rgba(255,255,255,.94) !important;
  border-radius:20px !important;
  backdrop-filter: blur(12px) !important;
}
.stFileUploader {
  background: rgba(255,255,255,.92) !important;
  border: 1px dashed rgba(37,99,235,.28) !important;
  border-radius: 18px !important;
  padding: 14px !important;
  box-shadow: 0 10px 28px rgba(15,23,42,.06) !important;
}
.stButton > button, .stDownloadButton > button {
  border-radius:14px !important;
  border:1px solid rgba(37,99,235,.18) !important;
  box-shadow:0 10px 24px rgba(15,23,42,.07) !important;
  min-height:44px !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color:#2563eb !important;
  box-shadow:0 14px 28px rgba(37,99,235,.16) !important;
  transform:translateY(-1px) !important;
}
.stDataFrame, [data-testid="stDataFrame"] {
  border-radius:16px !important;
  overflow:hidden !important;
  box-shadow:0 12px 28px rgba(15,23,42,.045) !important;
}


/* FINAL UI POLISH: compact tabs/cards and reliable active button look */
div[data-testid="stHorizontalBlock"] .stButton > button {
  min-height: 36px !important;
  height: 36px !important;
  padding: 6px 10px !important;
  font-size: 12px !important;
  border-radius: 10px !important;
  line-height: 1.1 !important;
}
.nav-button-row {
  padding: 6px !important;
  margin-bottom: 8px !important;
}
.track-upload-card {
  padding: 10px 12px !important;
  margin-bottom: 8px !important;
}
[data-testid="stFileUploader"] {
  padding: 10px !important;
  min-height: 62px !important;
}
[data-testid="stFileUploaderDropzone"] {
  min-height: 74px !important;
  padding: 10px 12px !important;
}
[data-testid="stFileUploaderFile"] {
  margin-top: 6px !important;
  min-height: 34px !important;
  border-radius: 999px !important;
  border: 1px solid #d5e1f2 !important;
  background: #f8fbff !important;
  padding: 6px 12px !important;
  display: flex !important;
  align-items: center !important;
}
[data-testid="stFileUploaderFileName"] {
  font-weight: 800 !important;
  color: #0f172a !important;
}
div[data-testid="stDataFrame"] {
  margin-bottom: 0 !important;
}


/* ENTERPRISE NAV POLISH - hierarchy: Programs > Program Tracks > Dashboard Tabs */
.enterprise-nav-shell {
  background: rgba(255,255,255,.96);
  border: 1px solid #dbe4f0;
  border-radius: 18px;
  padding: 12px 14px 14px 14px;
  margin: 8px 0 14px 0;
  box-shadow: 0 12px 30px rgba(15,23,42,.06);
}
.nav-section-label {
  font-size: 11px;
  line-height: 1;
  font-weight: 900;
  color: #0f2b68;
  letter-spacing: .8px;
  text-transform: uppercase;
  margin: 2px 0 7px 2px;
}
.nav-section-sub {
  font-size: 10px;
  color: #64748b;
  font-weight: 700;
  margin: -2px 0 7px 2px;
}
.region-filter-card {
  background: linear-gradient(135deg,#f8fbff,#eef4ff);
  border: 1px solid #dbeafe;
  border-radius: 14px;
  padding: 8px 10px 10px 10px;
  min-height: 74px;
  box-shadow: 0 8px 20px rgba(37,99,235,.06);
}
.region-filter-card .region-field-label {
  font-size: 11px !important;
  margin: 0 0 4px 0 !important;
}
.region-filter-card [data-testid="stSelectbox"] {
  margin-top: -8px !important;
}
.region-filter-card [data-baseweb="select"] > div {
  min-height: 34px !important;
  border-radius: 10px !important;
  font-size: 12px !important;
}

/* Compact program and track tab buttons */
div[data-testid="stHorizontalBlock"] .stButton > button {
  min-height: 34px !important;
  height: 34px !important;
  padding: 5px 9px !important;
  font-size: 11.5px !important;
  line-height: 1.05 !important;
  border-radius: 10px !important;
  font-weight: 850 !important;
  box-shadow: 0 6px 14px rgba(15,23,42,.055) !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Dashboard tabs should look like smaller executive tabs */
.dashboard-tabs-row {
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
  padding: 7px;
  margin: 2px 0 10px 0;
  box-shadow: 0 8px 18px rgba(15,23,42,.04);
}
.dashboard-tabs-row + div .stButton > button {
  min-height: 34px !important;
  height: 34px !important;
  font-size: 11.5px !important;
}

/* Better exact-fit track cards / upload cards */
.track-upload-card, .main-page-card, .upload-card {
  border-radius: 16px !important;
}
.track-upload-card {
  padding: 10px 11px !important;
  margin-bottom: 8px !important;
  min-height: auto !important;
}
[data-testid="stFileUploader"] {
  padding: 10px !important;
  min-height: 60px !important;
}
[data-testid="stFileUploaderDropzone"] {
  min-height: 72px !important;
  padding: 10px 12px !important;
  border-radius: 14px !important;
}
[data-testid="stFileUploader"] section {
  padding: 8px !important;
}
.stButton > button, .stDownloadButton > button {
  min-height: 36px !important;
}
.panel-title {
  margin-bottom: 8px !important;
}
.side-card {
  padding: 12px !important;
  border-radius: 16px !important;
}
.block-container {
  max-width: 1600px !important;
  padding-top: .4rem !important;
}


/* FINAL CLEANUP: remove empty pill bars and tighten enterprise nav */
.enterprise-nav-shell {
  padding: 8px 10px 10px 10px !important;
  margin: 4px 0 10px 0 !important;
  border-radius: 14px !important;
}
.nav-section-label {
  margin: 0 0 4px 1px !important;
  font-size: 10px !important;
}
.nav-section-sub {
  display: none !important;
}
.dashboard-tabs-row {
  padding: 5px !important;
  margin: 0 0 6px 0 !important;
  border-radius: 12px !important;
}
.region-filter-card {
  padding: 5px 7px 7px 7px !important;
  min-height: 50px !important;
  border-radius: 12px !important;
}
.region-filter-card .region-field-label {
  font-size: 10px !important;
  margin-bottom: 2px !important;
}
.region-filter-card [data-testid="stSelectbox"] {
  margin-top: -10px !important;
}
.region-filter-card [data-baseweb="select"] > div {
  min-height: 30px !important;
  height: 30px !important;
  border-radius: 9px !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button,
.dashboard-tabs-row + div .stButton > button {
  min-height: 30px !important;
  height: 30px !important;
  padding: 3px 8px !important;
  font-size: 10.5px !important;
  border-radius: 9px !important;
}

/* remove blank saved-report filename placeholder bars */
.saved-report-name-box,
.empty-file-name-box,
.report-name-placeholder,
div:empty[class*="saved"],
div:empty[class*="placeholder"] {
  display: none !important;
}

/* defensive: hide empty custom html pill bars */
div[style*="border-radius:999px"]:empty,
div[style*="border-radius: 999px"]:empty,
div[style*="height:34px"]:empty,
div[style*="height: 34px"]:empty {
  display: none !important;
}

/* reduce accidental whitespace from markdown-only separators */
[data-testid="stMarkdownContainer"] p:empty {
  display: none !important;
}
[data-testid="stMarkdownContainer"]:has(p:empty) {
  margin: 0 !important;
}


/* SCREENSHOT STYLE DASHBOARD NAV - Programs left, tracks/views right */
.sshot-wrapper {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 18px;
  background: rgba(255,255,255,.94);
  border: 1px solid #dbe4f0;
  border-radius: 22px;
  margin: 12px 0 10px 0;
  padding: 0;
  overflow: hidden;
  box-shadow: 0 18px 44px rgba(15,23,42,.075);
}
.sshot-left {
  background: linear-gradient(135deg,#2563eb 0%,#7c3aed 100%);
  padding: 17px 16px 16px 16px;
  min-height: 222px;
}
.sshot-right {
  padding: 18px 18px 16px 0;
}
.sshot-title {
  font-size: 11px;
  font-weight: 950;
  letter-spacing: .9px;
  text-transform: uppercase;
  margin: 0 0 10px 2px;
  color: #0f2b68;
}
.sshot-left .sshot-title {
  color: white;
}
.sshot-region-card {
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 16px;
  padding: 10px 11px 12px 11px;
  box-shadow: 0 12px 24px rgba(15,23,42,.055);
  min-height: 86px;
}
.sshot-region-card [data-testid="stSelectbox"] {
  margin-top: -8px !important;
}
.sshot-region-card [data-baseweb="select"] > div {
  min-height: 36px !important;
  height: 36px !important;
  border-radius: 11px !important;
  font-size: 12px !important;
}
.sshot-wrapper .stButton > button, .sshot-tabs .stButton > button {
  height: 42px !important;
  min-height: 42px !important;
  padding: 6px 14px !important;
  border-radius: 12px !important;
  font-size: 13px !important;
  font-weight: 850 !important;
  white-space: nowrap !important;
  line-height: 1.05 !important;
  border: 1px solid #dbe4f0 !important;
  box-shadow: 0 8px 18px rgba(15,23,42,.06) !important;
}
.sshot-left .stButton > button {
  justify-content: flex-start !important;
  text-align: left !important;
  background: transparent !important;
  color: #ffffff !important;
  border: 1px solid transparent !important;
  box-shadow: none !important;
}
.sshot-left .stButton > button[kind="primary"] {
  background: #ffffff !important;
  color: #4f46e5 !important;
  border-color: rgba(255,255,255,.8) !important;
  box-shadow: 0 12px 24px rgba(15,23,42,.16) !important;
}
.sshot-right .stButton > button[kind="primary"], .sshot-tabs .stButton > button[kind="primary"] {
  background: linear-gradient(90deg,#2563eb,#7c3aed) !important;
  color: #ffffff !important;
  border-color: transparent !important;
}
.sshot-right .stButton > button[kind="secondary"], .sshot-tabs .stButton > button[kind="secondary"] {
  background: #ffffff !important;
  color: #111827 !important;
}
.sshot-wrapper [data-testid="stVerticalBlock"] {
  gap: .38rem !important;
}
.sshot-tabs {
  background: rgba(255,255,255,.94);
  border: 1px solid #dbe4f0;
  border-radius: 18px;
  padding: 12px 14px 14px 14px;
  margin: 0 0 14px 378px;
  box-shadow: 0 14px 32px rgba(15,23,42,.055);
}
/* remove all old blank bars */
.exec-empty-space,
.saved-report-name-box,
.empty-file-name-box,
.report-name-placeholder,
div[style*="border-radius:999px"]:empty,
div[style*="border-radius: 999px"]:empty,
div[style*="height:34px"]:empty,
div[style*="height: 34px"]:empty,
div[style*="min-height:34px"]:empty,
div[style*="min-height: 34px"]:empty {
  display: none !important;
}
@media(max-width:1100px){
  .sshot-wrapper { grid-template-columns: 1fr; }
  .sshot-right { padding: 14px; }
  .sshot-tabs { margin-left: 0; }
}


/* HEADER REMOVED + PROGRAMS INSIDE BLUE PANEL */
.sshot-wrapper{
  overflow: hidden !important;
}
.sshot-left{
  border-top-left-radius: 22px;
  border-bottom-left-radius: 22px;
}


/* EXACT NAV LAYOUT FIX - matches requested screenshot using real Streamlit columns */
.exact-nav-anchor {
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] {
  background: rgba(255,255,255,.94) !important;
  border: 1px solid #dbe4f0 !important;
  border-radius: 22px !important;
  overflow: hidden !important;
  box-shadow: 0 18px 44px rgba(15,23,42,.075) !important;
  margin: 12px 0 6px 0 !important;
  gap: 0 !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] > div:first-child {
  background: linear-gradient(135deg,#2563eb 0%,#7c3aed 100%) !important;
  padding: 16px 16px 10px 16px !important;
  min-height: 0 !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
  padding: 34px 18px 8px 18px !important;
}
.exact-label {
  display: inline-block;
  font-size: 16px;
  font-weight: 850;
  letter-spacing: .2px;
  text-transform: none;
  margin: 0 0 10px 0;
  color: #111827;
  border: 1px solid #c9d4e8;
  border-radius: 10px;
  background: rgba(255,255,255,.76);
  padding: 4px 10px;
}
.exact-label.white {
  color: #111827;
  text-shadow: none;
  background: rgba(255,255,255,.88);
}
/* Button styles inside exact nav */
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] .stButton > button {
  height: 42px !important;
  min-height: 42px !important;
  border-radius: 12px !important;
  font-size: 13px !important;
  font-weight: 850 !important;
  border: 1px solid #dbe4f0 !important;
  box-shadow: 0 8px 18px rgba(15,23,42,.06) !important;
  white-space: nowrap !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] > div:first-child .stButton > button {
  justify-content: flex-start !important;
  text-align: left !important;
  border-color: transparent !important;
  box-shadow: none !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] > div:first-child .stButton > button[kind="secondary"] {
  background: transparent !important;
  color: #ffffff !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] > div:first-child .stButton > button[kind="primary"] {
  background: #ffffff !important;
  color: #4f46e5 !important;
  border-color: rgba(255,255,255,.8) !important;
  box-shadow: 0 12px 24px rgba(15,23,42,.16) !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button[kind="primary"] {
  background: linear-gradient(90deg,#2563eb,#7c3aed) !important;
  color: #ffffff !important;
  border-color: transparent !important;
}
.exact-nav-anchor + div[data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button[kind="secondary"] {
  background: #ffffff !important;
  color: #111827 !important;
}
/* Region filter exact compact card */
.exact-region-card {
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 16px;
  padding: 10px 11px 12px 11px;
  box-shadow: 0 12px 24px rgba(15,23,42,.055);
  min-height: 88px;
  margin-top: 0;
}
.exact-region-card [data-testid="stSelectbox"] { margin-top: -8px !important; }
.exact-region-card [data-baseweb="select"] > div {
  min-height: 36px !important;
  height: 36px !important;
  border-radius: 11px !important;
  font-size: 12px !important;
}
/* Remove old accidental blank bars/boxes */
.sshot-left, .sshot-right, .sshot-wrapper, .sshot-tabs,
.exec-nav-card, .enterprise-nav-shell {
  all: unset;
}
div[style*="border-radius:999px"]:empty,
div[style*="border-radius: 999px"]:empty,
div[style*="height:34px"]:empty,
div[style*="height: 34px"]:empty,
div[style*="height: 70px"]:empty,
div[style*="height:70px"]:empty,
.saved-report-name-box,
.empty-file-name-box,
.report-name-placeholder,
.exec-empty-space {
  display: none !important;
}
@media(max-width:1100px){
  .exact-nav-anchor + div[data-testid="stHorizontalBlock"] {
    display: block !important;
  }
}


/* FINAL HTML NAV MATCH - fixed screenshot-style layout */
.ciq-nav-wrap {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 18px;
  background: rgba(255,255,255,.96);
  border: 1px solid #dbe4f0;
  border-radius: 22px;
  overflow: hidden;
  box-shadow: 0 18px 44px rgba(15,23,42,.075);
  margin: 12px 0 16px 0;
}
.ciq-program-panel {
  background: linear-gradient(135deg,#2563eb 0%,#7c3aed 100%);
  padding: 18px 16px 18px 16px;
  min-height: 224px;
}
.ciq-main-panel {
  padding: 18px 18px 16px 0;
}
.ciq-title {
  font-size: 11px;
  font-weight: 950;
  letter-spacing: .9px;
  text-transform: uppercase;
  margin-bottom: 12px;
  color: #0f2b68;
}
.ciq-program-panel .ciq-title {
  color: #fff;
}
.ciq-program-link,
.ciq-track-link,
.ciq-tab-link {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 42px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 850;
  text-decoration: none !important;
  box-sizing: border-box;
}
.ciq-program-link {
  justify-content: flex-start;
  padding: 0 14px;
  color: #fff !important;
  margin-bottom: 10px;
  border: 1px solid transparent;
}
.ciq-program-link.active {
  background: #fff;
  color: #4f46e5 !important;
  border-color: rgba(255,255,255,.8);
  box-shadow: 0 12px 24px rgba(15,23,42,.16);
}
.ciq-track-grid {
  display: grid;
  grid-template-columns: .58fr .68fr 1.55fr 1.95fr 190px;
  gap: 14px;
  align-items: start;
  margin-bottom: 16px;
}
.ciq-track-link,
.ciq-tab-link {
  color: #111827 !important;
  background: #fff;
  border: 1px solid #dbe4f0;
  box-shadow: 0 8px 18px rgba(15,23,42,.06);
  padding: 0 10px;
  white-space: nowrap;
}
.ciq-track-link.active,
.ciq-tab-link.active {
  color: #fff !important;
  background: linear-gradient(90deg,#2563eb,#7c3aed);
  border-color: transparent;
}
.ciq-region-card {
  grid-row: span 2;
  background: #fff;
  border: 1px solid #dbe4f0;
  border-radius: 16px;
  padding: 11px;
  min-height: 92px;
  box-shadow: 0 12px 24px rgba(15,23,42,.055);
}
.ciq-region-title {
  font-size: 11px;
  font-weight: 950;
  letter-spacing: .8px;
  text-transform: uppercase;
  color: #0f2b68;
  margin-bottom: 8px;
}
.ciq-region-select {
  width: 100%;
  height: 38px;
  border: 1px solid #dbe4f0;
  border-radius: 11px;
  background: #f8fafc;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 650;
  color: #111827;
}
.ciq-tab-grid {
  display: grid;
  grid-template-columns: 1.05fr 1.42fr 1.32fr 1.15fr 190px;
  gap: 14px;
  align-items: start;
}
.ciq-spacer {
  width: 190px;
}
@media(max-width:1100px){
  .ciq-nav-wrap { grid-template-columns: 1fr; }
  .ciq-main-panel { padding: 16px; }
  .ciq-track-grid, .ciq-tab-grid { grid-template-columns: 1fr; }
  .ciq-spacer { display:none; }
}


/* CLEAN UPLOAD PAGE ONLY - do not affect login or dashboard */
.clean-upload-page-marker + div,
body:has(.clean-upload-page-marker) .block-container {
  max-width: 1480px !important;
}

/* 2x2 upload cards - neat, compact, readable */
body:has(.clean-upload-page-marker) [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px !important;
  background: rgba(255,255,255,.96) !important;
  border: 1px solid #dbe4f0 !important;
  box-shadow: 0 10px 24px rgba(15,23,42,.045) !important;
}

body:has(.clean-upload-page-marker) [data-testid="stFileUploader"] {
  padding: 10px !important;
}

body:has(.clean-upload-page-marker) [data-testid="stFileUploaderDropzone"] {
  min-height: 78px !important;
  padding: 10px 12px !important;
  border-radius: 14px !important;
}

body:has(.clean-upload-page-marker) .stButton > button {
  min-height: 38px !important;
  border-radius: 11px !important;
}

/* Hide the three lower shortcut cards only on upload page:
   Executive Dashboard / Excel Report / AI Chatbot */
body:has(.clean-upload-page-marker) .main-page-card,
body:has(.clean-upload-page-marker) .feature-grid,
body:has(.clean-upload-page-marker) .quick-grid,
body:has(.clean-upload-page-marker) .upload-page-quick-row {
  display: none !important;
}


/* FORCE HIDE BOTTOM EXECUTIVE/EXCEL/CHATBOT CARDS */
body:has(.clean-upload-page-marker) div[data-testid="stHorizontalBlock"]:has(.main-page-card){
    display:none !important;
}
body:has(.clean-upload-page-marker) .main-page-card{
    display:none !important;
}


/* LEFT PANEL FOR UPLOAD PAGE */
body:has(.upload-left-panel-marker) .block-container {
  max-width: none !important;
  padding: 108px 30px 24px 286px !important;
}
.upload-left-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 248px;
  height: 100vh;
  background: linear-gradient(180deg,#061633 0%,#071e52 58%,#06142f 100%);
  z-index: 9998;
  padding: 28px 14px;
  box-sizing: border-box;
  box-shadow: 12px 0 30px rgba(15,23,42,.16);
}
.upload-left-logo {
  color: #ffffff;
  font-size: 30px;
  font-weight: 900;
  margin: 8px 10px 36px 10px;
}
.upload-left-link {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 46px;
  padding: 0 14px;
  border-radius: 14px;
  margin-bottom: 12px;
  color: #dbeafe !important;
  text-decoration: none !important;
  font-size: 15px;
  font-weight: 850;
}
.upload-left-link.active {
  background: linear-gradient(90deg,#4f46e5,#7c3aed);
  color: #ffffff !important;
  box-shadow: 0 12px 28px rgba(124,58,237,.38);
}
.upload-left-link:hover {
  background: rgba(255,255,255,.10);
  color: #ffffff !important;
}
.upload-topbar {
  position: fixed;
  top: 0;
  left: 248px;
  right: 0;
  height: 82px;
  background: #ffffff;
  border-bottom: 1px solid #dbe4f0;
  z-index: 9997;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px 0 34px;
  box-sizing: border-box;
}
.upload-top-title {
  font-size: 22px;
  font-weight: 950;
  color: #0f172a;
}
.upload-top-actions {
  display:flex;
  align-items:center;
  gap:18px;
  font-size:14px;
  font-weight:850;
  color:#0f172a;
}
body:has(.upload-left-panel-marker) .hero-title-box,
body:has(.upload-left-panel-marker) .hero-subtitle {
  display: none !important;
}
@media(max-width:1100px){
  body:has(.upload-left-panel-marker) .block-container {
    padding: 20px !important;
  }
  .upload-left-sidebar,.upload-topbar {
    position: relative;
    left: auto;
    width: auto;
    height: auto;
  }
}


/* 4 COLUMN + CLEAN TOP ACTIONS FIX */
body:has(.upload-left-panel-marker) .block-container {
  max-width: none !important;
  padding: 108px 24px 24px 286px !important;
}

body:has(.upload-left-panel-marker) .upload-top-actions,
body:has(.native-upload-marker) .native-actions,
body:has(.exact-upload-shell) .exact-actions {
  display: flex !important;
  align-items: center !important;
  gap: 16px !important;
  font-size: 14px !important;
  font-weight: 800 !important;
  color: #0f172a !important;
  white-space: nowrap !important;
}

body:has(.upload-left-panel-marker) .upload-top-actions span,
body:has(.native-upload-marker) .native-actions span,
body:has(.exact-upload-shell) .exact-actions span {
  line-height: 1 !important;
}

/* Prevent browser/Streamlit toolbar visual duplication on top-right where possible */
body:has(.upload-left-panel-marker) [data-testid="stToolbar"],
body:has(.native-upload-marker) [data-testid="stToolbar"],
body:has(.exact-upload-shell) [data-testid="stToolbar"] {
  display: none !important;
}

/* Keep 4 upload cards side-by-side and compact */
body:has(.upload-left-panel-marker) div[data-testid="stHorizontalBlock"],
body:has(.clean-upload-page-marker) div[data-testid="stHorizontalBlock"] {
  gap: 12px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stVerticalBlockBorderWrapper"],
body:has(.clean-upload-page-marker) [data-testid="stVerticalBlockBorderWrapper"] {
  min-height: 300px !important;
  border-radius: 15px !important;
  padding: 10px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stFileUploaderDropzone"],
body:has(.clean-upload-page-marker) [data-testid="stFileUploaderDropzone"] {
  min-height: 76px !important;
  padding: 8px 10px !important;
  border-radius: 14px !important;
}


/* SIDEBAR NAV FIX + REMOVE UPLOAD BOTTOM CARDS */
body:has(.upload-left-panel-marker) .block-container {
  max-width: none !important;
  padding: 108px 26px 26px 286px !important;
}
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] {
  width: 244px !important;
  min-width: 244px !important;
  background: linear-gradient(180deg,#061633 0%,#071d50 58%,#06142f 100%) !important;
  border-right: 1px solid rgba(255,255,255,.08) !important;
  box-shadow: 10px 0 30px rgba(15,23,42,.16) !important;
}
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] > div:first-child {
  padding: 20px 12px !important;
}
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] * {
  color: #ffffff !important;
}
.upload-left-logo {
  color:#fff !important;
  font-size:28px !important;
  margin: 10px 8px 34px 8px !important;
}
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton {
  margin-bottom: 10px !important;
}
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button {
  height: 48px !important;
  min-height: 48px !important;
  border-radius: 14px !important;
  padding: 0 14px !important;
  font-size: 14px !important;
  font-weight: 850 !important;
  justify-content: flex-start !important;
  text-align: left !important;
  border: none !important;
  background: transparent !important;
  color: #dbeafe !important;
  box-shadow: none !important;
}
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: linear-gradient(90deg,#4f46e5,#7c3aed) !important;
  box-shadow: 0 10px 24px rgba(124,58,237,.36) !important;
  color:#fff !important;
}
.upload-topbar {
  position: fixed !important;
  top: 0 !important;
  left: 244px !important;
  right: 0 !important;
  height: 86px !important;
  background:#fff !important;
  border-bottom:1px solid #dbe4f0 !important;
  z-index:9997 !important;
  display:flex !important;
  align-items:center !important;
  justify-content:space-between !important;
  padding:0 32px 0 38px !important;
}
.upload-top-title {
  font-size:22px !important;
  font-weight:950 !important;
  color:#0f172a !important;
}
.upload-top-actions { display:none !important; }
body:has(.upload-left-panel-marker) [data-testid="stToolbar"] { display:none !important; }
body:has(.upload-left-panel-marker) .hero-title-box,
body:has(.upload-left-panel-marker) .hero-subtitle { display:none !important; }

/* keep upload cards in 4 columns */
body:has(.upload-left-panel-marker) div[data-testid="stHorizontalBlock"] {
  gap: 14px !important;
  margin-bottom: 22px !important;
}
body:has(.upload-left-panel-marker) [data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255,255,255,.96) !important;
  border:1px solid #dbe4f0 !important;
  border-radius:16px !important;
  box-shadow:0 10px 24px rgba(15,23,42,.04) !important;
  padding:14px !important;
}

/* remove Executive Dashboard / Excel Report / AI Chatbot cards under Program Track Uploads */
body:has(.upload-left-panel-marker) .main-page-card,
body:has(.upload-left-panel-marker) .quick-grid,
body:has(.upload-left-panel-marker) .upload-page-quick-row {
  display:none !important;
}


/* 2X2 TRACK UPLOADS + REPORTS UI */
body:has(.upload-left-panel-marker) .block-container {
  max-width: none !important;
  padding: 108px 34px 28px 286px !important;
}

body:has(.upload-left-panel-marker) div[data-testid="stHorizontalBlock"] {
  gap: 18px !important;
  margin-bottom: 18px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stVerticalBlockBorderWrapper"] {
  min-height: 300px !important;
  max-height: none !important;
  border-radius: 16px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stFileUploaderDropzone"] {
  min-height: 72px !important;
  height: 78px !important;
  border-radius: 14px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stFileUploaderDropzone"] button {
  height: 34px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stAlert"] {
  min-height: 48px !important;
}

/* Reports tab cards in clean 2x2 */
body:has(.upload-left-panel-marker) .report-program-card {
  min-height: 260px !important;
  border-radius: 16px !important;
}


/* FINAL NAV + REPORTS + 2X2 FIX */
body:has(.upload-left-panel-marker) .block-container {
  max-width: none !important;
  padding: 108px 26px 26px 26px !important;
}

/* if topbar is fixed, align it with native sidebar width */
.upload-topbar {
  left: 244px !important;
  right: 0 !important;
}

/* 2x2 cards remain clean */
body:has(.upload-left-panel-marker) div[data-testid="stHorizontalBlock"] {
  gap: 18px !important;
  margin-bottom: 18px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stVerticalBlockBorderWrapper"] {
  min-height: 300px !important;
  border-radius: 16px !important;
  background: rgba(255,255,255,.96) !important;
  border: 1px solid #dbe4f0 !important;
  box-shadow: 0 10px 24px rgba(15,23,42,.04) !important;
  padding: 14px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stFileUploaderDropzone"] {
  min-height: 72px !important;
  height: 78px !important;
  border-radius: 14px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stAlert"] {
  min-height: 44px !important;
  border-radius: 10px !important;
}

/* remove bottom shortcut cards under Program Track Uploads */
body:has(.upload-left-panel-marker) .main-page-card,
body:has(.upload-left-panel-marker) .quick-grid,
body:has(.upload-left-panel-marker) .upload-page-quick-row {
  display: none !important;
}

/* Reports tab 2x2 cards */
.report-program-card {
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 16px;
  padding: 16px;
  min-height: 260px;
  box-shadow: 0 10px 24px rgba(15,23,42,.04);
}
.report-program-title {
  font-size: 18px;
  font-weight: 950;
  color: #0f2b68;
  margin-bottom: 14px;
}
.dashboard-static-card {
  max-width: 720px;
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 10px 24px rgba(15,23,42,.04);
}
.dashboard-static-title {
  font-size: 20px;
  font-weight: 950;
  color: #0f2b68;
  margin-bottom: 10px;
}
.dashboard-static-desc {
  color: #64748b;
  font-size: 14px;
  line-height: 1.55;
  margin-bottom: 20px;
}
.dashboard-static-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 42px;
  padding: 0 18px;
  border-radius: 12px;
  color: #ffffff !important;
  text-decoration: none !important;
  font-weight: 850;
  background: linear-gradient(90deg,#2563eb,#7c3aed);
}


/* REPORTS INSIDE CARDS FIX */
.reports-subtitle {
  color: #64748b !important;
  font-size: 15px !important;
  margin: -4px 0 18px 0 !important;
}

.report-program-card {
  background: #ffffff !important;
  border: 1px solid #dbe4f0 !important;
  border-radius: 16px !important;
  padding: 18px !important;
  min-height: 260px !important;
  box-shadow: 0 10px 24px rgba(15,23,42,.04) !important;
  margin-bottom: 18px !important;
}

.report-program-title {
  font-size: 22px !important;
  font-weight: 950 !important;
  color: #0f2b68 !important;
  margin-bottom: 14px !important;
}

.report-program-card .panel-title,
.report-program-card h2,
.report-program-card h3,
.report-program-card h4 {
  display: none !important;
}

.report-program-card [data-testid="stVerticalBlockBorderWrapper"] {
  min-height: auto !important;
  max-height: none !important;
  padding: 10px !important;
}

.report-program-card [data-testid="stAlert"] {
  min-height: 48px !important;
  border-radius: 10px !important;
}

.report-program-card .stButton > button {
  height: 38px !important;
  border-radius: 10px !important;
}


/* REPORTS REAL CONTAINER CARDS FINAL */
.reports-subtitle {
  color: #64748b !important;
  font-size: 15px !important;
  margin: -4px 0 18px 0 !important;
}

body:has(.upload-left-panel-marker) .report-program-title {
  font-size: 22px !important;
  font-weight: 950 !important;
  color: #0f2b68 !important;
  margin-bottom: 14px !important;
}

/* Reports page bordered containers */
body:has(.upload-left-panel-marker) div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px !important;
}

/* Compact saved rows */
.compact-saved-row {
  background: #f8fbff !important;
  border: 1px solid #dbe4f0 !important;
  border-radius: 10px !important;
  padding: 10px !important;
  margin-bottom: 10px !important;
}

.compact-saved-cell-name {
  font-size: 14px !important;
  font-weight: 800 !important;
  color: #0f172a !important;
  margin-bottom: 8px !important;
}

.compact-saved-row .stButton > button {
  height: 36px !important;
  border-radius: 10px !important;
}

/* Remove previous fake HTML cards if any */
.report-program-card {
  display: none !important;
}


/* DASHBOARD STATIC CARD + TAB RESPONSIVENESS FIX */
.dashboard-static-card {
  max-width: 920px !important;
  padding: 22px 26px !important;
}

.dashboard-static-title {
  font-size: 20px !important;
  line-height: 1.15 !important;
  margin-bottom: 12px !important;
}

.dashboard-static-desc {
  font-size: 15px !important;
  line-height: 1.45 !important;
  margin-bottom: 20px !important;
}

.dashboard-static-btn {
  height: 40px !important;
  padding: 0 18px !important;
  font-size: 15px !important;
  border-radius: 12px !important;
}

/* keep top dashboard nav clicks snappy visually */
button[kind="primary"],
.stButton > button {
  transition: none !important;
}


body:has(.upload-left-panel-marker) .panel-title:has(+ .dashboard-static-card) {
  display: none !important;
}


/* STATIC DASHBOARD URL + PERFORMANCE POLISH */
.dashboard-static-card {
  max-width: 960px !important;
  padding: 20px 24px !important;
}
.dashboard-static-title {
  font-size: 22px !important;
  line-height: 1.15 !important;
  margin-bottom: 10px !important;
}
.dashboard-static-desc {
  font-size: 14px !important;
  line-height: 1.45 !important;
  margin-bottom: 16px !important;
}
.dashboard-static-btn {
  height: 38px !important;
  padding: 0 16px !important;
  font-size: 14px !important;
  border-radius: 11px !important;
}
.static-url-box {
  margin-top: 14px;
  background: #f8fbff;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  padding: 10px 12px;
  color: #0f2b68;
  font-size: 13px;
  font-weight: 700;
  word-break: break-all;
}
.page-url-row {
  margin-top: 12px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.7;
}
.page-url-row span {
  color: #0f2b68;
  font-weight: 800;
}
.page-url-row code {
  background: #eef4ff;
  border-radius: 6px;
  padding: 2px 6px;
  color: #0f172a;
}

/* Faster perceived tab clicks: remove animation/large shadows */
* {
  transition-duration: 0s !important;
  animation-duration: 0s !important;
}
.executive-tab,
.track-tab,
button,
.stButton > button {
  transition: none !important;
}


/* DASHBOARD TAB SPEED + SMALL TITLE */
.dashboard-static-title {
  font-size: 20px !important;
  line-height: 1.15 !important;
}
.dashboard-static-card {
  max-width: 900px !important;
}
.ciq-tab-link,
.ciq-track-link,
.ciq-program-link,
.stButton > button {
  transition: none !important;
  animation: none !important;
}
.js-plotly-plot,
.plot-container {
  transition: none !important;
}


/* ROUTES + DASHBOARD SPEED FIX */
.dashboard-static-title {
  font-size: 18px !important;
  line-height: 1.15 !important;
}
.dashboard-static-card {
  max-width: 900px !important;
  padding: 18px 22px !important;
}
.dashboard-static-desc {
  font-size: 13px !important;
  margin-bottom: 14px !important;
}
.dashboard-static-btn {
  height: 36px !important;
  font-size: 13px !important;
}
.ciq-tab-link,
.ciq-track-link,
.ciq-program-link,
.stButton > button {
  transition: none !important;
  animation: none !important;
}


/* Login/upload routes, chatbot/settings cards */
.dashboard-static-title {
  font-size: 18px !important;
  line-height: 1.15 !important;
}
.static-url-box {
  margin-top: 14px;
  background: #f8fbff;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  padding: 10px 12px;
  color: #0f2b68;
  font-size: 13px;
  font-weight: 700;
  word-break: break-all;
}
.settings-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.settings-card {
  display: block;
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 16px;
  padding: 18px;
  text-decoration: none !important;
  box-shadow: 0 10px 24px rgba(15,23,42,.04);
}
.settings-card:hover {
  border-color: #2563eb;
  box-shadow: 0 14px 30px rgba(37,99,235,.12);
}
.settings-title {
  font-size: 17px;
  font-weight: 950;
  color: #0f2b68;
  margin-bottom: 8px;
}
.settings-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.45;
}
@media(max-width: 1100px) {
  .settings-grid { grid-template-columns: 1fr; }
}


/* EXCEL SAVED REPORTS LIST */
.excel-report-name {
  font-size: 17px !important;
  font-weight: 900 !important;
  color: #111827 !important;
  margin: 18px 0 10px 0 !important;
}
.excel-row-gap {
  height: 18px;
}


/* API ONLY EXCEL REPORT PAGE */
.saved-report-title {
  font-size: 18px !important;
  font-weight: 900 !important;
  color: #111827 !important;
  margin: 18px 0 10px 0 !important;
  word-break: break-word !important;
}

.saved-report-divider {
  height: 22px !important;
}

body:has(.upload-left-panel-marker) .report-program-title {
  font-size: 22px !important;
  font-weight: 950 !important;
  color: #0f2b68 !important;
  margin-bottom: 12px !important;
}

body:has(.upload-left-panel-marker) .reports-subtitle {
  color: #64748b !important;
  font-size: 15px !important;
  margin: -4px 0 18px 0 !important;
}

body:has(.upload-left-panel-marker) .stDownloadButton > button,
body:has(.upload-left-panel-marker) .stButton > button {
  height: 38px !important;
  border-radius: 10px !important;
}


/* In Excel Report page, never show UI/Cloud/Inventory report cards */
body:has(.api-excel-file-name) .report-program-card:not(:first-child) {
  display: none !important;
}


/* Hide page headings on Reports/Excel pages; cards have their own headings */
body:has(.report-program-title) > div .panel-title {
  display: none !important;
}
body:has(.excel-saved-name) .report-program-title {
  font-size: 18px !important;
}
body:has(.excel-saved-name) .stDownloadButton > button,
body:has(.excel-saved-name) .stButton > button {
  height: 38px !important;
  border-radius: 10px !important;
}


/* Hide page headings on Reports/Excel pages; cards have their own headings */
body:has(.report-program-title) .panel-title {
  display: none !important;
}
body:has(.excel-api-only-page) .stDownloadButton > button,
body:has(.excel-api-only-page) .stButton > button {
  height: 38px !important;
  border-radius: 10px !important;
}
/* Defensive: if stale report-tab titles remain after browser refresh/navigation, hide them on Excel page */
body:has(.excel-api-only-page) div:has(> .report-program-title):has(> div:nth-child(1)):not(:has(.excel-saved-name)) {
  display: none !important;
}




/* Hide hidden-slot parent card only, not the API card */
body:has(.excel-report-active-page) [data-testid="stVerticalBlockBorderWrapper"]:has(.excel-hidden-slot) {
  display: none !important;
}
body:has(.excel-report-active-page) .stDownloadButton > button,
body:has(.excel-report-active-page) .stButton > button {
  min-height: 38px !important;
  border-radius: 10px !important;
}


/* REVERT BAD LOADING OVERLAY */
body:has(.upload-left-panel-marker) .block-container {
  opacity: 1 !important;
}



/* EXCEL EMPTY BAR + FAST BUTTON FIX */
.excel-only-title {
  font-size: 18px !important;
  font-weight: 900 !important;
  color: #0f2b68 !important;
  margin-bottom: 16px !important;
}
.excel-only-name {
  font-size: 15px !important;
  font-weight: 850 !important;
  color: #111827 !important;
  margin: 12px 0 10px 0 !important;
  word-break: break-word !important;
}
.excel-only-gap {
  height: 18px !important;
}
body:has(.excel-only-title) .stDownloadButton > button,
body:has(.excel-only-title) .stButton > button {
  display: inline-flex !important;
  min-height: 38px !important;
  border-radius: 10px !important;
}


/* SIDEBAR ALIGNMENT FIX - UI ONLY */
.sidebar-nav-item,
.left-nav-item,
.nav-link,
[data-testid="stSidebar"] a {
  display: flex !important;
  align-items: center !important;
}

.sidebar-nav-item .icon,
.left-nav-item .icon {
  width: 20px !important;
  min-width: 20px !important;
  display: inline-flex !important;
  justify-content: center !important;
  align-items: center !important;
  margin-right: 10px !important;
}

.sidebar-nav-item,
.left-nav-item {
  padding-left: 18px !important;
}

.sidebar-nav-item.active,
.left-nav-item.active {
  border-radius: 18px !important;
}

/* Top logo/dashboard symbol cleanup */
.sidebar-logo,
.nav-logo,
.left-panel-logo {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  margin-bottom: 18px !important;
}

.sidebar-logo img,
.nav-logo img,
.left-panel-logo img {
  width: 26px !important;
  height: 26px !important;
  object-fit: contain !important;
}


/* LEFT PANEL ICON POLISH - UI ONLY, NO FUNCTIONALITY CHANGE */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] {
  background: linear-gradient(180deg, #071a3a 0%, #09245a 100%) !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button {
  justify-content: flex-start !important;
  text-align: left !important;
  padding-left: 58px !important;
  padding-right: 20px !important;
  height: 54px !important;
  border-radius: 18px !important;
  font-size: 16px !important;
  font-weight: 800 !important;
  letter-spacing: -0.1px !important;
  white-space: nowrap !important;
  font-family: "Inter", "Segoe UI", Arial, sans-serif !important;
}

/* Make the icon character occupy a visually fixed lane */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button p {
  text-align: left !important;
  width: 100% !important;
  margin: 0 !important;
  font-size: 16px !important;
  line-height: 1 !important;
  white-space: pre !important;
  font-variant-numeric: tabular-nums !important;
}

/* Inactive items: clean text, no boxes */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button[kind="secondary"],
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
  background: transparent !important;
  border: 0 !important;
  color: rgba(255,255,255,.92) !important;
  box-shadow: none !important;
}

/* Active item: screenshot-like purple pill */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
  color: #ffffff !important;
  border: 0 !important;
  box-shadow: 0 16px 34px rgba(88, 80, 236, .28) !important;
}

/* Keep all buttons in one straight vertical menu column */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton {
  width: 100% !important;
  margin: 0 0 22px 0 !important;
}

/* Top icon/logo: smaller and aligned with menu icon lane */
body:has(.upload-left-panel-marker) .upload-left-logo {
  color: #ffffff !important;
  font-size: 28px !important;
  line-height: 1 !important;
  margin: 44px 0 62px 34px !important;
  text-align: left !important;
  width: 36px !important;
  height: 36px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  letter-spacing: -4px !important;
}

/* Remove extra default sidebar padding offsets */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] > div:first-child {
  padding-left: 10px !important;
  padding-right: 18px !important;
}


/* Exact sidebar icon style from reference image */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button {
  font-size: 15px !important;
  font-weight: 700 !important;
  padding-left: 46px !important;
  height: 50px !important;
  border-radius: 18px !important;
  justify-content: flex-start !important;
}

body:has(.upload-left-panel-marker) .upload-left-logo {
  font-size: 22px !important;
  margin-left: 22px !important;
  margin-top: 26px !important;
  margin-bottom: 44px !important;
  letter-spacing: -3px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton {
  margin-bottom: 16px !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button p {
  font-size: 15px !important;
}


/* FINAL LEFT SIDEBAR PROFESSIONAL UI - UI ONLY */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] {
  width: 238px !important;
  min-width: 238px !important;
  background: linear-gradient(180deg, #071a3a 0%, #082355 100%) !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] > div:first-child {
  padding: 22px 14px 18px 14px !important;
}

/* top logo like reference: small, top-left */
body:has(.upload-left-panel-marker) .upload-left-logo {
  color: #ffffff !important;
  font-size: 22px !important;
  line-height: 1 !important;
  width: 26px !important;
  height: 26px !important;
  margin: 10px 0 42px 12px !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  letter-spacing: -3px !important;
  text-align: left !important;
}

/* button rows: compact, left aligned, same column */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton {
  margin: 0 0 12px 0 !important;
  width: 100% !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  height: 48px !important;
  min-height: 48px !important;
  border-radius: 14px !important;
  justify-content: flex-start !important;
  text-align: left !important;
  padding: 0 14px 0 22px !important;
  font-size: 14px !important;
  font-weight: 750 !important;
  letter-spacing: -0.1px !important;
  box-shadow: none !important;
  transform: none !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button p {
  font-size: 14px !important;
  font-weight: 750 !important;
  line-height: 1 !important;
  margin: 0 !important;
  color: inherit !important;
  white-space: pre !important;
  text-align: left !important;
}

/* inactive menu */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button[kind="secondary"],
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
  background: transparent !important;
  border: 1px solid transparent !important;
  color: rgba(255,255,255,.88) !important;
}

/* active purple pill */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: linear-gradient(90deg, #5b45f3 0%, #7d3ef0 100%) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  color: #ffffff !important;
  box-shadow: 0 14px 28px rgba(99,75,241,.28) !important;
}

/* hover */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,.08) !important;
  color: #ffffff !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
  background: linear-gradient(90deg, #5b45f3 0%, #7d3ef0 100%) !important;
}

/* reduce oversized Streamlit sidebar collapse/icon spacing side effects */
body:has(.upload-left-panel-marker) [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
  display: none !important;
}


/* Better top sidebar logo */
body:has(.upload-left-panel-marker) .upload-left-logo {
  font-size: 26px !important;
  font-weight: 800 !important;
  color: #ffffff !important;
  opacity: 0.95 !important;
  letter-spacing: 0 !important;
}


/* remove empty sidebar logo spacing */
body:has(.upload-left-panel-marker) .upload-left-logo {
  display: none !important;
}

/* keep collapse action disabled only on upload page */
body:has(.upload-left-panel-marker) [data-testid="stSidebarCollapseButton"],
body:has(.upload-left-panel-marker) [data-testid="collapsedControl"],
body:has(.upload-left-panel-marker) button[kind="header"],
body:has(.upload-left-panel-marker) button[aria-label="Close sidebar"],
body:has(.upload-left-panel-marker) button[aria-label="Collapse sidebar"] {
  display: none !important;
  visibility: hidden !important;
  pointer-events: none !important;
}

/* if sidebar was collapsed earlier, force it visible on upload page */
body:has(.upload-left-panel-marker) section[data-testid="stSidebar"] {
  transform: none !important;
  margin-left: 0 !important;
  left: 0 !important;
}

/* FINAL TWEAK: reduce header-gap + straighten left tabs */
body:has(.upload-left-panel-marker) .block-container {
  padding-top: 82px !important;
}

body:has(.upload-left-panel-marker) .upload-program-title {
  font-size: 18px !important;
  font-weight: 950 !important;
  margin: -2px 0 8px 0 !important;
  line-height: 1.15 !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton {
  margin: 0 0 10px 0 !important;
}

body:has(.upload-left-panel-marker) [data-testid="stSidebar"] .stButton > button {
  border-radius: 8px !important;
  width: 100% !important;
  justify-content: flex-start !important;
  text-align: left !important;
}

</style>
""", unsafe_allow_html=True)

params = st.query_params
view_param = str(params.get("view", "")).strip().strip("./ ").lower()
page_param = str(params.get("page", "")).strip().strip("./ ").lower()
if page_param == "login":
    st.session_state.team_authenticated = False
dashboard_only = view_param == "dashboard"
team_upload_view = not dashboard_only
run_id = params.get("run_id", "")


@st.cache_resource
def get_dashboard_store():
    return {}


dashboard_store = get_dashboard_store()


st.markdown(
    """
<style>
:root {
  --navy:#07132f;
  --navy2:#0a1b3f;
  --blue:#2563eb;
  --purple:#6d28d9;
  --green:#16a34a;
  --red:#dc2626;
  --orange:#f59e0b;
  --card:#ffffff;
  --border:#dbe4f0;
  --muted:#667085;
}
.stApp {
  background: #f4f7fb;
  color: #111827;
}
[data-testid="stHeader"] { background: transparent; }
.block-container {
  max-width: 1560px;
  padding: 0.6rem 1rem 1.6rem 1rem;
}
#MainMenu, footer { visibility: hidden; }
.app-shell {
  background: white;
  border: 1px solid #dce3ef;
  border-radius: 18px;
  padding: 12px;
  box-shadow: 0 10px 30px rgba(10,27,63,0.06);
}
.hero {
  background:
    radial-gradient(circle at 20% 20%, rgba(59,130,246,.22), transparent 28%),
    radial-gradient(circle at 80% 10%, rgba(124,58,237,.28), transparent 26%),
    linear-gradient(135deg,#07132f 0%, #0a1b3f 50%, #0f2b68 100%);
  color:white;
  border-radius: 18px;
  padding: 12px 22px;
  box-shadow: 0 14px 32px rgba(7,19,47,.18);
  margin-bottom: 18px;
}
.hero h1 {
  margin: 0;
  font-size: 20px;
  line-height: 1.15;
  font-weight: 850;
  letter-spacing:-.4px;
}
.hero p {
  margin: 8px 0 0 0;
  color: rgba(255,255,255,.82);
  font-size: 14px;
}
.hero-actions {
  display:flex;
  gap:12px;
  align-items:center;
  margin-top: 18px;
  flex-wrap: wrap;
}
.primary-pill {
  display:inline-block;
  background: linear-gradient(90deg,#4f46e5,#2563eb);
  color:white !important;
  text-decoration:none !important;
  padding: 10px 16px;
  border-radius: 12px;
  font-weight:750;
  box-shadow: 0 12px 24px rgba(37,99,235,.24);
}
.secondary-pill {
  display:inline-block;
  background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.20);
  color:white !important;
  text-decoration:none !important;
  padding: 9px 14px;
  border-radius: 12px;
  font-weight:650;
}
.top-nav {
  display:flex;
  align-items:center;
  justify-content:space-between;
  background:linear-gradient(90deg,#0f2b68,#2563eb 55%,#7c3aed);
  color:white;
  border-radius: 0 0 22px 22px;
  padding: 16px 22px;
  margin: -0.6rem -1rem 16px -1rem;
  box-shadow: 0 18px 42px rgba(7,19,47,.20);
  border-bottom: 1px solid rgba(255,255,255,.16);
}
.brand {
  display:flex;
  align-items:center;
  gap: 12px;
}
.brand-icon {
  width:34px;height:34px;border-radius:10px;
  background:linear-gradient(135deg,#4f46e5,#06b6d4);
  display:flex;align-items:center;justify-content:center;
  font-size:18px;
}
.brand-title { font-size:21px;font-weight:900;line-height:1.1;letter-spacing:-.25px; }
.brand-sub { font-size:12px;color:rgba(255,255,255,.78);margin-top:3px;}
.nav-tabs {
  display:flex;
  gap: 8px;
  align-items:center;
}
.nav-tab {
  color:white;
  padding:8px 12px;
  border-radius:10px;
  font-size:13px;
  font-weight:650;
  opacity:.9;
}
.nav-tab.active {
  background: linear-gradient(90deg,#4f46e5,#2563eb);
  box-shadow:0 8px 16px rgba(37,99,235,.28);
}
.nav-time {font-size:11px;color:rgba(255,255,255,.82);text-align:right;}
.panel {
  background: rgba(255,255,255,.94);
  border: 1px solid rgba(148,163,184,.24);
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 18px 42px rgba(15,23,42,.075);
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
}
.panel-title {
  font-size: 14px;
  font-weight: 900;
  color: #102a63;
  margin-bottom: 8px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  letter-spacing:.16px;
  line-height: 1.2;
}
.panel-title .tag {
  font-size:11px;
  background:linear-gradient(90deg,#eef4ff,#f5f3ff);
  color:#1d4ed8;
  padding:4px 10px;
  border-radius:999px;
  border:1px solid #dbeafe;
}
.dashboard-subtitle {
  font-size: 13px;
  font-weight: 800;
  color: #1f3b78;
  margin: 4px 0 6px 0;
  line-height: 1.2;
}
.kpi-grid {
  display:grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}
.kpi-card {
  background:white;
  border:1px solid var(--border);
  border-radius:14px;
  padding:14px;
  min-height:96px;
  box-shadow: 0 6px 18px rgba(15,23,42,.045);
  display:flex;
  gap:12px;
  align-items:flex-start;
}
.kpi-icon {
  width:38px;height:38px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  color:white;font-size:19px;flex:0 0 38px;
  box-shadow: 0 10px 18px rgba(0,0,0,.12);
}
.kpi-label { font-size:12px;color:#111827;font-weight:750; }
.kpi-value { font-size:24px;font-weight:850;color:#111827;margin-top:6px;line-height:1.0; }
.kpi-sub { font-size:11px;color:var(--muted);margin-top:8px; }
.kpi-sub.good { color:#15803d; }
.kpi-sub.bad { color:#dc2626; }
.grid-3 {
  display:grid;
  grid-template-columns: 1.1fr 1fr 1fr;
  gap:12px;
}
.grid-2 {
  display:grid;
  grid-template-columns: 1.1fr .9fr;
  gap:12px;
}
.side-card {
  background: rgba(255,255,255,.94);
  border:1px solid rgba(148,163,184,.24);
  border-radius:18px;
  padding:16px;
  box-shadow: 0 18px 40px rgba(15,23,42,.075);
  margin-bottom:16px;
  backdrop-filter: blur(10px);
}
.insight-item {
  display:flex;
  gap:10px;
  align-items:flex-start;
  margin: 10px 0;
  font-size:13px;
  color:#1f2937;
}
.dot {
  width:22px;height:22px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  color:white;font-size:12px;font-weight:800;flex:0 0 22px;
}
.filter-card {
  background:#f8fbff;
  border:1px solid var(--border);
  border-radius:12px;
  padding: 12px;
}
.chat-card {
  background:white;
  border: 1px solid #c7b7ff;
  border-radius:13px;
  padding:14px;
  box-shadow: 0 8px 22px rgba(109,40,217,.10);
}
.chat-header {
  background:linear-gradient(90deg,#6d28d9,#7c3aed);
  color:white;
  padding:10px 12px;
  border-radius:10px;
  font-size:13px;
  font-weight:800;
  margin:-2px -2px 12px -2px;
}
.mini-link {
  color:#2563eb !important;
  font-size:12px;
  font-weight:700;
  text-decoration:none !important;
}
.stButton > button {
  border-radius: 10px !important;
  font-weight: 750 !important;
}
.stDownloadButton > button {
  border-radius: 10px !important;
  font-weight: 750 !important;
}
[data-testid="stFileUploader"] {
  background:white;
  border:1px dashed #a6b4ca;
  border-radius:14px;
  padding: 16px;
}
[data-testid="stMetric"] {
  background:white;
  border-radius: 12px;
}
.upload-card {
  max-width: 1100px;
  margin: 0 auto;
}
.main-page-card {
  background:white;
  border:1px solid var(--border);
  border-radius:16px;
  padding:22px;
  box-shadow: 0 12px 30px rgba(15,23,42,.06);
  margin-bottom:16px;
}
.login-form-wrap {
  max-width: 660px;
  margin: 18px auto 0 auto;
}
.login-form-wrap [data-testid="stTextInput"] {
  margin-bottom: 14px;
}
.login-form-wrap [data-testid="stTextInput"] input {
  min-height: 48px !important;
  border: 1.5px solid #1f2937 !important;
  border-radius: 4px !important;
  background: #ffffff !important;
}
.login-form-wrap [data-testid="InputInstructions"] {
  display: none !important;
}
.login-form-wrap [data-testid="stTextInput"] label {
  color: #1f2937 !important;
  font-size: 18px !important;
  font-weight: 700 !important;
  padding-bottom: 4px !important;
}
.login-form-wrap .stButton > button {
  margin-top: 8px;
}
.feature-grid {
  display:grid;
  grid-template-columns: repeat(3, 1fr);
  gap:12px;
  margin-top:14px;
}
.feature {
  border:1px solid #e3e9f5;
  border-radius:14px;
  padding:14px;
  background:#fbfdff;
}
.feature h4 { margin:0 0 6px 0;font-size:14px;color:#0f2b68; }
.feature p { margin:0;color:#667085;font-size:12px; }
@media(max-width:1100px){
  .kpi-grid,.grid-3,.grid-2,.feature-grid {grid-template-columns:1fr;}
  .nav-tabs {display:none;}
}

/* Executive KPI metric styling */
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #dbe4f0 !important;
    border-radius: 14px !important;
    padding: 16px 16px !important;
    box-shadow: 0 8px 20px rgba(15,23,42,.055) !important;
    min-height: 104px !important;
}
div[data-testid="stMetricLabel"] {
    font-weight: 800 !important;
    color: #111827 !important;
}
div[data-testid="stMetricValue"] {
    font-weight: 850 !important;
    color: #111827 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


def get_store():
    return dashboard_store


def infer_program_track(label: str) -> Tuple[str, str]:
    name = str(label or "").upper()
    if "ONPREM" in name and "RISK" in name:
        return "Cisco IQ Onprem - Risk App", TRACK_API
    if "ONPREM" in name and "ASSET" in name:
        return "Cisco IQ Onprem - Assets", TRACK_API
    if "CX AI ASSISTANT" in name or "CX_AI_ASSISTANT" in name:
        return "CX AI Assistant", TRACK_API

    if "CLOUD" in name and "CONNECTOR" in name:
        return PROGRAM_SAAS, TRACK_CLOUD
    if "BENCHMARK" in name or "INVENTORY" in name:
        return PROGRAM_SAAS, TRACK_INVENTORY
    if "LIGHTHOUSE" in name or re.search(r"(?:^|[_\-])UI(?:[_\-]|$)", name):
        return PROGRAM_SAAS, TRACK_UI
    return PROGRAM_SAAS, TRACK_API


def canonical_track_name(value: str) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return TRACK_API
    if text == "API" or "ASKAI" in text:
        return TRACK_API
    if text == "UI" or "LIGHTHOUSE" in text:
        return TRACK_UI
    if "CLOUD" in text and "CONNECTOR" in text:
        return TRACK_CLOUD
    if "INVENTORY" in text or "BENCHMARK" in text:
        return TRACK_INVENTORY
    return str(value or "").strip()


def frame_track_name(frames: Dict[str, pd.DataFrame]) -> str:
    info = frames.get("Run_Info")
    info_row = info.iloc[0].to_dict() if info is not None and not info.empty else {}
    return canonical_track_name(info_row.get("Track") or infer_program_track(frames.get("Label", ""))[1])


def merge_run_frames_by_track(existing_frames: List[Dict[str, pd.DataFrame]], new_frames: List[Dict[str, pd.DataFrame]], track_name: str) -> List[Dict[str, pd.DataFrame]]:
    target_track = canonical_track_name(track_name)
    kept = [frames for frames in (existing_frames or []) if frame_track_name(frames) != target_track]
    merged = kept + (new_frames or [])
    return add_region_to_frames(merged)


def sanitize_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip())
    token = re.sub(r"-+", "-", token).strip("-")
    return token or "NA"


def normalize_users_token(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"(?i)\s*(concurrent\s*)?users?\s*", "", text)
    text = re.sub(r"\s+", "", text)
    if not text or text.upper() == "N/A":
        return "NAUsers"
    text = re.sub(r"(?i)vu", "", text).strip()
    return f"{text}Users"


def normalize_devices_token(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"(?i)\s*devices?\s*", "", text)
    text = re.sub(r"\s+", "", text)
    if not text or text.upper() == "N/A":
        return "NA-Devices"
    return f"{text}Devices"


def extract_env_token(file_name: str) -> str:
    upper = str(file_name or "").upper()
    for env in ["PROD", "UAT", "QA", "DEV", "STAGE", "STG", "TEST"]:
        if re.search(rf"(?:^|[_\-\s]){env}(?:$|[_\-\s])", upper):
            return env
    return "PROD"


def extract_mmddyyyy_from_text(value: str) -> str | None:
    """Return MMDDYYYY parsed from common filename/date formats."""
    text = str(value or "").strip()
    if not text:
        return None
    month_map = {
        "jan": "01", "january": "01", "feb": "02", "february": "02", "mar": "03", "march": "03",
        "apr": "04", "april": "04", "may": "05", "jun": "06", "june": "06", "jul": "07", "july": "07",
        "aug": "08", "august": "08", "sep": "09", "sept": "09", "september": "09", "oct": "10", "october": "10",
        "nov": "11", "november": "11", "dec": "12", "december": "12",
    }
    def valid(mm: str, dd: str, yyyy: str) -> str | None:
        try:
            mm_i, dd_i, yy_i = int(mm), int(dd), int(yyyy)
            if 1 <= mm_i <= 12 and 1 <= dd_i <= 31 and 2000 <= yy_i <= 2100:
                return f"{mm_i:02d}{dd_i:02d}{yy_i:04d}"
        except Exception:
            return None
        return None
    m = re.search(r"(?i)(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[_\-/\s,]*(\d{1,2})[_\-/\s,]*(20\d{2})", text)
    if m:
        month = month_map.get(m.group(1).lower())
        out = valid(month, m.group(2), m.group(3)) if month else None
        if out:
            return out
    m = re.search(r"(?<!\d)(20\d{2})[_\-/\s]?(\d{1,2})[_\-/\s]?(\d{1,2})(?!\d)", text)
    if m:
        out = valid(m.group(2), m.group(3), m.group(1))
        if out:
            return out
    for m in re.finditer(r"(?<!\d)(\d{1,2})[_\-/\s]?(\d{1,2})[_\-/\s]?(20\d{2})(?!\d)", text):
        out = valid(m.group(1), m.group(2), m.group(3))
        if out:
            return out
    return None


def to_mmddyyyy(date_value: str) -> str:
    parsed = extract_mmddyyyy_from_text(date_value)
    if parsed:
        return parsed
    return datetime.now().strftime("%m%d%Y")


def to_mm_dd_yyyy(date_value: str) -> str:
    token = to_mmddyyyy(date_value)
    return f"{token[:2]}-{token[2:4]}-{token[4:8]}"


def build_standard_report_name(track_name: str, program_name: str, original_name: str, extension: str) -> str:
    info = infer_saved_report_info(original_name)
    date_token = to_mmddyyyy(info.get("date", "") or original_name)
    epoch_token = f"EPOC-{int(datetime.now().timestamp())}"
    users_token = normalize_users_token(info.get("users", "N/A"))
    devices_token = normalize_devices_token(info.get("devices", "N/A"))
    region_token = sanitize_token(info.get("region", "Unknown")).upper()
    env_token = sanitize_token(info.get("env", "") or extract_env_token(original_name)).upper()
    run_token = sanitize_token(info.get("run_id", "") or f"RUN-{uuid.uuid4().hex[:8].upper()}")
    track_token = sanitize_token(track_name)
    app_token = sanitize_token(APP_NAME_TOKEN)
    program_token = sanitize_token(program_name)
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"{track_token}_{app_token}_{program_token}_{date_token}_{epoch_token}_{users_token}_{devices_token}_{region_token}_{env_token}_{run_token}{ext.lower()}"


def report_title(region: str, users: str, devices: str, include_users: bool = True) -> str:
    region_token = str(region or "Unknown").strip().upper()
    user_value = re.sub(r"(?i)\s*(concurrent\s*)?users?\s*", "", str(users or "").strip())
    user_value = re.sub(r"(?i)vu", "", user_value).strip() or "NA"
    if re.fullmatch(r"\d{9,13}", user_value):
        user_value = "NA"
    region_user_match = re.search(r"(\d+(?:\.\d+)?\s*K?)\s*USERS?", region_token, re.IGNORECASE)
    if region_user_match:
        if user_value.upper() == "NA":
            user_value = region_user_match.group(1).replace(" ", "")
        region_token = ""
    user_token = f"{user_value}Users"
    device_value = re.sub(r"(?i)\s*devices?\s*", "", str(devices or "").strip())
    device_value = device_value or "NA"
    device_token = f"{device_value}Devices"
    if include_users:
        if region_token and region_token not in {"N/A", "NA", "UNKNOWN"}:
            return f"{region_token}-{user_token}-{device_token}"
        return f"{user_token}-{device_token}"
    return f"{region_token}-{device_token}"


def add_ui_sla_columns(apis_df: pd.DataFrame) -> pd.DataFrame:
    df = apis_df.copy()
    if df.empty:
        return df
    df["Feature"] = df["Feature"].astype(str)
    df["Scenario"] = df.get("Scenario", "").astype(str)
    df["Endpoint"] = df.get("Endpoint", "").astype(str)
    df["API"] = df["Feature"] + "/" + df["Scenario"] + "/" + df["Endpoint"]
    for col in [
        "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec",
        "sampleCount", "errorCount", "errorPct",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "SLA Sec" not in df.columns:
        df["SLA Sec"] = 2.0
    df["SLA Sec"] = pd.to_numeric(df["SLA Sec"], errors="coerce")
    if "SLA Status" not in df.columns:
        status = (
            (df["Avg ResTime in sec"] <= df["SLA Sec"])
            & (df["Min ResTime in sec"] <= df["SLA Sec"])
            & (df["MaxRes Time in sec"] <= df["SLA Sec"])
        ).map({True: "PASS", False: "FAIL"})
        df["SLA Status"] = status
    if "SLA Breach Sec" not in df.columns:
        df["SLA Breach Sec"] = (df["Avg ResTime in sec"] - df["SLA Sec"]).clip(lower=0).round(2)
    if "Track Type" not in df.columns:
        df["Track Type"] = df["Feature"].astype(str)
    return df


def process_uploaded_file(path: Path, label: str) -> Dict[str, pd.DataFrame]:
    frames = build_single_report_frames(path)
    frames["APIs"] = add_ui_sla_columns(frames["APIs"])
    frames["Label"] = label
    frames["Region"] = region_from_frames(frames)
    info = infer_saved_report_info(label)
    program_name, track_name = infer_program_track(label)
    if "Run_Info" in frames and frames["Run_Info"] is not None and not frames["Run_Info"].empty:
        frames["Run_Info"]["Application"] = info.get("application", APP_NAME_TOKEN)
        frames["Run_Info"]["Program"] = program_name
        frames["Run_Info"]["Track"] = track_name
        frames["Run_Info"]["Environment"] = info.get("env", "PROD")
        frames["Run_Info"]["Run ID"] = info.get("run_id", "N/A")
        frames["Run_Info"]["Epoch"] = info.get("epoch", "N/A")
    return frames


def region_from_frames(frames: Dict[str, pd.DataFrame]) -> str:
    info = frames.get("Run_Info")
    if info is not None and not info.empty and "Region" in info.columns:
        region = str(info.iloc[0].get("Region", "N/A")).strip()
        if region and region.upper() != "N/A":
            return region
    label = str(frames.get("Label", ""))
    upper = label.upper()
    for region in ["APJC", "EMEA", "US", "AMER", "EU", "LATAM", "INDIA"]:
        if re.search(rf"(?:^|[_\-\s]){region}(?:$|[_\-\s])", upper):
            return region
    return "Unknown"


def add_region_to_frames(run_frames: List[Dict[str, pd.DataFrame]]) -> List[Dict[str, pd.DataFrame]]:
    for frames in run_frames:
        frames["Region"] = region_from_frames(frames)
    return run_frames


def summarize_run(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return dict(avg_sec=0, min_sec=0, success_rate=0, error_rate=0, transactions=0, performance_score=0, sla_compliance=0, errors=0, samples=0, max_sec=0)
    samples = pd.to_numeric(df.get("sampleCount", 0), errors="coerce").fillna(0).sum()
    errors = pd.to_numeric(df.get("errorCount", 0), errors="coerce").fillna(0).sum()
    success_rate = round(((samples - errors) / samples) * 100, 2) if samples else 0
    error_rate = round((errors / samples) * 100, 2) if samples else 0
    sla_status = df.get("SLA Status", pd.Series(dtype=str)).astype(str).str.upper()
    sla_scope = sla_status.isin(["PASS", "FAIL"])
    sla_pass_pct = round((sla_status.eq("PASS") & sla_scope).sum() / sla_scope.sum() * 100, 2) if sla_scope.sum() else 0
    score = round(max(0, min(100, sla_pass_pct - error_rate)), 2)
    return dict(
        avg_sec=round(float(df["Avg ResTime in sec"].mean()), 2),
        min_sec=round(float(df["Min ResTime in sec"].min()), 2) if "Min ResTime in sec" in df.columns else 0,
        success_rate=success_rate,
        error_rate=error_rate,
        transactions=int(len(df)),
        performance_score=score,
        sla_compliance=sla_pass_pct,
        errors=int(errors),
        samples=int(samples),
        max_sec=round(float(df["MaxRes Time in sec"].max()), 2) if "MaxRes Time in sec" in df.columns else 0,
    )


def safe_cols(df: pd.DataFrame, cols: List[str]) -> List[str]:
    return [c for c in cols if c in df.columns]


def is_excluded_ui_metric(name: str) -> bool:
    norm = sanitize_column_name(name)
    return any(norm == token or norm.startswith(f"{token}_") for token in UI_EXCLUDED_METRICS)


def is_speed_index_metric(name: str) -> bool:
    norm = sanitize_column_name(name)
    return norm in {"si", "speed_index", "speedindex"} or "speed_index" in norm


def apply_ui_speed_index_sla(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    metric_col = "Scenario" if "Scenario" in work.columns else "Feature"
    speed_mask = work[metric_col].astype(str).map(is_speed_index_metric)

    avg_series = pd.to_numeric(work.get("Avg ResTime in sec", 0), errors="coerce").fillna(0)
    work.loc[speed_mask, "SLA Sec"] = 3.0
    work.loc[speed_mask, "SLA Status"] = (avg_series[speed_mask] <= 3.0).map({True: "PASS", False: "FAIL"})
    work.loc[speed_mask, "SLA Breach Sec"] = (avg_series[speed_mask] - 3.0).clip(lower=0).round(3)

    work.loc[~speed_mask, "SLA Sec"] = pd.NA
    work.loc[~speed_mask, "SLA Status"] = "N/A"
    work.loc[~speed_mask, "SLA Breach Sec"] = pd.NA
    return work


def track_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    work = df.copy()
    for col, default in {
        "Avg ResTime in sec": 0,
        "Min ResTime in sec": 0,
        "MaxRes Time in sec": 0,
        "errorCount": 0,
        "errorPct": 0,
        "sampleCount": 0,
        "SLA Status": "PASS",
        "Feature": "Unknown",
    }.items():
        if col not in work.columns:
            work[col] = default

    out = (
        work.groupby(["Feature"], dropna=False)
        .agg(
            APIs=("Feature", "count"),
            Avg_Sec=("Avg ResTime in sec", "mean"),
            Min_Sec=("Min ResTime in sec", "min"),
            Max_Sec=("MaxRes Time in sec", "max"),
            Errors=("errorCount", "sum"),
            ErrorPct=("errorPct", "mean"),
            SLA_Fails=("SLA Status", lambda x: (x == "FAIL").sum()),
            Samples=("sampleCount", "sum"),
        )
        .reset_index()
    )
    out["SLA Fail %"] = (out["SLA_Fails"] / out["APIs"] * 100).round(2)
    for col in ["Avg_Sec", "Min_Sec", "Max_Sec", "ErrorPct"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).round(2)
    return out.sort_values(["Max_Sec", "Avg_Sec", "Errors"], ascending=False)


def sla_color_for_track(track_name: str, metric_value: float) -> float:
    threshold = 10 if str(track_name).upper().startswith("ASKAI") else 2
    return 1 if float(metric_value or 0) < threshold else 0


def combined_df(run_frames: List[Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    parts = []
    for frames in run_frames:
        tmp = frames["APIs"].copy()
        tmp["Run"] = frames["Label"]
        tmp["Region"] = frames.get("Region", region_from_frames(frames))
        parts.append(tmp)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()









def render_upload_left_panel() -> str:
    """Native Streamlit sidebar navigation; does not reload app or lose login session."""

    components.html(
        """
<script>
(function () {
  const doc = window.parent.document;
  const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
  const openBtn = doc.querySelector('button[aria-label="Open sidebar"], button[aria-label="Expand sidebar"]');
  const isCollapsed = sidebar && (
    sidebar.getAttribute('aria-expanded') === 'false' ||
    getComputedStyle(sidebar).transform.includes('-')
  );
  if (isCollapsed && openBtn) {
    openBtn.click();
  }
})();
</script>
""",
        height=0,
    )

    st.markdown('<div class="upload-left-panel-marker"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="upload-topbar">
  <div class="upload-top-title">CiscoIQ Performance Report App</div>
  <div class="upload-top-actions"></div>
</div>
""",
        unsafe_allow_html=True,
    )

    if "upload_left_page" not in st.session_state:
        st.session_state.upload_left_page = "Track Uploads"

    nav_items = [
        ("Dashboard", "⌂  Dashboard"),
        ("Track Uploads", "▣  Track Uploads"),
        ("Reports", "▤  Reports"),
        ("Excel Report", "▥  Excel Report"),
        ("AI Chatbot", "☻  AI Chatbot"),
        ("Settings", "⚙  Settings"),
    ]

    with st.sidebar:
        st.markdown('<div class="upload-left-logo"></div>', unsafe_allow_html=True)
        for page_name, label in nav_items:
            active = st.session_state.upload_left_page == page_name
            if st.button(
                label,
                key=f"upload_nav_{sanitize_token(page_name)}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.upload_left_page = page_name
                st.rerun()

    return st.session_state.upload_left_page


def render_upload_sidebar_page(page_name: str) -> bool:
    """Return True if a sidebar page was rendered and upload cards should stop."""
    base_app_url = "https://ciscoiq-report-automation-app.streamlit.app/"

    if page_name == "Dashboard":
        run_id_value = st.session_state.get("run_id", "")
        dash_href = f"{base_app_url}?view=dashboard&run_id={run_id_value}" if run_id_value else f"{base_app_url}?view=dashboard"
        st.markdown(f"""
        <div class="dashboard-static-card">
          <div class="dashboard-static-title">View All Results</div>
          <div class="dashboard-static-desc">
            Share this dashboard URL with management. After you generate results, this opens the latest dashboard view.
          </div>
          <a class="dashboard-static-btn" href="{dash_href}" target="_blank">Open Results Dashboard ↗</a>
          <div class="static-url-box">{dash_href}</div>
          <div class="page-url-row">
            <span>Login:</span> <code>{base_app_url}?page=login</code><br/>
            <span>Upload:</span> <code>{base_app_url}?page=upload</code><br/>
            <span>Dashboard:</span> <code>{base_app_url}?view=dashboard</code><br/>
            <span>Chatbot:</span> <code>{base_app_url}?view=dashboard&tab=Chatbot</code>
          </div>
        </div>
        """, unsafe_allow_html=True)
        return True

    if page_name == "Reports":
        r1, r2 = st.columns(2, gap="medium")
        r3, r4 = st.columns(2, gap="medium")

        with r1:
            with st.container(border=True):
                st.markdown("### API Reports")
                render_saved_reports_compact_for_track(TRACK_API, title="", key_prefix="reports_api")

        with r2:
            with st.container(border=True):
                st.markdown("### UI Reports")
                render_saved_reports_compact_for_track(TRACK_UI, title="", key_prefix="reports_ui")

        with r3:
            with st.container(border=True):
                st.markdown("### Cloud Assist Reports")
                render_saved_reports_compact_for_track(TRACK_CLOUD, title="", key_prefix="reports_cloud")

        with r4:
            with st.container(border=True):
                st.markdown("### Inventory Reports")
                render_saved_reports_compact_for_track(TRACK_INVENTORY, title="", key_prefix="reports_inventory")

        return True

    if page_name == "Excel Report":
        # API-only Excel page. No HTML wrapper, so no empty bar appears above the heading.
        api_uploads = [
            item for item in normalize_saved_uploads(load_saved_uploads())
            if (item.get("track") or infer_program_track(item.get("file_name", ""))[1]) == TRACK_API
        ]

        with st.container(border=True):
            st.markdown('<div class="excel-only-title">API Excel Reports</div>', unsafe_allow_html=True)

            if not api_uploads:
                st.info("No saved API reports yet.")
                return True

            for idx, item in enumerate(api_uploads):
                original_name = item.get("file_name", "API_Report.json")
                saved_name = item.get("saved_name", "")
                saved_path = SAVED_REPORTS_DIR / saved_name
                display_name = compact_saved_file_label(original_name)

                st.markdown(f'<div class="excel-only-name">{display_name}</div>', unsafe_allow_html=True)

                col_download, col_remove = st.columns(2, gap="medium")

                with col_download:
                    if saved_path.exists():
                        try:
                            excel_bytes_for_download = cached_excel_bytes_for_saved_api(
                                str(saved_path),
                                display_name,
                                saved_path.stat().st_mtime,
                            )
                            st.download_button(
                                "Download Excel Report",
                                data=excel_bytes_for_download,
                                file_name=f"{display_name}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"excel_simple_download_{idx}_{sanitize_token(saved_name)}",
                                use_container_width=True,
                            )
                        except Exception as exc:
                            st.error(f"Unable to prepare Excel report: {exc}")
                    else:
                        st.warning("Saved source file is missing.")

                with col_remove:
                    if st.button(
                        "Remove",
                        key=f"excel_simple_remove_{idx}_{sanitize_token(saved_name)}",
                        use_container_width=True,
                    ):
                        remove_saved_upload(saved_name)
                        st.rerun()

                st.markdown('<div class="excel-only-gap"></div>', unsafe_allow_html=True)

        return True

    if page_name == "AI Chatbot":
        run_id_value = st.session_state.get("run_id", "")
        chat_href = f"{base_app_url}?view=dashboard&tab=Chatbot&run_id={run_id_value}" if run_id_value else f"{base_app_url}?view=dashboard&tab=Chatbot"
        st.markdown(f"""
        <div class="dashboard-static-card">
          <div class="dashboard-static-title">AI Chatbot</div>
          <div class="dashboard-static-desc">
            Share this static chatbot URL to open the dashboard chatbot. After results are generated, it opens with the latest available data.
          </div>
          <a class="dashboard-static-btn" href="{chat_href}" target="_blank">Open AI Chatbot ↗</a>
          <div class="static-url-box">{chat_href}</div>
        </div>
        """, unsafe_allow_html=True)
        return True

    if page_name == "Settings":
        st.markdown(f"""
        <div class="settings-grid">
          <a class="settings-card" href="{base_app_url}?page=login" target="_self">
            <div class="settings-title">Logout / Login</div>
            <div class="settings-desc">Return to the secure login page.</div>
          </a>
          <a class="settings-card" href="{base_app_url}?page=upload" target="_self">
            <div class="settings-title">Upload Page</div>
            <div class="settings-desc">Open Program Track Uploads.</div>
          </a>
          <a class="settings-card" href="{base_app_url}?view=dashboard" target="_blank">
            <div class="settings-title">Dashboard Link</div>
            <div class="settings-desc">Open management dashboard in a new tab.</div>
          </a>
          <a class="settings-card" href="{base_app_url}?view=dashboard&tab=Chatbot" target="_blank">
            <div class="settings-title">Chatbot Link</div>
            <div class="settings-desc">Open AI Chatbot in dashboard view.</div>
          </a>
          <a class="settings-card" href="mailto:support@example.com?subject=CiscoIQ%20Report%20Automation%20Help">
            <div class="settings-title">Help / Support</div>
            <div class="settings-desc">Contact support for upload or dashboard issues.</div>
          </a>
          <a class="settings-card" href="https://docs.streamlit.io/" target="_blank">
            <div class="settings-title">Reference Docs</div>
            <div class="settings-desc">Open Streamlit reference documentation.</div>
          </a>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", type="primary"):
            st.session_state.team_authenticated = False
            st.session_state.upload_left_page = "Track Uploads"
            st.query_params["page"] = "login"
            st.rerun()
        return True

    return False


def render_dashboard_header() -> None:
    st.markdown(
        f"""
<div class="top-nav">
  <div class="brand">
    <div class="brand-icon">📈</div>
    <div>
    </div>
  </div>
  <div class="nav-time">Dashboard View<br/>Last Updated</div>
</div>
""",
        unsafe_allow_html=True,
    )





def dashboard_view_tabs() -> str:
    current_tab = params.get("tab", "") or st.session_state.get("dashboard_tab", "Overview")
    if "nav_target" in st.session_state:
        current_tab = st.session_state.pop("nav_target")

    valid_tabs = ["Overview", "Track Comparison", "Detailed Report", "Chatbot"]
    legacy_tabs = {"Drilldown": "Detailed Report", "Compare": "Track Comparison", "Reports": "Overview", "Trends": "Overview"}
    current_tab = legacy_tabs.get(current_tab, current_tab)
    if current_tab not in valid_tabs:
        current_tab = "Overview"

    st.session_state["dashboard_tab"] = current_tab
    current_run_id = params.get("run_id", "") or st.session_state.get("run_id", "")

    tabs = [
        ("Overview", "◈  Overview"),
        ("Track Comparison", "▥  Track Comparison"),
        ("Detailed Report", "▣  Detailed Report"),
        ("Chatbot", "●  AI Chatbot"),
    ]
    tab_cols = st.columns([1.05, 1.42, 1.32, 1.15], gap="small")
    for col, (tab_value, tab_label) in zip(tab_cols, tabs):
        if col.button(
            tab_label,
            key=f"dashboard_view_{sanitize_token(tab_value)}",
            type="primary" if current_tab == tab_value else "secondary",
            use_container_width=True,
        ):
            st.session_state["dashboard_tab"] = tab_value
            if current_run_id:
                st.query_params["view"] = "dashboard"
                st.query_params["run_id"] = current_run_id
                st.query_params["tab"] = tab_value

    if current_run_id:
        if (
            st.query_params.get("view", "") != "dashboard"
            or st.query_params.get("run_id", "") != current_run_id
            or st.query_params.get("tab", "") != current_tab
        ):
            st.query_params["view"] = "dashboard"
            st.query_params["run_id"] = current_run_id
            st.query_params["tab"] = current_tab

    return current_tab


def kpi_cards(df: pd.DataFrame, previous_df: pd.DataFrame | None = None, title: str = "AGGREGATED PERFORMANCE OVERVIEW METRICS", compact: bool = False, show_health: bool = True) -> None:
    s = summarize_run(df)
    sla_fail = round(100 - s["sla_compliance"], 2) if s["transactions"] else 0

    previous = summarize_run(previous_df) if previous_df is not None else None

    def delta_html(current: float, previous_value: float | None, suffix: str = "", lower_is_better: bool = False) -> str:
        if previous_value is None:
            return ""
        diff = round(float(current or 0) - float(previous_value or 0), 2)
        good = diff <= 0 if lower_is_better else diff >= 0
        arrow = "▲" if diff >= 0 else "▼"
        css_class = "good" if good else "bad"
        sign = "+" if diff > 0 else ""
        return f'<div class="agg-delta {css_class}">{arrow} {sign}{diff:g}{suffix} vs prev</div>'

    previous_sla_fail = round(100 - previous["sla_compliance"], 2) if previous else None
    health_delta = delta_html(s["performance_score"], previous["performance_score"] if previous else None) if show_health else ""
    sla_pass_delta = delta_html(s["sla_compliance"], previous["sla_compliance"] if previous else None, "%")
    sla_fail_delta = delta_html(sla_fail, previous_sla_fail, "%", lower_is_better=True)
    apis_delta = delta_html(s["transactions"], previous["transactions"] if previous else None)
    samples_delta = delta_html(s["samples"], previous["samples"] if previous else None)
    errors_delta = delta_html(s["errors"], previous["errors"] if previous else None, lower_is_better=True)

    if show_health and not health_delta:
        health_delta = """
        <svg class="agg-spark" viewBox="0 0 130 28" xmlns="http://www.w3.org/2000/svg">
          <polyline points="2,20 16,19 29,20 42,17 55,18 68,11 81,16 94,18 107,9 124,14 129,8"
            fill="none" stroke="#22a447" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
    if not sla_pass_delta:
        sla_pass_delta = '<div class="agg-delta good">▲ APIs meeting SLA</div>'
    if not sla_fail_delta:
        sla_fail_delta = '<div class="agg-delta bad">▼ APIs breaching SLA</div>'
    if not apis_delta:
        apis_delta = '<div class="agg-delta good">▲ Compared APIs</div>'
    if not samples_delta:
        samples_delta = '<div class="agg-delta good">▲ Executed samples</div>'
    if not errors_delta:
        errors_delta = '<div class="agg-delta bad">▼ Failed samples</div>'

    extra_cards = "" if compact else f"""
    <div class="agg-kpi">
      <div class="agg-icon" style="background:linear-gradient(135deg,#2563eb,#3152d9);">♜</div>
      <div>
        <div class="agg-label">Total APIs</div>
        <div class="agg-value">{s['transactions']:,}</div>
        {apis_delta}
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:linear-gradient(135deg,#7c3aed,#a855f7);">◉</div>
      <div>
        <div class="agg-label">Total Samples</div>
        <div class="agg-value">{s['samples']:,}</div>
        {samples_delta}
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:#dc2626;">⚠</div>
      <div>
        <div class="agg-label">Total Errors</div>
        <div class="agg-value">{s['errors']:,}</div>
        {errors_delta}
      </div>
    </div>
    """

    columns = (3 if compact else 6) if show_health else (2 if compact else 5)
    component_height = 205 if not compact else 190

    health_card = "" if not show_health else f"""
    <div class="agg-kpi">
      <div class="agg-icon" style="background:linear-gradient(135deg,#2563eb,#4f46e5);">🛡</div>
      <div>
        <div class="agg-label">Health Score</div>
        <div class="agg-value">{s['performance_score']}<span class="agg-suffix">/100</span></div>
        {health_delta}
      </div>
    </div>
    """

    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: transparent;
}}
.agg-summary-card {{
    background:#ffffff;
    border:1px solid #dbe4f0;
    border-radius:14px;
    padding:0 0 12px 0;
    box-shadow:0 8px 22px rgba(15,23,42,.045);
}}
.agg-summary-title {{
    display:inline-block;
    background:linear-gradient(90deg,#2333a3,#3152d9);
    color:#ffffff;
    padding:9px 18px;
    border-radius:12px 12px 12px 0;
    font-size:15px;
    font-weight:900;
    letter-spacing:.2px;
    margin:0 0 8px 0;
}}
.agg-kpi-row {{
    display:grid;
    grid-template-columns: repeat({columns}, 1fr);
    gap:0;
    padding:10px 16px 0 16px;
}}
.agg-kpi {{
    display:flex;
    align-items:center;
    gap:14px;
    min-height:130px;
    padding:10px 18px;
    border-right:1px solid #e5edf7;
}}
.agg-kpi:last-child {{
    border-right:none;
}}
.agg-icon {{
    width:44px;
    height:44px;
    border-radius:10px;
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:23px;
    font-weight:900;
    box-shadow:0 10px 20px rgba(15,23,42,.16);
    flex:0 0 44px;
}}
.agg-label {{
    font-size:13px;
    font-weight:850;
    color:#111827;
    margin-bottom:8px;
}}
.agg-value {{
    font-size:28px;
    font-weight:900;
    color:#111827;
    line-height:1.0;
    letter-spacing:-.4px;
}}
.agg-suffix {{
    font-size:13px;
    color:#667085;
    font-weight:650;
    margin-left:5px;
}}
.agg-delta {{
    font-size:13px;
    margin-top:10px;
    color:#667085;
    font-weight:700;
    line-height:1.25;
    white-space:normal;
}}
.agg-delta.good {{ color:#15803d; }}
.agg-delta.bad {{ color:#ef4444; }}
.agg-spark {{
    width:132px;
    height:24px;
    margin-top:9px;
}}
@media(max-width:1100px){{
  .agg-kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  .agg-kpi:nth-child(2n){{border-right:none;}}
}}
</style>
</head>
<body>
<div class="agg-summary-card">
  <div class="agg-summary-title">{title}</div>
  <div class="agg-kpi-row">

    {health_card}

    <div class="agg-kpi">
      <div class="agg-icon" style="background:#16843a;">✓</div>
      <div>
        <div class="agg-label">SLA Pass %</div>
        <div class="agg-value">{s['sla_compliance']}%</div>
        {sla_pass_delta}
      </div>
    </div>

    <div class="agg-kpi">
      <div class="agg-icon" style="background:#dc2626;">×</div>
      <div>
        <div class="agg-label">SLA Fail %</div>
        <div class="agg-value">{sla_fail}%</div>
        {sla_fail_delta}
      </div>
    </div>

    {extra_cards}

  </div>
</div>
</body>
</html>
"""
    components.html(html, height=component_height, scrolling=False)


def build_run_summary_table(run_frames: List[Dict[str, pd.DataFrame]], include_health: bool = True) -> pd.DataFrame:
    rows = []
    baseline = None
    for index, frames in enumerate(run_frames):
        row = summarize_run(frames["APIs"])
        if baseline is None:
            baseline = row.copy()
        sla_fail = round(100 - row["sla_compliance"], 2)
        row_data = {
            "Result": run_display_label(frames),
            "Region": frames.get("Region", region_from_frames(frames)),
            "SLA Pass %": row["sla_compliance"],
            "SLA Fail %": sla_fail,
        }
        if include_health:
            row_data["Health Score"] = row["performance_score"]
        rows.append(row_data)
    return pd.DataFrame(rows)


def render_aggregated_or_comparison_summary(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    active_track = canonical_track_name(st.session_state.get("active_track") or params.get("track", "") or TRACK_API)
    hide_health = active_track == TRACK_UI
    scoped_frames = run_frames
    if active_track == TRACK_UI:
        scoped_frames = []
        for frames in run_frames:
            f = dict(frames)
            apis_df = frames.get("APIs", pd.DataFrame())
            f["APIs"] = apply_ui_speed_index_sla(apis_df)
            scoped_frames.append(f)

    if len(run_frames) <= 1:
        kpi_cards(combined_df(scoped_frames), compact=True, show_health=not hide_health)
        return

    current_df = scoped_frames[-1]["APIs"]
    previous_df = scoped_frames[-2]["APIs"] if len(scoped_frames) > 1 else None
    kpi_cards(current_df, previous_df=previous_df, title="AGGREGATED PERFORMANCE OVERVIEW METRICS", compact=True, show_health=not hide_health)

    summary = build_run_summary_table(scoped_frames, include_health=not hide_health)
    st.markdown('<div class="panel"><div class="panel-title">COMPARISON SUMMARY</div>', unsafe_allow_html=True)
    st.dataframe(summary, use_container_width=True, hide_index=True, height=min(245, 72 + 42 * len(summary)))
    st.markdown("</div>", unsafe_allow_html=True)


def sla_donut(df: pd.DataFrame):
    if "SLA Status" not in df.columns:
        fig = px.pie(values=[1], names=["N/A"], hole=0.62)
        return fig
    counts = df["SLA Status"].value_counts().reset_index()
    counts.columns = ["SLA Status", "Count"]
    counts = counts[counts["SLA Status"].isin(["PASS", "FAIL"])]
    if counts.empty:
        fig = px.pie(values=[1], names=["N/A"], hole=0.62)
        fig.update_layout(height=280, margin=dict(l=5, r=5, t=15, b=5))
        return fig
    fig = px.pie(
        counts,
        names="SLA Status",
        values="Count",
        hole=0.62,
        color="SLA Status",
        color_discrete_map={"PASS": "#2ca02c", "FAIL": "#ef4444"},
    )
    s = summarize_run(df)
    fig.update_layout(
        height=280,
        margin=dict(l=5, r=5, t=15, b=5),
        legend=dict(orientation="v", yanchor="middle", y=.5, xanchor="left", x=.82),
        annotations=[dict(text=f"<b>{s['sla_compliance']}%</b><br>PASS", x=.39, y=.5, font_size=18, showarrow=False)],
    )
    return fig


def get_filtered_frames(run_frames: List[Dict[str, pd.DataFrame]], forced_region: str = "All", forced_track: str = "API") -> List[Dict[str, pd.DataFrame]]:
    def normalize_filter_date(value: str, label: str) -> str:
        parsed = extract_mmddyyyy_from_text(str(value or "")) or extract_mmddyyyy_from_text(str(label or ""))
        if parsed:
            return f"{parsed[:2]}-{parsed[2:4]}-{parsed[4:8]}"
        return "N/A"

    cache = st.session_state.setdefault("_dashboard_filter_meta_cache", {})
    labels_key = "|".join([str(frames.get("Label", "")) for frames in run_frames])
    active_program = st.session_state.get("active_program", PROGRAM_SAAS)
    meta_key = f"{st.session_state.get('run_id','')}::{active_program}::{forced_track}::{labels_key}"
    meta = cache.get(meta_key)
    if meta is None:
        rows = []
        for frames in run_frames:
            info = frames.get("Run_Info")
            info_row = info.iloc[0].to_dict() if info is not None and not info.empty else {}
            label = frames["Label"]
            inferred = infer_saved_report_info(label)
            region = frames.get("Region", region_from_frames(frames))
            if not region or region == "Unknown":
                region = inferred.get("region", "Unknown")

            inferred_date = normalize_filter_date(inferred.get("date", "N/A"), label)
            info_date = normalize_filter_date(info_row.get("Date", "N/A"), label)
            date = inferred_date if inferred_date != "N/A" else info_date

            duration = str(info_row.get("Duration", "N/A"))
            if not duration or duration == "N/A":
                duration = inferred.get("duration", "N/A")

            short_result = run_display_label(frames)
            rows.append({
                "Label": label,
                "Display": short_result,
                "Region": region,
                "Date": date,
                "Duration": duration,
                "Track": canonical_track_name(info_row.get("Track") or infer_program_track(label)[1]),
                "Application": str(info_row.get("Application", inferred.get("application", APP_NAME_TOKEN))),
                "Program": str(info_row.get("Program", inferred.get("program", PROGRAM_SAAS))),
                "Environment": str(info_row.get("Environment", inferred.get("env", "PROD"))),
                "Run ID": str(info_row.get("Run ID", inferred.get("run_id", "N/A"))),
                "Result Option": short_result,
            })
        meta = pd.DataFrame(rows)
        cache[meta_key] = meta

    if meta.empty:
        return run_frames

    normalized_forced_track = canonical_track_name(forced_track)
    meta = meta[meta["Track"].map(canonical_track_name) == normalized_forced_track].copy()
    if meta.empty:
        return []

    files = meta["Result Option"].astype(str).tolist()
    dedup = {}
    for i, name in enumerate(files):
        dedup[name] = dedup.get(name, 0) + 1
        if dedup[name] > 1:
            files[i] = f"{name} ({dedup[name]})"
    meta["Result Option"] = files

    dates = sorted(meta["Date"].astype(str).unique().tolist())
    regions = sorted(meta["Region"].astype(str).unique().tolist())

    file_options = [f"Compare Selected ({len(files)})"] + files
    date_options = [f"All Dates ({len(dates)})"] + dates
    region_options = [", ".join(regions) + f" ({len(regions)})"] + regions

    with st.container(border=True):
        st.markdown(
            """
<style>
.filter-card-title {
    color:#0f2b68;
    font-size:18px;
    font-weight:900;
    letter-spacing:.2px;
    margin-bottom:12px;
}
.filter-help {
    color:#667085;
    font-size:12px;
    margin:-4px 0 12px 0;
}
</style>
<div class="filter-card-title">DATA & FILTERS</div>
<div class="filter-help">Choose reports, test date and region, then apply.</div>
""",
            unsafe_allow_html=True,
        )

        scope_key = f"{st.session_state.get('run_id','')}::{active_program}::{forced_track}"
        scope_token = hashlib.md5(scope_key.encode("utf-8")).hexdigest()[:12]
        all_filters = st.session_state.setdefault("applied_dashboard_filters", {})
        current_filters = all_filters.get(scope_key, {
            "file": file_options[0],
            "date": date_options[0],
            "region": region_options[0],
        })

        if current_filters.get("file") not in file_options:
            current_filters["file"] = file_options[0]
        if current_filters.get("date") not in date_options:
            current_filters["date"] = date_options[0]
        if current_filters.get("region") not in region_options:
            current_filters["region"] = region_options[0]

        selected_file_choice = st.selectbox(
            "Result File",
            file_options,
            index=file_options.index(current_filters.get("file", file_options[0])),
            key=f"dashboard_filter_file_choice_{scope_token}",
        )
        selected_date_choice = st.selectbox(
            "Date",
            date_options,
            index=date_options.index(current_filters.get("date", date_options[0])),
            key=f"dashboard_filter_date_choice_{scope_token}",
        )
        selected_region_choice = st.selectbox(
            "Region",
            region_options,
            index=region_options.index(current_filters.get("region", region_options[0])),
            key=f"dashboard_filter_region_choice_{scope_token}",
        )

        apply_clicked = st.button("Apply Filters", type="primary", use_container_width=True, key=f"dashboard_apply_filters_{scope_token}")
        reset_clicked = st.button("Reset Filters", use_container_width=True, key=f"dashboard_reset_filters_{scope_token}")

        if reset_clicked:
            all_filters[scope_key] = {
                "file": file_options[0],
                "date": date_options[0],
                "region": region_options[0],
            }
            st.session_state["applied_dashboard_filters"] = all_filters
            st.rerun()
        if apply_clicked or scope_key not in all_filters:
            all_filters[scope_key] = {
                "file": selected_file_choice,
                "date": selected_date_choice,
                "region": selected_region_choice,
            }
            st.session_state["applied_dashboard_filters"] = all_filters

        active_filters = st.session_state.get("applied_dashboard_filters", {}).get(scope_key, {
            "file": file_options[0],
            "date": date_options[0],
            "region": region_options[0],
        })

    selected_files = files if active_filters.get("file") == file_options[0] else [active_filters.get("file")]
    selected_dates = dates if active_filters.get("date") == date_options[0] else [active_filters.get("date")]
    selected_regions = regions if active_filters.get("region") == region_options[0] else [active_filters.get("region")]
    if forced_region and forced_region != "All":
        selected_regions = [forced_region]

    if not selected_files or not selected_dates or not selected_regions:
        return []

    keep_labels = meta[
        meta["Result Option"].isin(selected_files)
        & meta["Date"].astype(str).isin(selected_dates)
        & meta["Region"].astype(str).isin(selected_regions)
    ]["Label"].tolist()
    return [frames for frames in run_frames if frames["Label"] in keep_labels]


def auto_insights(run_frames: List[Dict[str, pd.DataFrame]]) -> List[Tuple[str, str, str]]:
    df = combined_df(run_frames)
    s = summarize_run(df)
    tracks = cached_track_summary(df)
    result = []
    if len(run_frames) > 1:
        summary_rows = []
        for frames in run_frames:
            row = summarize_run(frames["APIs"])
            row["Region"] = frames.get("Region", region_from_frames(frames))
            summary_rows.append(row)
        summary = pd.DataFrame(summary_rows)
        best = summary.sort_values("sla_compliance", ascending=False).iloc[0]
        worst = summary.sort_values("error_rate", ascending=False).iloc[0]
        result.append(("✓", "#16a34a", f"{best['Region']} has best SLA compliance at {best['sla_compliance']}%."))
        result.append(("!", "#ef4444", f"{worst['Region']} has highest error rate at {worst['error_rate']}%."))
    if not tracks.empty:
        worst_track = tracks.iloc[0]
        result.append(("⚠", "#f59e0b", f"{worst_track['Feature']} has highest max latency at {worst_track['Max_Sec']}s."))
    result.append(("i", "#2563eb", f"Overall SLA compliance is {s['sla_compliance']}% with {s['errors']:,} errors."))
    return result[:5]




def dashboard_frames_cache_key(run_frames: List[Dict[str, pd.DataFrame]], extra: str = "") -> str:
    """Stable lightweight key for current dashboard data so tab clicks reuse cached calculations."""
    parts = [str(extra), str(st.session_state.get("run_id", ""))]
    for frames in run_frames or []:
        label = str(frames.get("Label", ""))
        apis = frames.get("APIs")
        shape = getattr(apis, "shape", ("", ""))
        parts.append(f"{label}:{shape}")
    return "|".join(parts)


def cached_combined_df(run_frames: List[Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    key = dashboard_frames_cache_key(run_frames, "combined_df")
    cache = st.session_state.setdefault("_dashboard_calc_cache", {})
    if key not in cache:
        cache[key] = combined_df(run_frames)
    return cache[key]


def cached_track_summary(df: pd.DataFrame) -> pd.DataFrame:
    key = f"track_summary:{st.session_state.get('run_id','')}:{getattr(df, 'shape', '')}:{','.join(map(str, df.columns[:6])) if not df.empty else 'empty'}"
    cache = st.session_state.setdefault("_dashboard_calc_cache", {})
    if key not in cache:
        cache[key] = track_summary(df)
    return cache[key]


def cached_track_comparison(run_frames: List[Dict[str, pd.DataFrame]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    key = dashboard_frames_cache_key(run_frames, "track_comparison")
    cache = st.session_state.setdefault("_dashboard_calc_cache", {})
    if key not in cache:
        cache[key] = build_dashboard_track_comparison(run_frames)
    return cache[key]


def cached_auto_insights(run_frames: List[Dict[str, pd.DataFrame]]) -> List[Tuple[str, str, str]]:
    key = dashboard_frames_cache_key(run_frames, "auto_insights")
    cache = st.session_state.setdefault("_dashboard_calc_cache", {})
    if key not in cache:
        cache[key] = auto_insights(run_frames)
    return cache[key]


def response_bucket(value: float, is_askai: bool) -> str:
    value = float(value or 0)
    if value <= 3:
        return "0-3s %"
    if value <= 4:
        return "3-4s %"
    if value <= 5:
        return "4-5s %"
    return ">6s %"


def metric_bucket_summary(df: pd.DataFrame, track: str, metric: str, is_askai: bool) -> List[float]:
    col_map = {
        "Avg": "Avg ResTime in sec",
        "Min": "Min ResTime in sec",
        "Max": "MaxRes Time in sec",
    }
    col = col_map[metric]
    rows = df[df["Feature"].astype(str) == str(track)].copy()
    if rows.empty or col not in rows.columns:
        return [0, 0, 0, 0]

    bucket_names = ["0-3s %", "3-4s %", "4-5s %", ">6s %"]
    counts = dict.fromkeys(bucket_names, 0)
    values = pd.to_numeric(rows[col], errors="coerce").fillna(0)
    for value in values:
        counts[response_bucket(float(value), is_askai)] += 1
    total = len(values) if len(values) else 1
    percentages = [round(counts[name] / total * 100, 2) for name in bucket_names]
    return percentages + [round(float(values.max()), 2)]



def build_dashboard_track_comparison(run_frames: List[Dict[str, pd.DataFrame]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not run_frames:
        return pd.DataFrame(), pd.DataFrame()

    metric_source_frames = []
    for frames in run_frames:
        info = frames.get("Run_Info")
        info_row = info.iloc[0].to_dict() if info is not None and not info.empty else {}
        frame_track = canonical_track_name(info_row.get("Track") or infer_program_track(frames.get("Label", ""))[1])
        metric_key = "Scenario" if frame_track == TRACK_UI else "Feature"
        metric_source_frames.append((frames, metric_key))

    all_tracks = sorted(
        set().union(*[
            set(frames["APIs"].get(metric_key, pd.Series(dtype=str)).dropna().astype(str))
            for frames, metric_key in metric_source_frames
        ])
    )
    all_tracks = [
        t for t in all_tracks
        if t and t.lower() != "total"
        and "select customer" not in t.lower()
        and not is_excluded_ui_metric(t)
    ]

    other_tracks = all_tracks

    def metric_bucket_summary_for_rows(rows: pd.DataFrame, metric: str) -> List[float]:
        col_map = {
            "Avg": "Avg ResTime in sec",
            "Min": "Min ResTime in sec",
            "Max": "MaxRes Time in sec",
        }
        col = col_map[metric]
        bucket_names = ["0-3s %", "3-4s %", "4-5s %", ">6s %"]
        if rows.empty or col not in rows.columns:
            return [0, 0, 0, 0, 0]

        counts = dict.fromkeys(bucket_names, 0)
        values = pd.to_numeric(rows[col], errors="coerce").fillna(0)
        for value in values:
            bucket = response_bucket(float(value), False)
            counts[bucket] = counts.get(bucket, 0) + 1
        total = len(values) if len(values) else 1
        percentages = [round(counts[name] / total * 100, 2) for name in bucket_names]
        return percentages + [round(float(values.max()), 2)]

    def build_section(tracks: List[str]) -> pd.DataFrame:
        rows = []
        bucket_names = ["0-3s %", "3-4s %", "4-5s %", ">6s %"]
        row_targets = ["Total"] + tracks

        for target in row_targets:
            first_target_row = True
            for frames, metric_key in metric_source_frames:
                api_df = frames["APIs"].copy()
                axis_col = metric_key if metric_key in api_df.columns else "Feature"
                if target == "Total":
                    api_rows = api_df[api_df[axis_col].astype(str).isin(tracks)] if tracks else api_df
                else:
                    api_rows = api_df[api_df[axis_col].astype(str) == str(target)]

                display_label = run_display_label(frames)
                for metric_index, metric in enumerate(["Min", "Max"]):
                    values = metric_bucket_summary_for_rows(api_rows, metric)
                    row = {
                        "_TrackKey": target,
                        "Track": target if first_target_row else "",
                        "Result": display_label if metric_index == 0 else "",
                        "Metric": metric,
                    }
                    for name, value in zip(bucket_names + ["Max s"], values):
                        row[name] = value
                    rows.append(row)
                    first_target_row = False

        return pd.DataFrame(rows)

    return pd.DataFrame(), build_section(other_tracks)


def display_track_comparison_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=["_TrackKey"], errors="ignore")


def format_compare_cell(value: object) -> str:
    try:
        number = float(value)
        if pd.isna(number):
            return "-"
        return f"{number:.2f}".rstrip("0").rstrip(".")
    except Exception:
        text = str(value).strip()
        return text if text else "-"


def display_bucket_label(label: str) -> str:
    return str(label).replace("sec", "s").replace(" ", "")


def track_comparison_matrix_html(data: pd.DataFrame) -> str:
    if data.empty:
        return ""

    metric_order = ["Min", "Max"]
    bucket_cols = ["0-3s %", "3-4s %", "4-5s %", ">6s %"]

    detail = data[data["_TrackKey"] != "Total"].copy()
    if detail.empty:
        return ""

    results: List[str] = []
    tracks: List[str] = []
    seen_results = set()
    seen_tracks = set()
    row_lookup: Dict[Tuple[str, str, str], pd.Series] = {}
    last_result_by_track: Dict[str, str] = {}

    for _, row in detail.iterrows():
        track = str(row.get("_TrackKey", "")).strip()
        if not track:
            continue
        if track not in seen_tracks:
            tracks.append(track)
            seen_tracks.add(track)

        result = str(row.get("Result", "")).strip()
        if result:
            last_result_by_track[track] = result
            if result not in seen_results:
                results.append(result)
                seen_results.add(result)
        else:
            result = last_result_by_track.get(track, "")

        metric = str(row.get("Metric", "")).strip()
        if result and metric in metric_order:
            row_lookup[(track, result, metric)] = row

    if not results or not tracks:
        return ""

    html_rows: List[str] = []
    html_rows.append('<div class="track-compare-table-wrap">')
    html_rows.append('<table class="track-compare-table">')

    html_rows.append("<thead>")
    header_top = [
        '<tr>',
        '<th class="fixed-col" rowspan="2">Track</th>',
        '<th class="metric-col" rowspan="2">Metric</th>',
    ]
    for result in results:
        header_top.append(f'<th class="result-group" colspan="{len(bucket_cols) + 1}">{html.escape(result)}</th>')
    header_top.append("</tr>")
    html_rows.append("".join(header_top))

    header_second = ["<tr>"]
    for _ in results:
        for bucket in bucket_cols:
            header_second.append(f"<th>{html.escape(display_bucket_label(bucket))}</th>")
        header_second.append('<th class="max-header">Max s</th>')
    header_second.append("</tr>")
    html_rows.append("".join(header_second))
    html_rows.append("</thead>")

    html_rows.append("<tbody>")
    for track in tracks:
        for metric_index, metric in enumerate(metric_order):
            row_parts = ["<tr>"]
            if metric_index == 0:
                row_parts.append(f'<td class="track-name" rowspan="{len(metric_order)}">{html.escape(track)}</td>')
            row_parts.append(f'<td class="metric-name">{html.escape(metric)}</td>')

            for result in results:
                row = row_lookup.get((track, result, metric))
                for bucket in bucket_cols:
                    value = row.get(bucket, "-") if row is not None else "-"
                    row_parts.append(f'<td>{format_compare_cell(value)}</td>')
                max_value = row.get("Max s", "-") if row is not None else "-"
                row_parts.append(f'<td class="max-col">{format_compare_cell(max_value)}</td>')

            row_parts.append("</tr>")
            html_rows.append("".join(row_parts))
    html_rows.append("</tbody>")
    html_rows.append("</table>")
    html_rows.append("</div>")
    return "".join(html_rows)


def render_track_comparison_dashboard(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    askai_df, other_df = cached_track_comparison(run_frames)

    def render_section(title: str, data: pd.DataFrame, height: int) -> None:
        if data.empty:
            return
        with st.container(border=True):
            st.markdown(f'<div class="dashboard-subtitle">{title}</div>', unsafe_allow_html=True)
            total = data[data["_TrackKey"] == "Total"].copy()
            detail = data[data["_TrackKey"] != "Total"].copy()
            if not total.empty:
                st.caption("Total response distribution by uploaded result. Percent columns show APIs inside each response bucket.")
                st.dataframe(display_track_comparison_df(total), use_container_width=True, hide_index=True, height=min(260, 78 + 36 * len(total)))
            if not detail.empty:
                st.caption("Track-level breakdown using Min and Max response metrics.")
                st.dataframe(display_track_comparison_df(detail), use_container_width=True, hide_index=True, height=height)

    if askai_df.empty and other_df.empty:
        return

    st.markdown('<div class="panel-title" style="margin-top:12px;">TRACK COMPARISON DASHBOARD</div>', unsafe_allow_html=True)
    render_section("Track Comparison", other_df, 380)


def render_compare_tab(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    st.markdown('<div class="panel"><div class="panel-title" style="font-size:18px;">TRACK COMPARISON <span class="tag">Grouped by result</span></div>', unsafe_allow_html=True)

    st.markdown(
        """
<style>
.track-compare-table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #d3dbe8;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fbff 0%, #f2f6fc 100%);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}
.track-compare-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  color: #111827;
}
.track-compare-table th,
.track-compare-table td {
  border: 1px solid #cfd8e3;
  padding: 7px 9px;
  text-align: right;
  background: #f8fafc;
  white-space: nowrap;
}
.track-compare-table th.fixed-col,
.track-compare-table td.track-name {
  text-align: left;
  min-width: 220px;
}
.track-compare-table th.metric-col,
.track-compare-table td.metric-name {
  text-align: left;
  min-width: 70px;
}
.track-compare-table th.result-group {
  background: linear-gradient(180deg, #194b9b 0%, #103b81 100%);
  text-align: center;
  font-size: 12px;
  font-weight: 900;
  color: #ffffff;
  letter-spacing: 0.2px;
}
.track-compare-table thead tr:nth-child(2) th {
  background: #eaf0f7;
  font-weight: 800;
  font-size: 11px;
  color: #344256;
}
.track-compare-table th.max-header,
.track-compare-table td.max-col {
  background: #ffe1e5;
  color: #a0141a;
  font-weight: 900;
}
.track-compare-table td.track-name {
  font-size: 14px;
  font-weight: 700;
  background: #eef3f9;
}
.track-compare-table td.metric-name {
  font-size: 13px;
  font-weight: 700;
  background: #f1f5fa;
}
.track-compare-table td {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.05;
}
.track-compare-table tbody tr:nth-child(even) td {
  background: #f4f7fb;
}
@media (max-width: 1200px) {
  .track-compare-table th.result-group,
  .track-compare-table td.track-name,
  .track-compare-table td.metric-name,
  .track-compare-table td {
    font-size: 12px;
  }
  .track-compare-table thead tr:nth-child(2) th {
    font-size: 10px;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )

    askai_df, other_df = cached_track_comparison(run_frames)

    if not other_df.empty:
        other_html = track_comparison_matrix_html(other_df)
        if other_html:
            st.markdown(other_html, unsafe_allow_html=True)
        else:
            st.info("No comparison rows found.")
    else:
        st.info("No comparison tracks found.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_trends_tab(run_frames: List[Dict[str, pd.DataFrame]], compact: bool = False, show_table: bool = True) -> None:
    if not compact:
        st.markdown('<div class="panel"><div class="panel-title">TRENDS ACROSS RESULTS</div>', unsafe_allow_html=True)
    rows = []
    for frames in run_frames:
        row = summarize_run(frames["APIs"])
        row["Run"] = frames["Label"]
        row["Region"] = frames.get("Region", region_from_frames(frames))
        rows.append(row)
    summary = pd.DataFrame(rows)
    if len(summary) > 0:
        display_summary = summary.copy()
        display_summary["Result"] = [run_display_label(frames) for frames in run_frames]
        fig1 = px.line(display_summary, x="Result", y=["avg_sec", "min_sec", "max_sec"], markers=True, title="Response Trend")
        fig1.update_layout(height=330 if compact else 420, xaxis_title="", yaxis_title="Seconds", margin=dict(l=8, r=8, t=40, b=95), legend_title="Metric")
        st.plotly_chart(fig1, use_container_width=True)

        if show_table:
            table = display_summary.rename(columns={
                "avg_sec": "Avg Sec",
                "min_sec": "Min Sec",
                "max_sec": "Max Sec",
                "success_rate": "Success %",
                "error_rate": "Error %",
                "sla_compliance": "SLA Pass %",
                "performance_score": "Health Score",
                "errors": "Errors",
                "samples": "Samples",
            })
            needed_cols = ["Result", "Region", "Avg Sec", "Min Sec", "Max Sec"]
            display_table = table[safe_cols(table, needed_cols)].copy()
            if compact:
                st.markdown(
                    """
<style>
.trends-table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #d3dbe8;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fbff 0%, #f2f6fc 100%);
  box-shadow: 0 10px 28px rgba(15,23,42,.06);
  margin-top: 6px;
}
.trends-table {
  width: 100%;
  border-collapse: collapse;
  color: #111827;
}
.trends-table th,
.trends-table td {
  border: 1px solid #cfd8e3;
  padding: 8px 10px;
  white-space: nowrap;
}
.trends-table th {
  background: #eaf0f7;
  font-size: 11px;
  font-weight: 800;
  color: #344256;
  text-align: left;
}
.trends-table td {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 650;
  text-align: right;
}
.trends-table td.result-col,
.trends-table td.region-col {
  text-align: left;
  font-weight: 700;
}
.trends-table td.success-col,
.trends-table td.sla-col,
.trends-table td.health-col {
  background: #edf8f0;
  color: #166534;
}
.trends-table td.error-col {
  background: #ffeef0;
  color: #9f1239;
}
.trends-table tbody tr:nth-child(even) td {
  background: #f4f7fb;
}
@media (max-width: 1200px) {
  .trends-table th { font-size: 10px; }
  .trends-table td { font-size: 11px; }
}
</style>
""",
                    unsafe_allow_html=True,
                )

                column_classes = {
                    "Result": "result-col",
                    "Region": "region-col",
                    "Success %": "success-col",
                    "Error %": "error-col",
                    "SLA Pass %": "sla-col",
                    "Health Score": "health-col",
                }
                header_html = "".join([f"<th>{html.escape(col)}</th>" for col in display_table.columns])
                body_rows = []
                for _, row in display_table.iterrows():
                    cells = []
                    for col in display_table.columns:
                        cls = column_classes.get(col, "")
                        value = format_compare_cell(row.get(col, ""))
                        cells.append(f'<td class="{cls}">{html.escape(value)}</td>')
                    body_rows.append(f"<tr>{''.join(cells)}</tr>")
                st.markdown(
                    f'<div class="trends-table-wrap"><table class="trends-table"><thead><tr>{header_html}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.dataframe(display_table, use_container_width=True, hide_index=True, height=min(520, 78 + 36 * len(table)))
    if not compact:
        st.markdown("</div>", unsafe_allow_html=True)


def render_detailed_report_tab(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    df = combined_df(run_frames)
    st.markdown('<div class="panel"><div class="panel-title">DETAILED REPORT</div>', unsafe_allow_html=True)
    if st.session_state.get("active_track") == TRACK_UI:
        df = apply_ui_speed_index_sla(df)
        if df.empty:
            st.info("No UI metrics available.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        raw_detail = build_ui_raw_detail_df(run_frames)
        speed_rows_count = 0
        speed_pass = 0.0
        if not raw_detail.empty:
            speed_col = pick_ui_speed_index_column(raw_detail)
            speed_vals = pd.to_numeric(raw_detail.get(speed_col, pd.Series(dtype=float)), errors="coerce").dropna() if speed_col else pd.Series(dtype=float)
            if not speed_vals.empty:
                speed_rows_count = int(len(speed_vals))
                speed_pass = round(float((speed_vals <= 3.0).mean() * 100), 2)

        c1, c2, c3 = st.columns(3)
        c1.metric("Speed Index Rows", f"{speed_rows_count:,}")
        c2.metric("Speed Index SLA", "< 3s")
        c3.metric("Speed Index Pass %", f"{speed_pass:.2f}%")

        if raw_detail.empty:
            st.info("No raw UI CSV rows available for detailed view.")
        else:
            st.dataframe(raw_detail, use_container_width=True, hide_index=True, height=min(760, 78 + 28 * len(raw_detail)))
        st.markdown("</div>", unsafe_allow_html=True)
        return

    c1, c2, c3 = st.columns(3)
    tracks = sorted(df["Feature"].dropna().astype(str).unique().tolist())
    selected_tracks = c1.multiselect("Track", tracks, default=tracks[: min(10, len(tracks))])
    selected_status = c2.multiselect("SLA Status", ["PASS", "FAIL"], default=["PASS", "FAIL"])
    sort_col = c3.selectbox("Sort by", ["Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec", "errorCount", "sampleCount"])
    filtered = df[df["Feature"].isin(selected_tracks) & df["SLA Status"].isin(selected_status)].sort_values(sort_col, ascending=False)
    st.dataframe(filtered[standard_api_cols(filtered)], use_container_width=True, hide_index=True, height=650)
    st.markdown("</div>", unsafe_allow_html=True)


def goto_tab_button(label: str, tab_name: str, key: str) -> None:
    if st.button(label, key=key):
        st.session_state["nav_target"] = tab_name
        st.session_state["dashboard_tab"] = tab_name



def render_executive_dashboard(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    # Fast in-app navigation with screenshot-like layout.
    current_run_id = params.get("run_id", "") or st.session_state.get("run_id", "")
    selected_tab = st.session_state.get("dashboard_tab") or params.get("tab", "") or "Overview"
    legacy_tabs = {"Drilldown": "Detailed Report", "Compare": "Track Comparison", "Reports": "Overview", "Trends": "Overview"}
    selected_tab = legacy_tabs.get(selected_tab, selected_tab)
    if selected_tab not in ["Overview", "Track Comparison", "Detailed Report", "Chatbot"]:
        selected_tab = "Overview"
    st.session_state["dashboard_tab"] = selected_tab

    active_program = st.session_state.get("active_program") or params.get("program", "") or PROGRAM_SAAS
    program_values = [PROGRAM_SAAS, "Cisco IQ Onprem - Assets", "Cisco IQ Onprem - Risk App", "CX AI Assistant", "AI Framework"]
    if active_program not in program_values:
        active_program = PROGRAM_SAAS
    st.session_state["active_program"] = active_program

    active_track = st.session_state.get("active_track") or params.get("track", "") or "API"
    active_track = canonical_track_name(active_track)
    track_values = ["API", "UI", "Cloud Assist Connector", "Customer Inventory Benchmarking"]
    if active_track not in track_values:
        active_track = "API"

    available_tracks: List[str] = []
    for frames in run_frames:
        info = frames.get("Run_Info")
        info_row = info.iloc[0].to_dict() if info is not None and not info.empty else {}
        track_name = canonical_track_name(info_row.get("Track") or infer_program_track(frames.get("Label", ""))[1])
        if track_name in track_values and track_name not in available_tracks:
            available_tracks.append(track_name)

    st.session_state["active_track"] = active_track

    programs_html = [
        ("🎧", "Cisco IQ SaaS Support Services", PROGRAM_SAAS),
        ("▧", "Cisco IQ Onprem - Assets", "Cisco IQ Onprem - Assets"),
        ("🛡", "Cisco IQ Onprem - Risk App", "Cisco IQ Onprem - Risk App"),
        ("✣", "CX AI Assistant", "CX AI Assistant"),
        ("🤖", "AI Framework", "AI Framework"),
    ]
    tracks_html = ["API", "UI", "Cloud Assist Connector", "Customer Inventory Benchmarking"]
    tabs_html = [
        ("Overview", "◈ Overview"),
        ("Track Comparison", "▥ Track Comparison"),
        ("Detailed Report", "▣ Detailed Report"),
        ("Chatbot", "● AI Chatbot"),
    ]

    nav_changed = False
    st.markdown('<div class="exact-nav-anchor"></div>', unsafe_allow_html=True)
    nav_left, nav_right = st.columns([1.05, 3.3], gap="small")
    with nav_left:
        st.markdown('<div class="exact-label white">Programs</div>', unsafe_allow_html=True)
        for icon, label, value in programs_html:
            if st.button(
                f"{icon}  {label}",
                key=f"prog_fast_{sanitize_token(value)}",
                type="primary" if active_program == value else "secondary",
                use_container_width=True,
            ):
                st.session_state["active_program"] = value
                st.session_state["active_track"] = TRACK_API
                st.session_state["dashboard_tab"] = "Overview"
                nav_changed = True

    with nav_right:
        st.markdown('<div class="exact-label">Program Tracks</div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.columns([.58, .68, 1.55, 1.95], gap="small")
        for col, value in zip([t1, t2, t3, t4], tracks_html):
            if col.button(
                value,
                key=f"trk_fast_{sanitize_token(value)}",
                type="primary" if active_track == value else "secondary",
                use_container_width=True,
            ):
                st.session_state["active_track"] = value
                st.session_state["dashboard_tab"] = "Overview"
                nav_changed = True

        st.markdown('<div class="exact-label" style="margin-top:8px;">Dashboard Views</div>', unsafe_allow_html=True)
        tab_cols = st.columns([1.05, 1.42, 1.32, 1.15][:len(tabs_html)], gap="small")
        for col, (value, label) in zip(tab_cols, tabs_html):
            if col.button(
                label,
                key=f"tab_fast_{sanitize_token(value)}",
                type="primary" if selected_tab == value else "secondary",
                use_container_width=True,
            ):
                st.session_state["dashboard_tab"] = value
                nav_changed = True


    if nav_changed:
        if current_run_id:
            st.query_params["view"] = "dashboard"
            st.query_params["run_id"] = current_run_id
            st.query_params["program"] = st.session_state.get("active_program", PROGRAM_SAAS)
            st.query_params["track"] = st.session_state.get("active_track", TRACK_API)
            st.query_params["tab"] = st.session_state.get("dashboard_tab", "Overview")
        st.rerun()

    selected_tab = st.session_state.get("dashboard_tab", selected_tab)
    active_program = st.session_state.get("active_program", active_program)
    active_track = st.session_state.get("active_track", active_track)

    if active_program != PROGRAM_SAAS:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Coming Soon</div>', unsafe_allow_html=True)
            st.info(f"{active_program} is planned for Q4FY26. Dashboard enablement is in upcoming release windows.")
        return

    region_focus = "All"

    main_col, side_col = st.columns([4.35, .95], gap="medium")

    with side_col:
        selected_frames = get_filtered_frames(run_frames, forced_region=region_focus, forced_track=active_track)
        insights = cached_auto_insights(selected_frames)
        st.markdown('<div class="side-card"><div class="panel-title">REPORT ACTIONS</div>', unsafe_allow_html=True)
        if st.session_state.get("excel_bytes"):
            st.download_button(
                "Download Excel Report",
                data=st.session_state.excel_bytes,
                file_name=st.session_state.report_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="side_panel_excel_download",
                use_container_width=True,
            )
        else:
            st.info("Excel report is not available in this dashboard session.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="side-card"><div class="panel-title">INSIGHTS</div>', unsafe_allow_html=True)
        for icon, color, text in insights:
            st.markdown(f'<div class="insight-item"><div class="dot" style="background:{color};">{icon}</div><div>{text}</div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        try:
            dashboard_url = st.secrets.get("DASHBOARD_URL", "")
        except Exception:
            dashboard_url = ""
        if dashboard_url:
            st.markdown(f'<a class="primary-pill" href="{dashboard_url}?view=dashboard&tab=Overview" target="_self" style="width:100%;text-align:center;">Open Dashboard in New Tab ↗</a>', unsafe_allow_html=True)

    with main_col:
        if not selected_frames:
            st.warning("No reports match the selected filters. Please update Data & Filters.")
            return

        df = cached_combined_df(selected_frames)
        if active_track == TRACK_UI:
            df = apply_ui_speed_index_sla(df)

        if selected_tab == "Track Comparison":
            render_compare_tab(selected_frames)
            return

        if selected_tab == "Chatbot":
            st.markdown('<div class="panel"><div class="panel-title">AI CHATBOT</div>', unsafe_allow_html=True)
            render_chatbot(run_frames, key_suffix='tab')
            st.markdown("</div>", unsafe_allow_html=True)
            return
        if selected_tab == "Detailed Report":
            render_detailed_report_tab(selected_frames)
            return
        render_aggregated_or_comparison_summary(selected_frames)

        st.markdown('<div class="grid-3">', unsafe_allow_html=True)
        # Streamlit does not nest into raw grid well; use columns instead.
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns([1.35, 1], gap="medium")
        tracks = cached_track_summary(df)

        with c1:
            with st.container(border=True):
                st.markdown('<div class="panel-title">Response Time</div>', unsafe_allow_html=True)
                if not tracks.empty:
                    chart_df = tracks.head(8).sort_values("Max_Sec")
                    plot_df = chart_df[["Feature", "Avg_Sec", "Min_Sec", "Max_Sec"]].rename(
                        columns={
                            "Avg_Sec": "Avg",
                            "Min_Sec": "Min",
                            "Max_Sec": "Max",
                        }
                    )
                    long_df = plot_df.melt(id_vars="Feature", var_name="Metric", value_name="Seconds")
                    fig = px.bar(long_df, x="Feature", y="Seconds", color="Metric", barmode="group", text="Seconds")
                    fig.update_traces(texttemplate="%{text:.1f}s", textposition="outside")
                    fig.update_layout(height=330, margin=dict(l=8, r=10, t=5, b=95), xaxis_title="", yaxis_title="Seconds", legend_title="")
                    st.plotly_chart(fig, use_container_width=True)
                if active_track != TRACK_UI:
                    goto_tab_button('View all APIs →', 'Detailed Report', 'view_all_apis_btn')

        with c2:
            with st.container(border=True):
                st.markdown('<div class="panel-title">SLA Status</div>', unsafe_allow_html=True)
                st.plotly_chart(sla_donut(df), use_container_width=True)
                if active_track != TRACK_UI:
                    goto_tab_button('View SLA Breaches →', 'Detailed Report', 'view_sla_breaches_btn')

        with st.container(border=True):
            st.markdown('<div class="panel-title">SUMMARY</div>', unsafe_allow_html=True)
            render_overview_comparison_summary(selected_frames)
            goto_tab_button('Open Full Comparison →', 'Track Comparison', 'overview_full_compare_btn')

        with st.container(border=True):
            st.markdown('<div class="panel-title">TRENDS DASHBOARD</div>', unsafe_allow_html=True)
            render_trends_tab(selected_frames, compact=True, show_table=True)


def render_overview_comparison_summary(run_frames: List[Dict[str, pd.DataFrame]]) -> None:
    """Overview summary focused on UI Speed Index buckets."""

    def speed_index_cards(frames_list: List[Dict[str, pd.DataFrame]]) -> None:
        cards: List[Tuple[str, Dict[str, float]]] = []
        for frames in frames_list:
            raw_df = frames.get("UI_Raw")
            if raw_df is None or raw_df.empty:
                continue
            speed_col = pick_ui_speed_index_column(raw_df)
            if not speed_col:
                continue
            speed_values = pd.to_numeric(raw_df.get(speed_col, pd.Series(dtype=float)), errors="coerce").dropna()
            if speed_values.empty:
                continue
            percentages = ui_speed_index_bucket_percentages(speed_values)
            cards.append((run_display_label(frames), percentages))

        if not cards:
            st.info("No Speed Index rows found for summary.")
            return

        st.markdown('<div class="dashboard-subtitle">Speed Index Summary</div>', unsafe_allow_html=True)
        cols = st.columns(min(3, len(cards)), gap="medium")
        ordered_buckets = ["0-3s %", "3-4s %", "4-5s %", ">6s %"]
        for i, (label, bucket_values) in enumerate(cards):
            with cols[i % len(cols)]:
                parts = []
                for bucket in ordered_buckets:
                    value = float(bucket_values.get(bucket, 0) or 0)
                    parts.append(f'<div class="compare-bucket"><span>{display_bucket_label(bucket)}</span><b>{value:.2f}%</b></div>')
                st.markdown(f'''
<div class="overview-compare-card">
  <div class="overview-compare-title">{label}</div>
  <div class="overview-compare-grid">{"".join(parts)}</div>
</div>
''', unsafe_allow_html=True)

    st.markdown("""
<style>
.overview-compare-card {background: linear-gradient(180deg, #f8fbff 0%, #f2f6fc 100%); border: 1px solid #d3dbe8; border-radius: 14px; padding: 12px; box-shadow: 0 10px 28px rgba(15,23,42,.06); margin-bottom: 12px;}
.overview-compare-title {font-size: 12px; font-weight: 900; color: #ffffff; margin-bottom: 10px; background: linear-gradient(180deg, #194b9b 0%, #103b81 100%); border-radius: 10px; padding: 7px 10px; letter-spacing: .15px;}
.overview-compare-grid {display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px;}
.compare-bucket {background: #f8fafc; border: 1px solid #cfd8e3; border-radius: 10px; padding: 8px 6px; text-align: center;}
.compare-bucket span {display:block; font-size: 10px; color:#344256; font-weight:800;}
.compare-bucket b {display:block; margin-top: 4px; font-size: 13px; color:#111827;}
</style>
""", unsafe_allow_html=True)

    speed_index_cards(run_frames)



def standard_api_cols(df: pd.DataFrame) -> List[str]:
    return safe_cols(df, ["Feature", "Scenario", "Endpoint", "sampleCount", "errorCount", "errorPct", "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec", "SLA Sec", "SLA Status", "SLA Breach Sec"])


def extract_top_n(question: str, default: int = 10) -> int:
    match = re.search(r"\btop\s+(\d+)|\bfirst\s+(\d+)|\b(\d+)\s+(?:slow|error|fail|api|apis)", question.lower())
    nums = [g for g in match.groups() if g] if match else []
    return max(1, min(100, int(nums[0]))) if nums else default


def metric_col(question: str) -> str:
    q = question.lower()
    if "max" in q or "maximum" in q: return "MaxRes Time in sec"
    if "min" in q or "minimum" in q: return "Min ResTime in sec"
    return "Avg ResTime in sec"


def match_rows(df: pd.DataFrame, question: str) -> pd.DataFrame:
    if df.empty: return df
    q = question.lower()
    searchable_cols = safe_cols(df, ["Feature","Scenario","Endpoint","API","SLA Status","Track Type"])
    stop = {"show","give","tell","what","which","where","when","how","the","and","or","for","api","apis","track","tracks","report","details","data","list","top","bottom","is","are","was","were","in","of","to","me","with","on","by","about","please"}
    tokens = [t for t in re.findall(r"[a-zA-Z0-9_./-]+", q) if len(t) >= 3 and t not in stop]
    if not tokens or not searchable_cols: return df.head(0)
    combined = pd.Series("", index=df.index, dtype=str)
    for col in searchable_cols:
        combined = combined + " " + df[col].astype(str).str.lower()
    mask = pd.Series(False, index=df.index)
    for token in tokens:
        mask = mask | combined.str.contains(re.escape(token), na=False)
    return df[mask].copy()



def chat_answer(question: str, run_frames: List[Dict[str, pd.DataFrame]]) -> Tuple[str, pd.DataFrame | None]:
    q = question.lower().strip()
    if not run_frames:
        return "Hi! Upload and generate a dashboard first, then I can answer questions about SLA, slow APIs, errors, regions, tracks, and comparisons.", None

    df = combined_df(run_frames)
    label = "selected report(s)"
    n = extract_top_n(q)
    mcol = metric_col(q)

    s = summarize_run(df)
    run_count = len(run_frames)
    regions = sorted(set([frames.get("Region", region_from_frames(frames)) for frames in run_frames]))
    region_text = ", ".join([r for r in regions if r and r != "Unknown"]) or "selected region(s)"

    # Friendly small talk.
    greetings = {"hi", "hello", "hey", "hii", "hai", "good morning", "good afternoon", "good evening"}
    farewells = {"bye", "goodbye", "see you", "thanks bye", "thank you bye"}
    thanks = {"thanks", "thank you", "thx", "super", "good", "great", "awesome"}

    if q in greetings or any(q.startswith(g + " ") for g in greetings):
        return (
            f"Hi! I’m ready to help with this JMeter report. "
            f"Current summary: **{s['transactions']:,} APIs**, **{s['samples']:,} samples**, "
            f"**{s['sla_compliance']}% SLA pass**, **{s['error_rate']}% error rate**, "
            f"and regions/runs: **{region_text}**. Ask me about slow APIs, SLA breaches, errors, tracks, or comparison.",
            None,
        )

    if q in farewells or any(w in q for w in ["bye", "goodbye", "see you"]):
        return (
            "Bye! Quick reminder before you go: the dashboard has SLA status, slow APIs, error APIs, region comparison, and Track Comparison. "
            "Come back anytime and ask me about any API, track, region, or SLA breach.",
            None,
        )

    if q in thanks or any(w in q for w in ["thank", "thanks", "awesome", "great job"]):
        return (
            "You’re welcome! I can still help with report questions like: top slow APIs, SLA breaches, worst tracks, top errors, max/avg/min time, sample count, or region comparison.",
            None,
        )

    if any(w in q for w in ["help", "what can you do", "examples", "sample questions", "how to ask"]):
        return (
            "You can ask me things like:\n\n"
            "- What is the overall SLA summary?\n"
            "- Which APIs breached SLA?\n"
            "- Show top 10 slow APIs by max or avg response time.\n"
            "- Which tracks are worst?\n"
            "- Show top error APIs.\n"
            "- Compare APJC vs EMEA vs US.\n"
            "- What is the report date, duration, users and devices?\n"
            "- Search for an API, endpoint, scenario, or track name.",
            None,
        )

    if any(w in q for w in ["context","date","duration","region","users","devices","concurrent"]):
        rows = []
        for f in run_frames:
            info = f.get("Run_Info")
            if info is not None and not info.empty:
                row = info.iloc[0].to_dict()
                row["Run"] = f["Label"]
                row["Region"] = f.get("Region", region_from_frames(f))
                rows.append(row)
        if rows:
            context = pd.DataFrame(rows)
            return "Here is the report context I found from the uploaded run/file details.", context[safe_cols(context, ["Run","Region","Concurrent Users","Devices Count","Date","Duration"])]
        return "Report context was not available in the uploaded file names or parsed metadata.", None

    if any(w in q for w in ["health","summary","overall","status","executive","overview"]):
        return (
            f"Overall for **{label}**: Health Score **{s['performance_score']}/100**, "
            f"SLA Compliance **{s['sla_compliance']}%**, Success Rate **{s['success_rate']}%**, "
            f"Error Rate **{s['error_rate']}%**, Avg Response **{s['avg_sec']} sec**, "
            f"Min **{s['min_sec']} sec**, Max **{s['max_sec']} sec**, Total APIs **{s['transactions']:,}**, "
            f"Samples **{s['samples']:,}**, Errors **{s['errors']:,}**.",
            None,
        )

    if any(w in q for w in ["compare", "comparison", "regression", "improve", "degrade", "apjc", "emea", "us"]):
        rows = []
        for frames in run_frames:
            row = summarize_run(frames["APIs"])
            row["Run"] = frames["Label"]
            row["Region"] = frames.get("Region", region_from_frames(frames))
            rows.append(row)
        comp = pd.DataFrame(rows)
        if not comp.empty:
            cols = ["Region", "Run", "avg_sec", "min_sec", "max_sec", "success_rate", "error_rate", "sla_compliance", "performance_score", "errors", "samples"]
            return "Here is the comparison across uploaded runs/regions.", comp[safe_cols(comp, cols)].sort_values(["Region", "Run"])
        return "I could not find multiple run/region data to compare.", None

    if any(w in q for w in ["sla","breach","breached","violate","violation","pass","failed","fail"]):
        fail = df[df["SLA Status"] == "FAIL"].sort_values("SLA Breach Sec", ascending=False)
        if "pass" in q and "fail" not in q and "breach" not in q:
            ok = df[df["SLA Status"] == "PASS"].copy()
            return f"APIs passing SLA: **{len(ok):,}** out of **{len(df):,}** APIs.", ok[standard_api_cols(ok)].head(n)
        if fail.empty:
            return "Good news: I don’t see any SLA breaches in the selected report data.", None
        return f"Top {min(n,len(fail))} SLA breaches. UI target is <3 sec.", fail[standard_api_cols(fail)].head(n)

    if any(w in q for w in ["error","errors","failure","failures","errorpct"]):
        err = df[pd.to_numeric(df.get("errorCount",0), errors="coerce").fillna(0)>0].copy()
        if err.empty:
            return "No API errors found in the selected report data.", None
        sort_col = "errorPct" if "percent" in q or "pct" in q else "errorCount"
        return f"Top {min(n,len(err))} error APIs sorted by **{sort_col}**.", err.sort_values(sort_col, ascending=False)[standard_api_cols(err)].head(n)

    if any(w in q for w in ["track","tracks","feature","features"]):
        ts = track_summary(df)
        if ts.empty:
            return "No track/feature data found in the selected report.", None
        return "Worst tracks by Max Sec, Avg Sec, Errors, and SLA Fail %.", ts.head(n)

    if any(w in q for w in ["sample","samples","count","volume","load"]):
        sample_df = df.sort_values("sampleCount", ascending=False)
        return f"Top {min(n,len(sample_df))} APIs by sample count.", sample_df[standard_api_cols(sample_df)].head(n)

    if any(w in q for w in ["slow","latency","response","time","avg","maximum","minimum","max","min"]):
        if mcol not in df.columns:
            return f"{mcol} is not available in this report.", None
        top = df.sort_values(mcol, ascending=False)
        return f"Top {min(n,len(top))} APIs based on **{mcol}**.", top[standard_api_cols(top)].head(n)

    matched = match_rows(df, question)
    if not matched.empty:
        return f"I found {len(matched)} matching report rows for your search.", matched.sort_values(["SLA Breach Sec","Avg ResTime in sec","errorCount"], ascending=False)[standard_api_cols(matched)].head(n)

    return (
        "I can answer normal greetings and report-related questions. For this dashboard, please ask about SLA, slow APIs, max/avg/min times, errors, tracks, regions, samples, report context, or comparisons. "
        "For unrelated topics, I’ll keep the answer focused on this uploaded performance report.",
        None,
    )


def render_chatbot(run_frames: List[Dict[str, pd.DataFrame]], key_suffix: str = 'side') -> None:
    st.markdown('<div class="chat-card"><div class="chat-header">AI ASSISTANT</div>', unsafe_allow_html=True)
    st.write("Hi! I can chat normally and answer questions from this uploaded performance report.")
    with st.expander("Try asking me", expanded=True):
        st.write("- Hi / Bye\n- Give overall summary\n- Top slow APIs by max response\n- Which APIs breached SLA?\n- Top error APIs\n- Compare APJC, EMEA and US\n- Worst tracks\n- What is report date and duration?")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("table") is not None:
                st.dataframe(msg["table"], use_container_width=True, hide_index=True)
    question = st.chat_input("Ask anything about performance...", key=f"chat_input_{key_suffix}_{st.session_state.get('run_id', 'no_run')}")
    if question:
        st.session_state.messages.append({"role":"user","content":question,"table":None})
        answer, table = chat_answer(question, run_frames)
        st.session_state.messages.append({"role":"assistant","content":answer,"table":table})
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def build_non_api_track_summary(track_name: str) -> pd.DataFrame:
    uploads = normalize_saved_uploads(load_saved_uploads())
    rows = []
    for item in uploads:
        item_track = item.get("track") or infer_program_track(item.get("file_name", ""))[1]
        if item_track != track_name:
            continue
        rows.append({
            "File": item.get("file_name", ""),
            "Region": item.get("region", "Unknown"),
            "Date": item.get("date", "N/A"),
            "Duration": item.get("duration", "N/A"),
            "Uploaded At": item.get("uploaded_at", ""),
        })
    return pd.DataFrame(rows)


def render_non_api_track_view(track_name: str) -> None:
    track_frames = []
    for frames in st.session_state.get("run_frames", []):
        info = frames.get("Run_Info")
        info_row = info.iloc[0].to_dict() if info is not None and not info.empty else {}
        frame_track = str(info_row.get("Track") or infer_program_track(frames.get("Label", ""))[1])
        if frame_track == track_name:
            track_frames.append(frames)

    if track_frames:
        df = combined_df(track_frames)
        metric_col_name = "Avg ResTime in sec"
        focus = df.copy()
        metric_title = "Avg Response Time (sec)"
        if track_name == TRACK_UI:
            si_focus = df[df["Scenario"].astype(str).str.upper().isin(["SI", "SPEED INDEX", "SPEED_INDEX"])]
            focus = si_focus if not si_focus.empty else df
            metric_title = "Speed Index (sec)"
            st.info("UI SLA target is configured as Speed Index < 3 sec.")

        if focus.empty:
            st.warning(f"No {track_name} records available in generated results.")
            return

        avg_value = round(float(pd.to_numeric(focus[metric_col_name], errors="coerce").fillna(0).mean()), 2)
        min_value = round(float(pd.to_numeric(focus["Min ResTime in sec"], errors="coerce").fillna(0).min()), 2) if "Min ResTime in sec" in focus.columns else 0.0
        max_value = round(float(pd.to_numeric(focus["MaxRes Time in sec"], errors="coerce").fillna(0).max()), 2)
        pass_pct = round(float((focus["SLA Status"] == "PASS").mean() * 100), 2)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(metric_title, f"{avg_value}s")
        k2.metric("Min", f"{min_value}s")
        k3.metric("Max", f"{max_value}s")
        k4.metric("SLA Pass %", f"{pass_pct}%")

        region_comp = focus.groupby(["Region", "Run"], as_index=False)[metric_col_name].mean()
        fig = px.bar(region_comp, x="Region", y=metric_col_name, color="Run", barmode="group", title=f"{track_name}: Region Comparison")
        fig.update_layout(height=320, xaxis_title="Region", yaxis_title=metric_title)
        st.plotly_chart(fig, use_container_width=True)

        regions = sorted(focus["Region"].dropna().astype(str).unique().tolist())
        selected_region = st.selectbox(f"{track_name} Region Drilldown", ["All"] + regions, key=f"{track_name}_region_drilldown")
        region_df = focus if selected_region == "All" else focus[focus["Region"].astype(str) == selected_region]
        detail_cols = safe_cols(region_df, ["Run", "Region", "Feature", "Scenario", "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec", "SLA Sec", "SLA Status", "errorCount", "sampleCount"])
        st.dataframe(region_df[detail_cols].sort_values("Avg ResTime in sec", ascending=False), use_container_width=True, hide_index=True, height=min(460, 72 + 34 * len(region_df)))
        return

    if track_name == TRACK_UI:
        st.info("UI Lighthouse metrics dashboard is enabled. Upload CSV and click Generate Results to see charts.")
    elif track_name == TRACK_CLOUD:
        st.info("Cloud Assist Connector dashboard is enabled. Upload CSV and click Generate Results to see charts.")
    else:
        st.info("Customer Inventory Benchmarking dashboard is enabled. Upload CSV and click Generate Results to see charts.")

    summary_df = build_non_api_track_summary(track_name)
    if summary_df.empty:
        st.warning(f"No saved {track_name} CSV reports yet. Upload from the main page to populate this view.")
        return
    st.dataframe(summary_df, use_container_width=True, hide_index=True, height=min(440, 72 + 38 * len(summary_df)))





SAVED_REPORTS_DIR = Path("saved_reports")
SAVED_REPORTS_META = SAVED_REPORTS_DIR / "latest_uploads.json"


def ensure_saved_reports_dir() -> None:
    SAVED_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not SAVED_REPORTS_META.exists():
        SAVED_REPORTS_META.write_text("[]", encoding="utf-8")


def load_saved_uploads() -> List[Dict[str, str]]:
    ensure_saved_reports_dir()
    try:
        data = json.loads(SAVED_REPORTS_META.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else []
        cleaned = normalize_saved_uploads(items)
        if len(cleaned) != len(items):
            SAVED_REPORTS_META.write_text(json.dumps(cleaned[:SAVED_REPORT_LIMIT], indent=2), encoding="utf-8")
        return cleaned
    except Exception:
        return []





@st.cache_data(show_spinner=False)
def cached_excel_bytes_for_saved_api(saved_path_str: str, display_name: str, mtime: float) -> bytes:
    """Build Excel bytes for one saved API JSON file and cache by path/name/mtime."""
    saved_path = Path(saved_path_str)
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / f"{display_name}.xlsx"
        build_report(saved_path, output_path)
        return output_path.read_bytes()

def compact_saved_file_label(file_name: str) -> str:
    """Return short report label similar to Reports tab: Region-Users-Devices-Date."""
    info = infer_saved_report_info(file_name)
    region = info.get("region") or "Unknown"
    users = info.get("users") or "N/A"
    devices = info.get("devices") or "N/A"
    date = info.get("date") or "N/A"

    # Normalize users/devices text.
    users = str(users).replace(" Users", "Users")
    if users != "N/A" and "User" not in users:
        users = f"{users}Users"
    devices = str(devices).replace(" Devices", "Devices")
    if devices != "N/A" and "Device" not in devices:
        devices = f"{devices}Devices"

    if region != "Unknown" and users != "N/A" and devices != "N/A" and date != "N/A":
        return f"{region}-{users}-{devices}-{date}"
    return Path(file_name).stem


def infer_saved_report_info(file_name: str) -> Dict[str, str]:
    stem = Path(file_name).stem
    upper = stem.upper()

    standard_parts = stem.split("_")
    track_from_name = "N/A"
    app_from_name = "N/A"
    program_from_name = "N/A"
    if len(standard_parts) >= 10:
        track_from_name = standard_parts[0]
        app_from_name = standard_parts[1]
        program_from_name = standard_parts[2]

    region = "Unknown"
    for item in ["APJC", "EMEA", "US", "AMER", "EU", "LATAM", "INDIA"]:
        if re.search(rf"(?:^|[_\-\s]){item}(?:$|[_\-\s])", upper):
            region = item
            break

    duration = "N/A"
    duration_match = re.search(r"(\d+)\s*[_\-\s]?\s*(HOUR|HOURS|HR|HRS)", upper)
    if duration_match:
        duration = f"{duration_match.group(1)} Hour"

    date = "N/A"
    parsed_date = extract_mmddyyyy_from_text(stem)
    if parsed_date:
        date = f"{parsed_date[:2]}-{parsed_date[2:4]}-{parsed_date[4:8]}"

    users = "N/A"
    user_patterns = [
        r"(\d+(?:\.\d+)?\s*K?)\s*[_\-\s]*(?:CONCURRENT[_\-\s]*)?USERS?",
        r"(?:CONCURRENT[_\-\s]*)?USERS?[_\-\s]*(\d+(?:\.\d+)?\s*K?)",
        r"(\d+(?:\.\d+)?\s*K?)\s*[_\-\s]*VU\b",
        r"\bVU[_\-\s]*(\d+(?:\.\d+)?\s*K?)",
    ]
    for pattern in user_patterns:
        m = re.search(pattern, upper)
        if m:
            users = m.group(1).replace(" ", "")
            break

    devices = "N/A"
    device_patterns = [
        r"(\d+(?:\.\d+)?\s*K?)\s*[_\-\s]*DEVICES?",
        r"DEVICES?[_\-\s]*(\d+(?:\.\d+)?\s*K?)",
        # Common compact comparison naming: 50VU-100K, 100VU_100K
        r"\d+(?:\.\d+)?\s*K?\s*[_\-\s]*VU[_\-\s]*(\d+(?:\.\d+)?\s*K)\b",
        r"\d+(?:\.\d+)?\s*K?\s*[_\-\s]*USERS?[_\-\s]*(\d+(?:\.\d+)?\s*K)\b",
    ]
    for pattern in device_patterns:
        m = re.search(pattern, upper)
        if m:
            devices = m.group(1).replace(" ", "")
            break
    if devices != "N/A":
        devices = f"{devices} Devices"

    env = extract_env_token(file_name)
    run_id = "N/A"
    run_match = re.search(r"(?:^|[_\-\s])(RUN[_\-]?ID|RUN)[_\-]?([A-Z0-9]+)(?:$|[_\-\s])", upper)
    if run_match:
        run_id = f"RUN-{run_match.group(2)}"
    epoch = "N/A"
    epoch_match = re.search(r"EPOC[_\-]?(\d{9,13})", upper)
    if epoch_match:
        epoch = epoch_match.group(1)
    if len(standard_parts) >= 10:
        users = standard_parts[5].replace("Users", "").replace("users", "") or users
        users = re.sub(r"^\d{9,13}$", "N/A", str(users))
        devices = standard_parts[6].replace("Devices", " Devices").replace("devices", " Devices") or devices
        region = standard_parts[7].upper() if standard_parts[7] else region
        env = standard_parts[8].upper() if standard_parts[8] else env
        run_id = standard_parts[9] if standard_parts[9].upper().startswith("RUN") else run_id
        if len(standard_parts) > 4 and re.fullmatch(r"\d{8}", standard_parts[3]):
            mmddyyyy_token = standard_parts[3]
            date = f"{mmddyyyy_token[:2]}-{mmddyyyy_token[2:4]}-{mmddyyyy_token[4:8]}"
        if len(standard_parts) > 4 and standard_parts[4].upper().startswith("EPOC"):
            epoch = re.sub(r"[^0-9]", "", standard_parts[4]) or epoch

    normalized = re.sub(r"\s+", "", stem)
    match = re.match(
        r"^(?P<track>[^_]+)_(?P<app>[^_]+)_(?P<program>[^_]+)_(?P<date>\d{8})_(?:EPOC|EPOCH)[-_]?(?P<epoch>\d{9,13})_(?P<users>[^_]+)_(?P<devices>[^_]+)_(?P<region>[^_]+)_(?P<env>[^_]+)_(?P<runid>[^_]+)$",
        normalized,
        re.IGNORECASE,
    )
    if match:
        track_from_name = match.group("track")
        app_from_name = match.group("app")
        program_from_name = match.group("program")
        mmddyyyy_token = match.group("date")
        date = f"{mmddyyyy_token[:2]}-{mmddyyyy_token[2:4]}-{mmddyyyy_token[4:8]}"
        epoch = match.group("epoch")
        users = re.sub(r"(?i)users?", "", match.group("users")) or users
        users = re.sub(r"^\d{9,13}$", "N/A", str(users))
        devices_raw = re.sub(r"(?i)devices?", "", match.group("devices"))
        devices = f"{devices_raw} Devices" if devices_raw else devices
        region = match.group("region").upper()
        env = match.group("env").upper()
        run_id = match.group("runid")

    return {
        "region": region,
        "duration": duration,
        "date": date,
        "users": users,
        "devices": devices,
        "env": env,
        "run_id": run_id,
        "epoch": epoch,
        "track": track_from_name,
        "application": app_from_name,
        "program": program_from_name,
    }


def run_display_label(frames: Dict[str, pd.DataFrame]) -> str:
    """Short comparison label: Region UsersVU-Devices, never full filename."""
    label = str(frames.get("Label", ""))
    info = infer_saved_report_info(label)

    region = frames.get("Region", region_from_frames(frames))
    if not region or region == "Unknown":
        region = info.get("region", "Unknown")

    users = info.get("users", "N/A")
    devices = info.get("devices", "N/A")

    run_info = frames.get("Run_Info")
    if run_info is not None and not run_info.empty:
        row = run_info.iloc[0].to_dict()
        if not users or users == "N/A":
            users = str(row.get("Concurrent Users", row.get("Users", "N/A")))
        if not devices or devices == "N/A":
            devices = str(row.get("Devices Count", row.get("Devices", "N/A")))

    def clean_users(value: str) -> str:
        value = str(value).strip()
        value = re.sub(r"(?i)\s*(concurrent\s*)?users?\s*", "", value).strip()
        value = re.sub(r"(?i)\s*vu\s*", "", value).strip()
        return value if value and value.upper() != "N/A" else "NA"

    def clean_devices(value: str) -> str:
        value = str(value).strip()
        value = re.sub(r"(?i)\s*devices?\s*", "", value).strip()
        return value if value and value.upper() != "N/A" else "NA"

    users_clean = clean_users(users)
    devices_clean = clean_devices(devices)
    region_clean = region if region and region != "Unknown" else "Region"

    track_name = frame_track_name(frames)
    if track_name == TRACK_UI:
        return f"{users_clean}Users-{devices_clean}Devices"

    return f"{region_clean}-{users_clean}VU-{devices_clean}"




def normalize_saved_uploads(existing: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate saved reports from existing metadata and disk.
    Duplicates are detected by file_hash first, then file_name.
    """
    seen_hashes = set()
    seen_names = set()
    cleaned = []
    to_remove = []

    for item in existing:
        file_name = item.get("file_name", "")
        saved_name = item.get("saved_name", "")
        file_hash = item.get("file_hash", "")

        program_name = item.get("program") or infer_program_track(file_name)[0]
        if program_name != PROGRAM_SAAS:
            to_remove.append(item)
            continue

        # Backfill hash for older saved files if missing.
        saved_path = SAVED_REPORTS_DIR / saved_name
        if not file_hash and saved_path.exists():
            try:
                file_hash = hashlib.sha256(saved_path.read_bytes()).hexdigest()
                item["file_hash"] = file_hash
            except Exception:
                file_hash = ""

        duplicate = False
        if file_hash and file_hash in seen_hashes:
            duplicate = True
        if file_name and file_name in seen_names:
            duplicate = True

        if duplicate:
            to_remove.append(item)
            continue

        if file_hash:
            seen_hashes.add(file_hash)
        if file_name:
            seen_names.add(file_name)
        cleaned.append(item)

    # Remove duplicate/non-SaaS physical files.
    for item in to_remove:
        try:
            dup_path = SAVED_REPORTS_DIR / item.get("saved_name", "")
            if dup_path.exists():
                dup_path.unlink()
        except Exception:
            pass

    return cleaned


def remove_saved_upload(saved_name: str) -> None:
    ensure_saved_reports_dir()
    existing = load_saved_uploads()
    updated = [item for item in existing if item.get("saved_name") != saved_name]

    try:
        file_path = SAVED_REPORTS_DIR / saved_name
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass

    SAVED_REPORTS_META.write_text(json.dumps(updated, indent=2), encoding="utf-8")


def save_uploaded_files_to_latest(uploaded_files) -> None:
    ensure_saved_reports_dir()
    existing = normalize_saved_uploads(load_saved_uploads())
    existing_hashes = {item.get("file_hash") for item in existing if item.get("file_hash")}
    existing_names = {item.get("file_name") for item in existing if item.get("file_name")}

    skipped_duplicates = []

    for uploaded_file in uploaded_files:
        original_name = Path(uploaded_file.name).name.replace(" ", "_")
        clean_name = build_standard_report_name(TRACK_API, PROGRAM_SAAS, original_name, ".json")
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Do not save duplicate reports. Hash match catches same content; file name catches same report uploaded again.
        if file_hash in existing_hashes or clean_name in existing_names:
            skipped_duplicates.append(clean_name)
            continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_name = f"{timestamp}_{clean_name}"
        saved_path = SAVED_REPORTS_DIR / saved_name
        saved_path.write_bytes(file_bytes)

        info = infer_saved_report_info(clean_name)
        program_name, track_name = infer_program_track(clean_name)

        existing.insert(0, {
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_name": clean_name,
            "original_file_name": original_name,
            "saved_name": saved_name,
            "file_hash": file_hash,
            "region": info["region"],
            "date": info["date"],
            "duration": info["duration"],
            "users": info["users"],
            "devices": info["devices"],
            "environment": info.get("env", "PROD"),
            "run_id": info.get("run_id", "N/A"),
            "application": APP_NAME_TOKEN,
            "program": program_name,
            "track": track_name,
        })

        existing_hashes.add(file_hash)
        existing_names.add(clean_name)

    keep = existing[:SAVED_REPORT_LIMIT]
    keep_names = {item["saved_name"] for item in keep}

    for old in existing[SAVED_REPORT_LIMIT:]:
        try:
            old_path = SAVED_REPORTS_DIR / old.get("saved_name", "")
            if old_path.exists():
                old_path.unlink()
        except Exception:
            pass

    for file_path in SAVED_REPORTS_DIR.glob("*"):
        if not file_path.is_file() or file_path.name == SAVED_REPORTS_META.name:
            continue
        if file_path.name not in keep_names:
            try:
                file_path.unlink()
            except Exception:
                pass

    SAVED_REPORTS_META.write_text(json.dumps(keep, indent=2), encoding="utf-8")

    if skipped_duplicates:
        st.info("Duplicate upload skipped: " + ", ".join(skipped_duplicates[:3]) + (" ..." if len(skipped_duplicates) > 3 else ""))


def save_uploaded_files_for_track(uploaded_files, track_name: str, program_name: str = PROGRAM_SAAS) -> None:
    ensure_saved_reports_dir()
    existing = normalize_saved_uploads(load_saved_uploads())
    existing_hashes = {item.get("file_hash") for item in existing if item.get("file_hash")}
    existing_names = {item.get("file_name") for item in existing if item.get("file_name")}
    skipped_duplicates = []

    for uploaded_file in uploaded_files:
        original_name = Path(uploaded_file.name).name.replace(" ", "_")
        extension = Path(original_name).suffix or ".csv"
        clean_name = build_standard_report_name(track_name, program_name, original_name, extension)
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        if file_hash in existing_hashes or clean_name in existing_names:
            skipped_duplicates.append(clean_name)
            continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_name = f"{timestamp}_{clean_name}"
        saved_path = SAVED_REPORTS_DIR / saved_name
        saved_path.write_bytes(file_bytes)
        info = infer_saved_report_info(clean_name)

        existing.insert(0, {
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_name": clean_name,
            "original_file_name": original_name,
            "saved_name": saved_name,
            "file_hash": file_hash,
            "region": info["region"],
            "date": info["date"],
            "duration": info["duration"],
            "users": info["users"],
            "devices": info["devices"],
            "environment": info.get("env", "PROD"),
            "run_id": info.get("run_id", "N/A"),
            "application": APP_NAME_TOKEN,
            "program": program_name,
            "track": track_name,
        })
        existing_hashes.add(file_hash)
        existing_names.add(clean_name)

    keep = existing[:SAVED_REPORT_LIMIT]
    keep_names = {item["saved_name"] for item in keep}
    for old in existing[SAVED_REPORT_LIMIT:]:
        try:
            old_path = SAVED_REPORTS_DIR / old.get("saved_name", "")
            if old_path.exists():
                old_path.unlink()
        except Exception:
            pass

    for file_path in SAVED_REPORTS_DIR.glob("*"):
        if not file_path.is_file() or file_path.name == SAVED_REPORTS_META.name:
            continue
        if file_path.name not in keep_names:
            try:
                file_path.unlink()
            except Exception:
                pass

    SAVED_REPORTS_META.write_text(json.dumps(keep, indent=2), encoding="utf-8")
    if skipped_duplicates:
        st.info("Duplicate upload skipped: " + ", ".join(skipped_duplicates[:3]) + (" ..." if len(skipped_duplicates) > 3 else ""))




def generate_dashboard_from_json_paths(json_paths: List[Path], labels: List[str]) -> None:
    """Generate the same Excel/Dashboard/Chatbot state from saved JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        output_path = tmpdir_path / "JMeter_Report.xlsx"

        run_frames: List[Dict[str, pd.DataFrame]] = []
        for path, label in zip(json_paths, labels):
            run_frames.append(process_uploaded_file(path, label))

        if len(json_paths) == 1:
            build_report(json_paths[0], output_path)
        else:
            build_comparison_report(json_paths, labels, output_path)

        run_frames = add_region_to_frames(run_frames)
        excel_bytes = output_path.read_bytes()
        new_run_id = uuid.uuid4().hex

        dashboard_store[new_run_id] = {
            "run_frames": run_frames,
            "excel_bytes": excel_bytes,
            "report_file_name": "JMeter_Report.xlsx",
        }
        st.session_state.excel_bytes = excel_bytes
        st.session_state.run_frames = run_frames
        st.session_state.report_file_name = "JMeter_Report.xlsx"
        st.session_state.excel_api_only = True
        st.session_state.messages = []
        st.session_state.run_id = new_run_id


def sanitize_column_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def pick_first_matching_column(df: pd.DataFrame, patterns: List[str]) -> str | None:
    for col in df.columns:
        normalized = sanitize_column_name(col)
        if any(re.search(pattern, normalized) for pattern in patterns):
            return col
    return None


def to_numeric_series(df: pd.DataFrame, col: str | None) -> pd.Series:
    if not col or col not in df.columns:
        return pd.Series(dtype=float)
    series = pd.to_numeric(df[col], errors="coerce").dropna()
    return series.astype(float)


def pick_ui_speed_index_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        norm = sanitize_column_name(col)
        if is_speed_index_metric(norm) or re.search(r"speed[_\s]*index", str(col), re.IGNORECASE):
            return col
    return None


def ui_speed_index_bucket_percentages(values: pd.Series) -> Dict[str, float]:
    buckets = {"0-3s %": 0, "3-4s %": 0, "4-5s %": 0, ">6s %": 0}
    if values.empty:
        return {k: 0.0 for k in buckets}
    clean = pd.to_numeric(values, errors="coerce").dropna().astype(float)
    if clean.empty:
        return {k: 0.0 for k in buckets}
    for value in clean:
        bucket = response_bucket(float(value), False)
        if bucket in buckets:
            buckets[bucket] += 1
    total = float(len(clean))
    return {name: round((count / total) * 100, 2) for name, count in buckets.items()}


def build_ui_raw_detail_df(run_frames: List[Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    rows: List[pd.DataFrame] = []
    for frames in run_frames:
        raw_df = frames.get("UI_Raw")
        if raw_df is None or raw_df.empty:
            continue
        piece = raw_df.copy()
        piece.insert(0, "Result", run_display_label(frames))
        piece.insert(1, "Region", frames.get("Region", region_from_frames(frames)))
        rows.append(piece)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def numeric_scalar(value, default: float = 0.0) -> float:
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return float(default)
    return float(parsed)


def make_api_like_row(feature: str, scenario: str, values: pd.Series, sla_sec: float, higher_is_better: bool = False) -> Dict[str, object]:
    if values.empty:
        avg_v = min_v = max_v = 0.0
        sample_count = 0
    else:
        avg_v = round(float(values.mean()), 3)
        min_v = round(float(values.min()), 3)
        max_v = round(float(values.max()), 3)
        sample_count = int(values.count())

    if higher_is_better:
        pass_status = avg_v >= float(sla_sec)
        error_count = int((values < float(sla_sec)).sum()) if not values.empty else 0
        breach_sec = round(max(float(sla_sec) - avg_v, 0.0), 3)
    else:
        pass_status = avg_v <= float(sla_sec)
        error_count = int((values > float(sla_sec)).sum()) if not values.empty else 0
        breach_sec = round(max(avg_v - float(sla_sec), 0.0), 3)

    error_pct = round((error_count / sample_count) * 100, 3) if sample_count else 0.0
    return {
        "Feature": feature,
        "Scenario": scenario,
        "Endpoint": scenario,
        "API": f"{feature}/{scenario}/{scenario}",
        "sampleCount": sample_count,
        "errorCount": error_count,
        "errorPct": error_pct,
        "Avg ResTime in sec": avg_v,
        "Min ResTime in sec": min_v,
        "MaxRes Time in sec": max_v,
        "SLA Sec": float(sla_sec),
        "SLA Status": "PASS" if pass_status else "FAIL",
        "SLA Breach Sec": breach_sec,
        "Track Type": feature,
    }


def build_api_like_df_from_csv(csv_path: Path, track_name: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path)
    if raw.empty:
        return pd.DataFrame(columns=standard_api_cols(pd.DataFrame(columns=[
            "Feature", "Scenario", "Endpoint", "sampleCount", "errorCount", "errorPct",
            "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec",
            "SLA Sec", "SLA Status", "SLA Breach Sec",
        ])))

    rows: List[Dict[str, object]] = []

    if track_name == TRACK_UI:
        metric_map = {
            "FCP": [r"\bfcp\b", r"first_contentful_paint"],
            "LCP": [r"\blcp\b", r"largest_contentful_paint"],
            "TBT": [r"\btbt\b", r"total_blocking_time"],
            "CLS": [r"\bcls\b", r"cumulative_layout_shift"],
            "SI": [r"\bsi\b", r"speed_index"],
            "PERFORMANCE": [r"performance", r"perf_score", r"score"],
        }
        used_cols = set()
        for metric, patterns in metric_map.items():
            col = pick_first_matching_column(raw, patterns)
            series = to_numeric_series(raw, col)
            if series.empty:
                continue
            if col:
                used_cols.add(col)
            if metric == "PERFORMANCE":
                rows.append(make_api_like_row(metric, metric, series, UI_SLA_THRESHOLDS[metric], higher_is_better=True))
            else:
                rows.append(make_api_like_row(metric, metric, series, 3.0, higher_is_better=False))

        for col in raw.columns:
            if col in used_cols:
                continue
            series = to_numeric_series(raw, col)
            if series.empty:
                continue
            name = str(col)
            norm = sanitize_column_name(name)
            if is_excluded_ui_metric(name):
                continue
            if re.search(r"performance|score", norm):
                rows.append(make_api_like_row(name, name, series, UI_SLA_THRESHOLDS["PERFORMANCE"], higher_is_better=True))
            else:
                rows.append(make_api_like_row(name, name, series, 3.0, higher_is_better=False))

        if not rows:
            for col in raw.columns:
                series = to_numeric_series(raw, col)
                if series.empty:
                    continue
                name = str(col)
                norm = sanitize_column_name(name)
                if is_excluded_ui_metric(name):
                    continue
                if re.search(r"performance|score", norm):
                    rows.append(make_api_like_row(name, name, series, UI_SLA_THRESHOLDS["PERFORMANCE"], higher_is_better=True))
                else:
                    rows.append(make_api_like_row(name, name, series, 3.0, higher_is_better=False))
    else:
        avg_col = pick_first_matching_column(raw, [r"\bavg\b", r"average", r"mean", r"response_time", r"res_time", r"latency"]) or pick_first_matching_column(raw, [r"\btime\b", r"sec", r"ms"])
        min_col = pick_first_matching_column(raw, [r"\bmin\b"])
        max_col = pick_first_matching_column(raw, [r"\bmax\b"])
        sample_col = pick_first_matching_column(raw, [r"sample", r"count", r"requests", r"hits"])
        error_col = pick_first_matching_column(raw, [r"error_count", r"errors", r"failed", r"failures"])
        error_pct_col = pick_first_matching_column(raw, [r"error_pct", r"error_percent", r"failure_pct", r"failure_percent"])
        feature_col = pick_first_matching_column(raw, [r"feature", r"track", r"module", r"component"])
        scenario_col = pick_first_matching_column(raw, [r"scenario", r"transaction", r"name", r"endpoint", r"api"])

        sla_sec = NON_API_LATENCY_SLA_SEC.get(track_name, 2.0)
        if avg_col:
            for idx, row in raw.iterrows():
                avg_v = numeric_scalar(row.get(avg_col), 0)
                min_v = numeric_scalar(row.get(min_col), avg_v)
                max_v = numeric_scalar(row.get(max_col), avg_v)
                sample_count = max(1, int(numeric_scalar(row.get(sample_col), 1)))
                error_count = max(0, int(numeric_scalar(row.get(error_col), 0)))
                error_pct_raw = numeric_scalar(row.get(error_pct_col), -1)
                error_pct = error_pct_raw if error_pct_raw >= 0 else (error_count / sample_count * 100 if sample_count else 0)
                feature = str(row.get(feature_col) or track_name)
                scenario = str(row.get(scenario_col) or f"{track_name}-{idx+1}")
                pass_status = (avg_v <= sla_sec and min_v <= sla_sec and max_v <= sla_sec)
                rows.append({
                    "Feature": feature,
                    "Scenario": scenario,
                    "Endpoint": scenario,
                    "API": f"{feature}/{scenario}/{scenario}",
                    "sampleCount": sample_count,
                    "errorCount": error_count,
                    "errorPct": round(error_pct, 3),
                    "Avg ResTime in sec": round(avg_v, 3),
                    "Min ResTime in sec": round(min_v, 3),
                    "MaxRes Time in sec": round(max_v, 3),
                    "SLA Sec": float(sla_sec),
                    "SLA Status": "PASS" if pass_status else "FAIL",
                    "SLA Breach Sec": round(max(avg_v - sla_sec, 0.0), 3),
                    "Track Type": feature,
                })

        if not rows:
            ignored = {feature_col, scenario_col, sample_col, error_col, error_pct_col}
            for col in raw.columns:
                if col in ignored:
                    continue
                series = to_numeric_series(raw, col)
                if series.empty:
                    continue
                rows.append(make_api_like_row(track_name, str(col), series, sla_sec, higher_is_better=False))

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=[
            "Feature", "Scenario", "Endpoint", "sampleCount", "errorCount", "errorPct",
            "Avg ResTime in sec", "Min ResTime in sec", "MaxRes Time in sec",
            "SLA Sec", "SLA Status", "SLA Breach Sec", "Track Type",
        ])
    if track_name == TRACK_UI:
        df = apply_ui_speed_index_sla(df)
    return df


@st.cache_data(show_spinner=False)
def build_excel_bytes_from_frames(run_frames: List[Dict[str, pd.DataFrame]]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for index, frames in enumerate(run_frames, start=1):
            label = str(frames.get("Label", f"Run_{index}"))
            safe_label = re.sub(r"[^A-Za-z0-9_-]+", "_", label)[:20] or f"Run_{index}"
            apis_df = frames.get("APIs", pd.DataFrame())
            run_info = frames.get("Run_Info", pd.DataFrame())
            apis_df.to_excel(writer, index=False, sheet_name=f"{safe_label}_APIs"[:31])
            run_info.to_excel(writer, index=False, sheet_name=f"{safe_label}_Info"[:31])
    return output.getvalue()


def generate_dashboard_from_saved_csv(track_name: str, csv_path: Path, item: Dict[str, str] | None = None) -> None:
    label = Path((item or {}).get("file_name", csv_path.name)).stem
    inferred = infer_saved_report_info((item or {}).get("file_name", csv_path.name))
    region = (item or {}).get("region") or inferred.get("region", "Unknown")

    apis_df = build_api_like_df_from_csv(csv_path, track_name)
    ui_raw_df = pd.DataFrame()
    if track_name == TRACK_UI:
        try:
            ui_raw_df = pd.read_csv(csv_path)
        except Exception:
            ui_raw_df = pd.DataFrame()
    run_info = pd.DataFrame([{
        "Report File": (item or {}).get("file_name", csv_path.name),
        "Concurrent Users": (item or {}).get("users") or inferred.get("users", "N/A"),
        "Devices Count": (item or {}).get("devices") or inferred.get("devices", "N/A"),
        "Date": (item or {}).get("date") or inferred.get("date", "N/A"),
        "Duration": (item or {}).get("duration") or inferred.get("duration", "N/A"),
        "Region": region,
        "Application": (item or {}).get("application", APP_NAME_TOKEN),
        "Program": (item or {}).get("program", PROGRAM_SAAS),
        "Track": track_name,
        "Environment": (item or {}).get("environment", inferred.get("env", "PROD")),
        "Run ID": (item or {}).get("run_id", inferred.get("run_id", "N/A")),
        "Epoch": inferred.get("epoch", "N/A"),
    }])

    run_frames = [{
        "Label": label,
        "Region": region,
        "APIs": apis_df,
        "UI_Raw": ui_raw_df,
        "Transactions": pd.DataFrame(),
        "Errors": apis_df[apis_df.get("errorCount", 0) > 0].copy() if not apis_df.empty else pd.DataFrame(),
        "Run_Info": run_info,
    }]

    merged_frames = merge_run_frames_by_track(st.session_state.get("run_frames", []), run_frames, track_name)
    excel_bytes = build_excel_bytes_from_frames(run_frames)
    new_run_id = uuid.uuid4().hex
    report_name = f"{track_name.replace(' ', '_')}_Report.xlsx"

    dashboard_store[new_run_id] = {
        "run_frames": merged_frames,
        "excel_bytes": st.session_state.get("excel_bytes"),
        "report_file_name": st.session_state.get("report_file_name", "JMeter_Report.xlsx"),
    }
    st.session_state.run_frames = merged_frames
    st.session_state.messages = []
    st.session_state.run_id = new_run_id
    st.session_state["active_track"] = track_name
    st.session_state["dashboard_tab"] = "Overview"


def generate_dashboard_from_uploaded_csv_files(track_name: str, uploaded_files) -> None:
    run_frames: List[Dict[str, pd.DataFrame]] = []
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{Path(uploaded_file.name).name}") as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = Path(tmp.name)
        inferred = infer_saved_report_info(uploaded_file.name)
        apis_df = build_api_like_df_from_csv(temp_path, track_name)
        ui_raw_df = pd.DataFrame()
        if track_name == TRACK_UI:
            try:
                ui_raw_df = pd.read_csv(temp_path)
            except Exception:
                ui_raw_df = pd.DataFrame()
        run_info = pd.DataFrame([{
            "Report File": uploaded_file.name,
            "Concurrent Users": inferred.get("users", "N/A"),
            "Devices Count": inferred.get("devices", "N/A"),
            "Date": inferred.get("date", "N/A"),
            "Duration": inferred.get("duration", "N/A"),
            "Region": inferred.get("region", "Unknown"),
            "Application": inferred.get("application", APP_NAME_TOKEN),
            "Program": PROGRAM_SAAS,
            "Track": track_name,
            "Environment": inferred.get("env", "PROD"),
            "Run ID": inferred.get("run_id", "N/A"),
            "Epoch": inferred.get("epoch", "N/A"),
        }])
        run_frames.append({
            "Label": Path(uploaded_file.name).stem,
            "Region": inferred.get("region", "Unknown"),
            "APIs": apis_df,
            "UI_Raw": ui_raw_df,
            "Transactions": pd.DataFrame(),
            "Errors": apis_df[apis_df.get("errorCount", 0) > 0].copy() if not apis_df.empty else pd.DataFrame(),
            "Run_Info": run_info,
        })
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass

    merged_frames = merge_run_frames_by_track(st.session_state.get("run_frames", []), run_frames, track_name)
    new_run_id = uuid.uuid4().hex
    dashboard_store[new_run_id] = {
        "run_frames": merged_frames,
        "excel_bytes": st.session_state.get("excel_bytes"),
        "report_file_name": st.session_state.get("report_file_name", "JMeter_Report.xlsx"),
    }
    st.session_state.run_frames = merged_frames
    st.session_state.messages = []
    st.session_state.run_id = new_run_id
    st.session_state["active_track"] = track_name
    st.session_state["dashboard_tab"] = "Overview"



def render_latest_uploads_panel() -> None:
    uploads = normalize_saved_uploads(load_saved_uploads())
    # Persist duplicate cleanup immediately so user sees clean list.
    try:
        SAVED_REPORTS_META.write_text(json.dumps(uploads[:SAVED_REPORT_LIMIT], indent=2), encoding="utf-8")
    except Exception:
        pass

    st.markdown(
        """
<div class="main-page-card upload-card latest-team-box">
  <h3>Latest Team Uploads</h3>
  <p>Latest 15 uploaded JMeter JSON reports are saved for team reference. Duplicate reports are automatically skipped.</p>
</div>
<style>
.latest-team-box {
    margin-top:10px !important;
    padding:10px 14px !important;
    max-width: 960px !important;
}
.latest-team-box h3 {
    margin:0 0 3px 0 !important;
    color:#0f2b68 !important;
    font-size:17px !important;
    line-height:1.15 !important;
}
.latest-team-box p {
    color:#667085 !important;
    font-size:12px !important;
    margin:0 !important;
}
.hero-title-box {
    padding:13px 20px !important;
}
.hero-title-box h1 {
    font-size:19px !important;
    line-height:1.12 !important;
}
.hero-subtitle {
    font-size:14px !important;
    margin-bottom:14px !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

    if not uploads:
        st.info("No saved uploads yet. Upload JSON files and click Generate Results.")
        return

    saved_paths = []
    saved_labels = []
    for item in uploads:
        file_path = SAVED_REPORTS_DIR / item["saved_name"]
        if file_path.exists():
            saved_paths.append(file_path)
            saved_labels.append(Path(item["file_name"]).stem)

    if saved_paths:
        st.caption(f"Generate an executive dashboard and comparison report using the latest {len(saved_paths)} saved report(s).")
        saved_button_label = "Generate Comparison Dashboard" if len(saved_paths) > 1 else "Generate Dashboard From Latest Upload"
        if st.button(saved_button_label, key="generate_all_saved_uploads", use_container_width=True):
            try:
                generate_dashboard_from_json_paths(saved_paths, saved_labels)
                st.success(f"Generated dashboard, Excel report and chatbot from latest {len(saved_paths)} saved report(s).")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to generate from saved uploads: {exc}")

    header = st.columns([0.4, 2.8, 0.9, 1.35, 1.45, 1.35, 1.0])
    header[0].markdown("**#**")
    header[1].markdown("**File name**")
    header[2].markdown("**Region**")
    header[3].markdown("**Date / Duration**")
    header[4].markdown("**Uploaded at**")
    header[5].markdown("**Generate**")
    header[6].markdown("**Remove**")

    for index, item in enumerate(uploads, start=1):
        file_path = SAVED_REPORTS_DIR / item["saved_name"]
        inferred = infer_saved_report_info(item.get("file_name", ""))
        region = item.get("region") or inferred.get("region", "Unknown")
        date = item.get("date") or inferred.get("date", "N/A")
        duration = item.get("duration") or inferred.get("duration", "N/A")
        users = item.get("users") or inferred.get("users", "N/A")
        devices = item.get("devices")
        if not devices or str(devices).upper() == "N/A":
            devices = inferred.get("devices", "N/A")
        report_info = f"{date} / {duration}"
        tooltip = f"Generate dashboard for: Region={region}, Date={date}, Duration={duration}, Users={users}, Devices={devices}"

        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.4, 2.8, 0.9, 1.35, 1.45, 1.35, 1.0])
        c1.write(f"#{index}")
        c2.write(item["file_name"])
        c3.write(region)
        c4.write(report_info)
        c5.write(item["uploaded_at"])

        if file_path.exists():
            if c6.button("Generate Results", help=tooltip, key=f"generate_saved_upload_{index}_{item['saved_name']}", use_container_width=True):
                try:
                    generate_dashboard_from_json_paths([file_path], [Path(item["file_name"]).stem])
                    st.success(f"Generated dashboard, Excel report and chatbot for: {item['file_name']} ({region}, {date}, {duration}).")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to generate saved report: {exc}")
        else:
            c6.warning("Missing")

        if c7.button("Remove", key=f"remove_saved_upload_{index}_{item['saved_name']}", use_container_width=True):
            remove_saved_upload(item["saved_name"])
            st.success(f"Removed saved report: {item['file_name']}")
            st.rerun()




def render_main_page(show_subtitle: bool = True) -> None:
    subtitle_html = ""
    st.markdown(
        f"""
<div class="hero-title-box">
  <h1>{APP_TITLE}</h1>
</div>
{subtitle_html}
""",
        unsafe_allow_html=True,
    )


def render_management_landing_page() -> None:
    uploads = normalize_saved_uploads(load_saved_uploads())[:SAVED_REPORT_LIMIT]
    st.markdown(
        f"""
<div class="hero-title-box">
  <h1>{APP_TITLE}</h1>
</div>
<div class="hero-subtitle">
  Management dashboard access is view-only. Please use the dashboard link shared by the performance team to review the latest results.
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="main-page-card upload-card">
  <h3 style="margin-top:0;color:#0f2b68;">Performance Results Portal</h3>
  <p style="color:#475569;margin-bottom:10px;">Upload and report generation are restricted to the performance team.</p>
  <p style="color:#64748b;margin-bottom:0;">Management users can view dashboards generated from saved reports below.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    if not uploads:
        st.info("No saved reports are available yet. Ask the performance team to upload and save reports.")
        return

    saved_paths = []
    saved_labels = []
    for item in uploads:
        file_path = SAVED_REPORTS_DIR / item.get("saved_name", "")
        if file_path.exists():
            saved_paths.append(file_path)
            saved_labels.append(Path(item.get("file_name", file_path.name)).stem)

    if saved_paths:
        if st.button(f"View Dashboard From Latest {len(saved_paths)} Saved Reports", type="primary", use_container_width=True):
            try:
                generate_dashboard_from_json_paths(saved_paths, saved_labels)
                st.session_state["dashboard_tab"] = "Overview"
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to generate dashboard from saved reports: {exc}")

    render_saved_reports_table(uploads)


def render_api_saved_reports_compact() -> None:
    render_saved_reports_compact_for_track(TRACK_API, title="Saved API Reports", key_prefix="api")


def render_saved_reports_compact_for_track(track_name: str, title: str | None = None, key_prefix: str = "track") -> None:
    uploads = normalize_saved_uploads(load_saved_uploads())
    track_uploads = [
        item for item in uploads
        if (item.get("track") or infer_program_track(item.get("file_name", ""))[1]) == track_name
    ]
    if not track_uploads:
        st.info(f"No saved {track_name} reports yet.")
        return

    if title is None:
        st.markdown(f"**Saved {track_name} Reports**")
    elif str(title).strip():
        st.markdown(f"**{title}**")

    st.markdown(
        """
<style>
.compact-saved-row {
    background: #f8fbff;
    border: 1px solid #dbe4f0;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 8px;
}
.compact-saved-cell-name {
    font-size: 14px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 10px;
}
</style>
""",
        unsafe_allow_html=True,
    )

    for index, item in enumerate(track_uploads, start=1):
        file_path = SAVED_REPORTS_DIR / item.get("saved_name", "")
        inferred = infer_saved_report_info(item.get("file_name", ""))
        region = item.get("region") or inferred.get("region", "Unknown")
        users = item.get("users") or inferred.get("users", "N/A")
        devices = item.get("devices") or inferred.get("devices", "N/A")
        date = item.get("date") or inferred.get("date", "N/A")
        date_token = to_mm_dd_yyyy(date)
        include_users = track_name in {TRACK_API, TRACK_UI}
        report_name = f"{report_title(region, users, devices, include_users=include_users)}-{date_token}"

        st.markdown('<div class="compact-saved-row">', unsafe_allow_html=True)
        st.markdown(f'<div class="compact-saved-cell-name">{report_name}</div>', unsafe_allow_html=True)

        action_generate_col, action_remove_col = st.columns(2, gap="small")
        if file_path.exists():
            if action_generate_col.button("Generate Results", key=f"{key_prefix}_compact_generate_{index}_{item.get('saved_name','')}", use_container_width=True):
                try:
                    if track_name == TRACK_API:
                        generate_dashboard_from_json_paths([file_path], [Path(item.get("file_name", file_path.name)).stem])
                    else:
                        generate_dashboard_from_saved_csv(track_name, file_path, item)
                    st.success(f"Generated {track_name} results for {item.get('file_name', file_path.name)}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to generate saved report: {exc}")
        else:
            action_generate_col.warning("Missing")

        if action_remove_col.button("Remove", key=f"{key_prefix}_compact_remove_{index}_{item.get('saved_name','')}", use_container_width=True):
            remove_saved_upload(item.get("saved_name", ""))
            st.success("Removed saved report.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def saved_reports_rows(uploads: List[Dict[str, str]]) -> pd.DataFrame:
    rows = []
    for item in uploads:
        inferred = infer_saved_report_info(item.get("file_name", ""))
        rows.append({
            "File": item.get("file_name", ""),
            "Application": item.get("application") or inferred.get("application", APP_NAME_TOKEN),
            "Program": item.get("program") or infer_program_track(item.get("file_name", ""))[0],
            "Track": item.get("track") or infer_program_track(item.get("file_name", ""))[1],
            "Region": item.get("region") or inferred.get("region", "Unknown"),
            "Date": item.get("date") or inferred.get("date", "N/A"),
            "Duration": item.get("duration") or inferred.get("duration", "N/A"),
            "Users": item.get("users") or inferred.get("users", "N/A"),
            "Devices": item.get("devices") or inferred.get("devices", "N/A"),
            "Environment": item.get("environment") or inferred.get("env", "PROD"),
            "Run ID": item.get("run_id") or inferred.get("run_id", "N/A"),
            "Uploaded At": item.get("uploaded_at", ""),
        })
    return pd.DataFrame(rows)


def render_saved_reports_table(uploads: List[Dict[str, str]] | None = None, compact: bool = False, show_title: bool = True) -> None:
    if uploads is None:
        uploads = normalize_saved_uploads(load_saved_uploads())[:SAVED_REPORT_LIMIT]
    if show_title:
        st.markdown("#### Saved Reports Available")
    if not uploads:
        st.info("No saved reports are available yet.")
        return
    rows = saved_reports_rows(uploads)
    if compact:
        rows = rows[safe_cols(rows, ["File", "Region", "Date", "Uploaded At"])]
    st.dataframe(rows, use_container_width=True, hide_index=True, height=min(520, 72 + 38 * len(rows)))


def secret_value(*keys: str) -> str:
    for key in keys:
        try:
            value = st.secrets.get(key, "")
        except Exception:
            value = ""
        if value:
            return str(value)
    return ""


def team_upload_access_granted() -> bool:
    if st.session_state.get("team_authenticated"):
        return True

    expected_user = secret_value("UPLOAD_USERNAME", "USERNAME", "APP_USERNAME")
    expected_password = secret_value("UPLOAD_PASSWORD", "PASSWORD", "APP_PASSWORD", "UPLOAD_PASSCODE")
    if not expected_user and not expected_password:
        st.warning("Upload login is not configured. Add UPLOAD_USERNAME and UPLOAD_PASSWORD in Streamlit secrets.")
        return False

    left, center, right = st.columns([1, 1.45, 1])
    with center:
        st.markdown('<div class="login-form-wrap">', unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_clicked = st.button("Login to Upload Reports", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    valid_user = True if not expected_user else username == expected_user
    valid_password = password == expected_password
    if login_clicked:
        if valid_user and valid_password:
            st.session_state.team_authenticated = True
            st.query_params["page"] = "upload"
            st.rerun()
        st.error("Invalid username or password.")
    return False


def load_saved_dashboard_frames() -> List[Dict[str, pd.DataFrame]]:
    uploads = normalize_saved_uploads(load_saved_uploads())
    frames_out: List[Dict[str, pd.DataFrame]] = []

    for item in uploads:
        path = SAVED_REPORTS_DIR / item.get("saved_name", "")
        if not path.exists():
            continue

        file_name = item.get("file_name", path.name)
        label = Path(file_name).stem
        track_name = item.get("track") or infer_program_track(file_name)[1]
        suffix = str(path.suffix).lower()

        try:
            if suffix == ".json" and track_name == TRACK_API:
                frames_out.append(process_uploaded_file(path, label))
                continue

            if suffix == ".csv" and track_name in {TRACK_UI, TRACK_CLOUD, TRACK_INVENTORY}:
                inferred = infer_saved_report_info(file_name)
                region = item.get("region") or inferred.get("region", "Unknown")
                apis_df = build_api_like_df_from_csv(path, track_name)
                ui_raw_df = pd.DataFrame()
                if track_name == TRACK_UI:
                    try:
                        ui_raw_df = pd.read_csv(path)
                    except Exception:
                        ui_raw_df = pd.DataFrame()
                run_info = pd.DataFrame([{
                    "Report File": file_name,
                    "Concurrent Users": item.get("users") or inferred.get("users", "N/A"),
                    "Devices Count": item.get("devices") or inferred.get("devices", "N/A"),
                    "Date": item.get("date") or inferred.get("date", "N/A"),
                    "Duration": item.get("duration") or inferred.get("duration", "N/A"),
                    "Region": region,
                    "Application": item.get("application") or inferred.get("application", APP_NAME_TOKEN),
                    "Program": item.get("program") or PROGRAM_SAAS,
                    "Track": track_name,
                    "Environment": item.get("environment") or inferred.get("env", "PROD"),
                    "Run ID": item.get("run_id") or inferred.get("run_id", "N/A"),
                    "Epoch": inferred.get("epoch", "N/A"),
                }])
                frames_out.append({
                    "Label": label,
                    "Region": region,
                    "APIs": apis_df,
                    "UI_Raw": ui_raw_df,
                    "Transactions": pd.DataFrame(),
                    "Errors": apis_df[apis_df.get("errorCount", 0) > 0].copy() if not apis_df.empty else pd.DataFrame(),
                    "Run_Info": run_info,
                })
        except Exception:
            continue

    return add_region_to_frames(frames_out)


def load_static_saved_dashboard() -> bool:
    frames = load_saved_dashboard_frames()
    if not frames:
        return False

    uploads = normalize_saved_uploads(load_saved_uploads())
    signature = "|".join(
        f"{item.get('saved_name','')}:{(SAVED_REPORTS_DIR / item.get('saved_name','')).stat().st_mtime_ns}"
        for item in uploads
        if (SAVED_REPORTS_DIR / item.get("saved_name", "")).exists()
    )
    if st.session_state.get("saved_dashboard_signature") == signature and st.session_state.get("run_frames"):
        return True

    st.session_state["run_frames"] = frames
    st.session_state["excel_bytes"] = None
    st.session_state["report_file_name"] = "JMeter_Report.xlsx"
    st.session_state["messages"] = []
    st.session_state["dashboard_tab"] = "Overview"
    tracks_present: List[str] = []
    for frame in frames:
        info = frame.get("Run_Info")
        info_row = info.iloc[0].to_dict() if info is not None and not info.empty else {}
        track_name = canonical_track_name(info_row.get("Track") or infer_program_track(frame.get("Label", ""))[1])
        if track_name and track_name not in tracks_present:
            tracks_present.append(track_name)
    if tracks_present:
        st.session_state["active_track"] = tracks_present[0]

    st.session_state["saved_dashboard_signature"] = signature
    st.session_state["run_id"] = "saved-dashboard"
    return True



def dashboard_url_for_run(run_id_value: str) -> str:
    if run_id_value:
        return f"?view=dashboard&run_id={run_id_value}"
    return "?view=dashboard"






def render_action_cards() -> None:
    has_report = bool(st.session_state.get("run_id") and st.session_state.get("excel_bytes"))
    run_id_value = st.session_state.get("run_id", "")
    dashboard_href = f"{dashboard_url_for_run(run_id_value)}&tab=Overview" if has_report else "#"
    chatbot_href = f"{dashboard_url_for_run(run_id_value)}&tab=Chatbot" if has_report else "#"

    st.markdown(
        """
<style>
.action-card-title {
    margin:0 0 8px 0;
    color:#0f2b68;
    font-size:19px;
    font-weight:800;
}
.action-card-text {
    margin:0 0 16px 0;
    color:#667085;
    font-size:13px;
    line-height:1.45;
    min-height:58px;
}
.action-link {
    display:inline-block;
    background:linear-gradient(90deg,#4f46e5,#2563eb);
    color:white !important;
    text-decoration:none !important;
    padding:10px 14px;
    border-radius:12px;
    font-weight:800;
    font-size:13px;
    box-shadow:0 10px 22px rgba(37,99,235,.22);
}
.action-link.purple {
    background:linear-gradient(90deg,#6d28d9,#7c3aed);
}
.action-link.disabled {
    background:#e5e7eb;
    color:#667085 !important;
    box-shadow:none;
    pointer-events:none;
}
</style>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.markdown('<div class="action-card-title">Executive Dashboard</div>', unsafe_allow_html=True)
            st.markdown('<div class="action-card-text">Open the leadership-ready dashboard with KPIs, region comparison, heatmaps and drilldowns.</div>', unsafe_allow_html=True)
            link_class = "action-link" if has_report else "action-link disabled"
            st.markdown(f'<a class="{link_class}" href="{dashboard_href}" target="_self">Open Dashboard ↗</a>', unsafe_allow_html=True)

    with c2:
        with st.container(border=True):
            st.markdown('<div class="action-card-title">Excel Report</div>', unsafe_allow_html=True)
            st.markdown('<div class="action-card-text">Download the generated workbook with Insights, APIs, Transactions, Errors and Comparison sheets.</div>', unsafe_allow_html=True)
            if has_report:
                st.download_button(
                    "⬇ Download Excel Report",
                    data=st.session_state.excel_bytes,
                    file_name=st.session_state.report_file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="excel_download_inside_card",
                    use_container_width=True,
                )
            else:
                st.button("⬇ Download Excel Report", disabled=True, use_container_width=True, key="excel_download_disabled_inside_card")

    with c3:
        with st.container(border=True):
            st.markdown('<div class="action-card-title">AI Chatbot</div>', unsafe_allow_html=True)
            st.markdown('<div class="action-card-text">Open the dashboard chatbot and ask questions about SLA, slow APIs, errors, regions and comparisons.</div>', unsafe_allow_html=True)
            link_class = "action-link purple" if has_report else "action-link disabled"
            st.markdown(f'<a class="{link_class}" href="{chatbot_href}" target="_self">Open Chatbot ↗</a>', unsafe_allow_html=True)

# Session state
if "excel_bytes" not in st.session_state: st.session_state.excel_bytes = None
if "run_frames" not in st.session_state: st.session_state.run_frames = []
if "report_file_name" not in st.session_state: st.session_state.report_file_name = "JMeter_Report.xlsx"
if "messages" not in st.session_state: st.session_state.messages = []
if "run_id" not in st.session_state: st.session_state.run_id = ""
if "team_authenticated" not in st.session_state: st.session_state.team_authenticated = False

if dashboard_only and run_id and run_id in dashboard_store:
    st.session_state.run_frames = dashboard_store[run_id]["run_frames"]
    st.session_state.excel_bytes = dashboard_store[run_id].get("excel_bytes")
    st.session_state.report_file_name = dashboard_store[run_id].get("report_file_name", "JMeter_Report.xlsx")

if dashboard_only:
    if not st.session_state.run_frames:
        load_static_saved_dashboard()
    if st.session_state.run_frames:
        render_executive_dashboard(st.session_state.run_frames)
    else:
        render_management_landing_page()
elif team_upload_view:
    if not st.session_state.get("team_authenticated", False):
        render_main_page(show_subtitle=st.session_state.get("team_authenticated", False))
    access_granted = team_upload_access_granted()
    if access_granted:
        upload_left_page = render_upload_left_panel()
        if render_upload_sidebar_page(upload_left_page):
            st.stop()
        st.markdown('<div class="clean-upload-page-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title upload-program-title">Program Track Uploads</div>', unsafe_allow_html=True)
        api_col, ui_col = st.columns(2, gap="medium")
        cloud_col, inv_col = st.columns(2, gap="medium")

        with api_col:
            with st.container(border=True):
                st.markdown("**API Metrics (.json)**")
                uploaded_files = st.file_uploader(
                    "Upload JMeter statistics.json file(s)",
                    type=["json"],
                    accept_multiple_files=True,
                    key="api_json_uploader",
                )
                st.checkbox(
                    "Save for team visibility",
                    value=True,
                    key="save_reports_checkbox",
                )
                generate_clicked = st.button(
                    "Generate API Results",
                    type="primary",
                    disabled=not uploaded_files,
                    key="generate_api_results",
                    use_container_width=True,
                )

        if uploaded_files and generate_clicked:
            if st.session_state.get('save_reports_checkbox', True):
                save_uploaded_files_to_latest(uploaded_files)
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                json_paths: List[Path] = []
                labels: List[str] = []
                run_frames: List[Dict[str, pd.DataFrame]] = []
                for idx, uploaded_file in enumerate(uploaded_files, start=1):
                    clean_name = uploaded_file.name.replace(" ", "_")
                    path = tmpdir / f"{idx}_{clean_name}"
                    path.write_bytes(uploaded_file.getvalue())
                    json_paths.append(path)
                    label = Path(uploaded_file.name).stem
                    labels.append(label)
                    run_frames.append(process_uploaded_file(path, label))
                output_path = tmpdir / "JMeter_Report.xlsx"
                try:
                    if len(json_paths) == 1:
                        build_report(json_paths[0], output_path)
                    else:
                        build_comparison_report(json_paths, labels, output_path)
                    run_frames = add_region_to_frames(run_frames)
                    excel_bytes = output_path.read_bytes()
                    new_run_id = uuid.uuid4().hex
                    dashboard_store[new_run_id] = {"run_frames": run_frames, "excel_bytes": excel_bytes, "report_file_name": "JMeter_Report.xlsx"}
                    st.session_state.excel_bytes = excel_bytes
                    st.session_state.run_frames = run_frames
                    st.session_state.report_file_name = "JMeter_Report.xlsx"
                    st.session_state.excel_api_only = True
                    st.session_state.messages = []
                    st.session_state.run_id = new_run_id
                    st.toast("Report generated successfully.", icon="✅")
                    st.success("Dashboard generated. Share the dashboard link below with management.")
                    st.markdown(f'<a class="primary-pill" href="{dashboard_url_for_run(new_run_id)}" target="_blank">Open Results Dashboard ↗</a>', unsafe_allow_html=True)
                    st.info("Dashboard, Excel Report, and AI Chatbot are now available from the left panel.")
                except Exception as exc:
                    st.error(f"Failed to generate report: {exc}")

        with ui_col:
            with st.container(border=True):
                st.markdown("**UI Metrics (.csv)**")
                ui_files = st.file_uploader("Upload UI CSV files", type=["csv"], accept_multiple_files=True, key="ui_csv_uploader")
                st.checkbox("Save for team visibility", value=True, key="save_ui_reports_checkbox")
                if st.button("Generate UI Results", key="generate_ui_results", type="primary", use_container_width=True, disabled=not ui_files):
                    if st.session_state.get("save_ui_reports_checkbox", True):
                        save_uploaded_files_for_track(ui_files, TRACK_UI)
                    generate_dashboard_from_uploaded_csv_files(TRACK_UI, ui_files)
                    st.success("Generated UI dashboard and report. Dashboard, Excel Report, and AI Chatbot are now available from the left panel.")
                    st.session_state.upload_left_page = "Dashboard"
                    st.rerun()

        with cloud_col:
            with st.container(border=True):
                st.markdown("**Cloud Assist Connector (.csv)**")
                cloud_files = st.file_uploader("Upload Cloud Assist CSV files", type=["csv"], accept_multiple_files=True, key="cloud_csv_uploader")
                st.checkbox("Save for team visibility", value=True, key="save_cloud_reports_checkbox")
                if st.button("Generate Cloud Results", key="generate_cloud_results", type="primary", use_container_width=True, disabled=not cloud_files):
                    if st.session_state.get("save_cloud_reports_checkbox", True):
                        save_uploaded_files_for_track(cloud_files, TRACK_CLOUD)
                    generate_dashboard_from_uploaded_csv_files(TRACK_CLOUD, cloud_files)
                    st.success("Generated Cloud Assist dashboard and report. Dashboard, Excel Report, and AI Chatbot are now available from the left panel.")
                    st.session_state.upload_left_page = "Dashboard"
                    st.rerun()

        with inv_col:
            with st.container(border=True):
                st.markdown("**Customer Inventory Benchmarking (.csv)**")
                inv_files = st.file_uploader("Upload Customer Inventory Benchmarking CSV files", type=["csv"], accept_multiple_files=True, key="inv_csv_uploader")
                st.checkbox("Save for team visibility", value=True, key="save_inventory_reports_checkbox")
                if st.button("Generate Inventory Results", key="generate_inventory_results", type="primary", use_container_width=True, disabled=not inv_files):
                    if st.session_state.get("save_inventory_reports_checkbox", True):
                        save_uploaded_files_for_track(inv_files, TRACK_INVENTORY)
                    generate_dashboard_from_uploaded_csv_files(TRACK_INVENTORY, inv_files)
                    st.success("Generated Customer Inventory Benchmarking dashboard and report. Dashboard, Excel Report, and AI Chatbot are now available from the left panel.")
                    st.session_state.upload_left_page = "Dashboard"
                    st.rerun()

else:
    if st.session_state.run_frames:
        render_executive_dashboard(st.session_state.run_frames)
    else:
        render_management_landing_page()
