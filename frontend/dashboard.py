"""
FinScope AI — Premium Interactive Dashboard
Run: streamlit run frontend/dashboard.py
"""
import streamlit as st
import requests
import json
import time
from styles import CUSTOM_CSS, BG_ORBS

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="FinScope AI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(BG_ORBS, unsafe_allow_html=True)

# ── API Helpers ───────────────────────────────────────
def api(method, path, body=None):
    try:
        fn = {"get": requests.get, "post": requests.post, "patch": requests.patch, "delete": requests.delete}[method]
        r = fn(f"{API_BASE}{path}", json=body, timeout=30) if body else fn(f"{API_BASE}{path}", timeout=15)
        return r.status_code, r.json()
    except Exception as e:
        return None, {"error": str(e)}

def backend_ok():
    c, _ = api("get", "/health")
    return c == 200

def sbadge(status):
    m = {"completed": ("badge-ok", "COMPLETED"), "researching": ("badge-run", "RESEARCHING"),
         "awaiting_approval": ("badge-wait", "AWAITING APPROVAL"), "failed": ("badge-err", "FAILED")}
    cls, label = m.get(status, ("badge-wait", status.upper()))
    return f'<span class="badge {cls}">{label}</span>'

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div class="sidebar-brand">
        <div class="sidebar-logo">📊</div>
        <div class="sidebar-name">FinScope AI</div>
        <div class="sidebar-tag">Deep Financial Research</div>
    </div>""", unsafe_allow_html=True)

    page = st.radio("", ["🏠 Home", "🔍 New Research", "📋 Track Session", "📄 Report Viewer"],
                     label_visibility="collapsed")
    st.divider()
    alive = backend_ok()
    st.markdown(f"{'🟢' if alive else '🔴'} **{'Online' if alive else 'Offline'}** — `{API_BASE}`")

# ══════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("""<div class="hero">
        <div class="hero-logo">📊</div>
        <h1>FinScope AI</h1>
        <p class="hero-sub">AI-powered deep financial research for IT & Pharma sectors</p>
    </div>""", unsafe_allow_html=True)

    # Bento grid
    st.markdown("""<div class="bento">
        <div class="bento-card"><div class="bento-icon">🧠</div>
            <div class="bento-title">Claude AI Engine</div>
            <div class="bento-desc">Powered by Anthropic Claude for intelligent query classification & research planning</div></div>
        <div class="bento-card"><div class="bento-icon">🔬</div>
            <div class="bento-title">Multi-Step Research</div>
            <div class="bento-desc">5–20 iterative research steps with memory, deduplication & confidence scoring</div></div>
        <div class="bento-card"><div class="bento-icon">⚡</div>
            <div class="bento-title">Live SSE Streaming</div>
            <div class="bento-desc">Real-time Server-Sent Events stream each finding as it happens</div></div>
        <div class="bento-card"><div class="bento-icon">📈</div>
            <div class="bento-title">Financial APIs</div>
            <div class="bento-desc">yfinance for live stock data, Tavily for web research, calculator tools</div></div>
        <div class="bento-card"><div class="bento-icon">📑</div>
            <div class="bento-title">Structured Reports</div>
            <div class="bento-desc">Professional reports with sections, metrics, risk factors & citations</div></div>
        <div class="bento-card"><div class="bento-icon">💾</div>
            <div class="bento-title">Supabase Persistence</div>
            <div class="bento-desc">Every session, step & report saved to PostgreSQL for full history</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### 🎯 How It Works")
        flow = ["Submit a financial query", "AI classifies the sector (IT / Pharma)",
                "Research plan is generated", "You review & approve the plan",
                "Agent executes multi-step research", "Live findings stream to you",
                "Final structured report generated"]
        for i, s in enumerate(flow, 1):
            st.markdown(f"**{i}.** {s}")
    with c2:
        st.markdown("#### 💡 Try These Queries")
        examples = [
            "Analyze Infosys financial performance and AI strategy 2025",
            "Sun Pharma drug pipeline and FDA approval status",
            "Compare TCS vs Wipro vs HCL Technologies",
            "Cipla biosimilar revenue and R&D investment outlook",
            "Tech Mahindra cloud transformation and deal pipeline",
        ]
        for q in examples:
            st.markdown(f'<span class="example-chip">{q}</span>', unsafe_allow_html=True)

    if not alive:
        st.error("⚠️ Backend offline — run `uvicorn src.main:app --reload --port 8000`")

# ══════════════════════════════════════════════════════
# NEW RESEARCH
# ══════════════════════════════════════════════════════
elif page == "🔍 New Research":
    st.markdown("## 🔍 Start New Research")
    if not alive:
        st.error("Backend offline."); st.stop()

    # Sector picker
    st.markdown("#### Pick a sector focus")
    st.markdown("""<div class="sector-grid">
        <div class="sector-card sector-it">
            <div class="sector-icon">💻</div>
            <div class="sector-name">IT Sector</div>
            <div class="sector-desc">TCS • Infosys • Wipro • HCL • Tech Mahindra</div>
        </div>
        <div class="sector-card sector-pharma">
            <div class="sector-icon">💊</div>
            <div class="sector-name">Pharma Sector</div>
            <div class="sector-desc">Sun Pharma • Cipla • Dr Reddy's • Biocon</div>
        </div>
    </div>""", unsafe_allow_html=True)

    with st.form("research_form"):
        query = st.text_area("Research Query", height=90,
                             placeholder="e.g. Analyze Infosys financial performance and AI strategy in 2025")
        c1, c2 = st.columns(2)
        with c1:
            user_id = st.text_input("User ID", value="user_001")
        with c2:
            depth = st.selectbox("Depth", ["standard", "quick", "deep"],
                                 help="quick=5, standard=10, deep=20 steps")
        submitted = st.form_submit_button("🚀 Launch Research", use_container_width=True, type="primary")

    if submitted:
        if len(query.strip()) < 10:
            st.error("Query must be at least 10 characters."); st.stop()
        with st.spinner("🧠 Classifying sector & generating plan..."):
            code, data = api("post", "/query/", {"query": query.strip(), "user_id": user_id.strip(), "depth": depth})
        if code == 202:
            sid = data.get("session_id", "")
            plan = data.get("plan", {})
            st.session_state["active_session"] = sid

            st.success(f"Session created: `{sid}`")
            st.markdown(f"**Sector:** {data.get('sector', '')} &nbsp;&nbsp; **Depth:** {depth}")

            st.markdown("#### 📋 Research Plan")
            for i, step in enumerate(plan.get("planned_steps", []), 1):
                st.markdown(f"`{i}.` {step}")

            st.divider()
            if st.button("✅ Approve & Start", use_container_width=True, type="primary"):
                c2, d2 = api("patch", f"/sessions/{sid}/approve")
                if c2 == 200:
                    st.success("🚀 Research started! Go to **Track Session**.")
                else:
                    st.error(f"Approval failed: {d2}")
        elif code == 422:
            detail = data.get("detail", {})
            st.error(f"Out of scope: {detail.get('message', '')}")
            for s in detail.get("suggested_queries", []):
                st.markdown(f'<span class="example-chip">{s}</span>', unsafe_allow_html=True)
        elif code is None:
            st.error(f"Connection error: {data.get('error')}")
        else:
            st.error(f"Error {code}: {data}")

# ══════════════════════════════════════════════════════
# TRACK SESSION
# ══════════════════════════════════════════════════════
elif page == "📋 Track Session":
    st.markdown("## 📋 Track Research Session")
    default_sid = st.session_state.get("active_session", "")
    sid = st.text_input("Session ID", value=default_sid, placeholder="Paste session ID")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        refresh = st.button("🔄 Refresh", use_container_width=True)
    with c2:
        auto = st.toggle("Auto-refresh")
    with c3:
        if sid and st.button("🗑️ Delete"):
            api("delete", f"/sessions/{sid}")
            st.success("Deleted")

    if auto and sid:
        time.sleep(5); st.rerun()

    if sid:
        code, data = api("get", f"/sessions/{sid}")
        if code == 200:
            status = data.get("status", "unknown")
            done = data.get("steps_completed", 0)
            total = data.get("max_steps", 10)
            pct = data.get("progress_pct", 0)

            # Metric row
            mc = st.columns(4)
            items = [
                ("Status", sbadge(status), ""),
                ("Sector", f'<span class="badge badge-run">{data.get("sector","")}</span>', ""),
                ("Steps", f'<span class="metric-num blue">{done}/{total}</span>', "COMPLETED"),
                ("Progress", f'<span class="metric-num green">{pct}%</span>', "DONE"),
            ]
            for col, (lbl, val, sub) in zip(mc, items):
                with col:
                    st.markdown(f'<div class="metric-pill">{val}<div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

            st.progress(min(pct / 100, 1.0))
            st.markdown(f"**Query:** _{data.get('original_query','')}_")

            if status == "awaiting_approval":
                if st.button("✅ Approve Research Plan", use_container_width=True, type="primary"):
                    api("patch", f"/sessions/{sid}/approve")
                    st.success("Approved!"); st.rerun()

            # Timeline
            steps = data.get("steps", [])
            if steps:
                st.markdown(f"#### 🔬 Research Timeline ({len(steps)} steps)")
                st.markdown('<div class="timeline">', unsafe_allow_html=True)
                for i, step in enumerate(steps):
                    conf = step.get("confidence", 0)
                    cpct = int(conf * 100)
                    cclr = "#34d399" if conf >= 0.75 else "#fbbf24" if conf >= 0.5 else "#f87171"
                    delay = i * 0.1
                    st.markdown(f"""
                    <div class="tl-step" style="animation-delay:{delay}s">
                        <div class="tl-dot{'  active' if i == len(steps)-1 else ''}"></div>
                        <div class="tl-head">
                            <span class="tl-query">Step {step.get('step_number',i+1)}: {step.get('query','')[:70]}</span>
                            <span class="tl-tool">{step.get('tool_used','')}</span>
                        </div>
                        <div class="tl-finding">{step.get('finding','')[:250]}</div>
                        <div class="tl-conf-bar"><div class="tl-conf-fill" style="width:{cpct}%;background:{cclr}"></div></div>
                        <div style="text-align:right;margin-top:2px"><span style="color:{cclr};font-size:0.7rem;font-family:'JetBrains Mono'">{cpct}%</span></div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            elif status == "researching":
                st.info("🔬 Research running... toggle auto-refresh to see live steps.")

            if status == "completed":
                st.balloons()
                st.success("✅ Research complete!")
                if st.button("📄 View Report →", use_container_width=True, type="primary"):
                    st.session_state["report_session"] = sid
        elif code == 404:
            st.error("Session not found.")
        elif code is None:
            st.error(f"Connection error: {data.get('error')}")
        else:
            st.error(f"Error {code}: {data}")

# ══════════════════════════════════════════════════════
# REPORT VIEWER
# ══════════════════════════════════════════════════════
elif page == "📄 Report Viewer":
    st.markdown("## 📄 Research Report")
    dsid = st.session_state.get("report_session", "")
    sid = st.text_input("Session ID", value=dsid)

    if sid and st.button("📥 Load Report", use_container_width=True):
        code, data = api("get", f"/sessions/{sid}/report")
        if code == 200:
            st.session_state["rpt"] = data
            st.session_state["rpt_sid"] = sid
        elif code == 202:
            d = data.get("detail", {})
            st.warning(f"⏳ Still researching — {d.get('steps_done',0)}/{d.get('total_steps',10)} done")
        else:
            st.error(f"Error {code}: {data}")

    rpt = st.session_state.get("rpt")
    if rpt:
        cavg = int(rpt.get("confidence_avg", 0) * 100)
        secs = rpt.get("sections", [])
        risks = rpt.get("risk_factors", [])
        cites = rpt.get("citations", [])

        mc = st.columns(4)
        vals = [(f"{cavg}%", "blue", "AVG CONFIDENCE"), (str(len(secs)), "purple", "SECTIONS"),
                (str(len(risks)), "amber", "RISK FACTORS"), (str(len(cites)), "green", "CITATIONS")]
        for col, (v, c, l) in zip(mc, vals):
            with col:
                st.markdown(f'<div class="metric-pill"><div class="metric-num {c}">{v}</div><div class="metric-lbl">{l}</div></div>', unsafe_allow_html=True)

        # Executive Summary
        st.markdown(f"""<div class="report-block"><h4>📌 Executive Summary</h4>
            <p style="color:#cbd5e1;line-height:1.7">{rpt.get('executive_summary','N/A')}</p></div>""", unsafe_allow_html=True)

        # Sections
        for sec in secs:
            with st.expander(f"📑 {sec.get('title','Section')}", expanded=True):
                st.markdown(sec.get("content", ""))
                dps = sec.get("data_points", [])
                if dps:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(dps), use_container_width=True)

        # Key Metrics
        km = rpt.get("key_metrics", {})
        if km:
            st.markdown("#### 📊 Key Metrics")
            cols = st.columns(min(len(km), 4))
            for i, (k, v) in enumerate(km.items()):
                with cols[i % len(cols)]:
                    st.metric(k, str(v))

        # Outlook
        if rpt.get("investment_outlook"):
            st.markdown(f"""<div class="report-block"><h4>📈 Investment Outlook</h4>
                <p style="color:#cbd5e1">{rpt['investment_outlook']}</p></div>""", unsafe_allow_html=True)

        # Risk Factors
        if risks:
            st.markdown("#### ⚠️ Risk Factors")
            for r in risks:
                st.markdown(f"- 🔴 {r}")

        # Citations
        if cites:
            with st.expander("🔗 Sources & Citations"):
                for c in cites:
                    u = c.get("url", "")
                    if u: st.markdown(f"- [{u}]({u})")

        # Export
        st.divider()
        md = rpt.get("markdown_export", "")
        if md:
            st.download_button("⬇️ Download Markdown", data=md,
                               file_name=f"finscope_{st.session_state.get('rpt_sid','report')[:8]}.md",
                               mime="text/markdown", use_container_width=True)
