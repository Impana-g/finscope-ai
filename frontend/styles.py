"""Premium CSS styles for FinScope AI Dashboard"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ──────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

.main { background: #06080f; }
.block-container { max-width: 1100px; padding-top: 1rem; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080c18 0%, #0c1020 100%);
    border-right: 1px solid rgba(96, 165, 250, 0.08);
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }

/* ── Animated Background Orbs ─────────────────────── */
.bg-orbs {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    pointer-events: none; z-index: 0; overflow: hidden;
}
.orb {
    position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.12;
    animation: orbFloat 12s ease-in-out infinite;
}
.orb-1 { width: 500px; height: 500px; background: #3b82f6; top: -10%; left: -5%; animation-delay: 0s; }
.orb-2 { width: 400px; height: 400px; background: #8b5cf6; top: 40%; right: -10%; animation-delay: -4s; }
.orb-3 { width: 350px; height: 350px; background: #06b6d4; bottom: -5%; left: 30%; animation-delay: -8s; }

@keyframes orbFloat {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(30px, -40px) scale(1.05); }
    66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* ── Glass Card ───────────────────────────────────── */
.glass {
    background: rgba(15, 20, 40, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(96, 165, 250, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass:hover {
    border-color: rgba(96, 165, 250, 0.25);
    box-shadow: 0 8px 32px rgba(96, 165, 250, 0.08);
    transform: translateY(-2px);
}

/* ── Hero ──────────────────────────────────────────── */
.hero {
    text-align: center; padding: 3rem 1rem 2rem;
    position: relative;
}
.hero-logo {
    font-size: 3rem; margin-bottom: 0.5rem;
    animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.08); }
}
.hero h1 {
    font-size: 3rem; font-weight: 700; margin: 0;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 40%, #34d399 80%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: gradShift 6s ease infinite;
    background-size: 200% 200%;
}
@keyframes gradShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}
.hero-sub {
    color: #64748b; font-size: 1rem; margin-top: 0.3rem;
    letter-spacing: 0.5px;
}

/* ── Sector Picker Cards ──────────────────────────── */
.sector-grid { display: flex; gap: 1rem; margin: 1rem 0; }
.sector-card {
    flex: 1; padding: 1.5rem; border-radius: 16px; cursor: pointer;
    text-align: center; transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative; overflow: hidden;
}
.sector-card::before {
    content: ''; position: absolute; inset: 0; border-radius: 16px;
    background: inherit; opacity: 0; transition: opacity 0.3s;
}
.sector-card:hover { transform: translateY(-4px) scale(1.02); }
.sector-card:hover::before { opacity: 1; }

.sector-it {
    background: linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(59,130,246,0.05) 100%);
    border: 1px solid rgba(59,130,246,0.2);
}
.sector-it:hover { border-color: rgba(59,130,246,0.5); box-shadow: 0 0 30px rgba(59,130,246,0.15); }

.sector-pharma {
    background: linear-gradient(135deg, rgba(139,92,246,0.15) 0%, rgba(139,92,246,0.05) 100%);
    border: 1px solid rgba(139,92,246,0.2);
}
.sector-pharma:hover { border-color: rgba(139,92,246,0.5); box-shadow: 0 0 30px rgba(139,92,246,0.15); }

.sector-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.sector-name { font-size: 1.1rem; font-weight: 600; color: #e2e8f0; }
.sector-desc { font-size: 0.75rem; color: #64748b; margin-top: 0.3rem; }

/* ── Metric Pill ──────────────────────────────────── */
.metric-pill {
    background: rgba(15, 20, 40, 0.7);
    border: 1px solid rgba(96, 165, 250, 0.12);
    border-radius: 12px; padding: 1rem; text-align: center;
    transition: all 0.3s;
}
.metric-pill:hover {
    border-color: rgba(96, 165, 250, 0.3);
    transform: translateY(-2px);
}
.metric-num {
    font-size: 1.6rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.metric-num.blue { color: #60a5fa; }
.metric-num.green { color: #34d399; }
.metric-num.purple { color: #a78bfa; }
.metric-num.amber { color: #fbbf24; }
.metric-lbl { color: #475569; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 0.2rem; }

/* ── Timeline Step ────────────────────────────────── */
.timeline { position: relative; padding-left: 2rem; }
.timeline::before {
    content: ''; position: absolute; left: 0.6rem; top: 0; bottom: 0;
    width: 2px; background: linear-gradient(180deg, #3b82f6, #8b5cf6, #06b6d4);
}
.tl-step {
    position: relative; margin-bottom: 1rem; padding: 1rem 1.2rem;
    background: rgba(15, 20, 40, 0.5);
    border: 1px solid rgba(96, 165, 250, 0.08);
    border-radius: 12px; transition: all 0.3s;
    animation: fadeSlideIn 0.5s ease-out forwards;
    opacity: 0;
}
.tl-step:hover { border-color: rgba(96, 165, 250, 0.2); transform: translateX(4px); }
.tl-dot {
    position: absolute; left: -1.65rem; top: 1.2rem;
    width: 10px; height: 10px; border-radius: 50%;
    background: #3b82f6; border: 2px solid #0f172a;
    box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}
.tl-dot.active { animation: dotPulse 1.5s ease-in-out infinite; }
@keyframes dotPulse {
    0%, 100% { box-shadow: 0 0 4px rgba(59,130,246,0.4); }
    50% { box-shadow: 0 0 16px rgba(59,130,246,0.8); }
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
}

.tl-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }
.tl-query { color: #e2e8f0; font-weight: 500; font-size: 0.9rem; }
.tl-tool {
    background: rgba(59,130,246,0.15); color: #60a5fa;
    padding: 2px 10px; border-radius: 999px;
    font-size: 0.7rem; font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}
.tl-finding { color: #94a3b8; font-size: 0.82rem; line-height: 1.5; }
.tl-conf-bar {
    height: 4px; border-radius: 999px; margin-top: 0.5rem;
    background: rgba(255,255,255,0.05); overflow: hidden;
}
.tl-conf-fill { height: 100%; border-radius: 999px; transition: width 1s ease-out; }

/* ── Status Badge ─────────────────────────────────── */
.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 14px; border-radius: 999px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
}
.badge::before {
    content: ''; width: 6px; height: 6px; border-radius: 50%;
}
.badge-ok { background: rgba(52,211,153,0.12); color: #34d399; }
.badge-ok::before { background: #34d399; }
.badge-run { background: rgba(59,130,246,0.12); color: #60a5fa; }
.badge-run::before { background: #60a5fa; animation: dotPulse 1.5s infinite; }
.badge-wait { background: rgba(251,191,36,0.12); color: #fbbf24; }
.badge-wait::before { background: #fbbf24; }
.badge-err { background: rgba(248,113,113,0.12); color: #f87171; }
.badge-err::before { background: #f87171; }

/* ── Report Section ───────────────────────────────── */
.report-block {
    background: rgba(15, 20, 40, 0.5);
    border: 1px solid rgba(96, 165, 250, 0.08);
    border-radius: 14px; padding: 1.5rem; margin: 0.8rem 0;
    transition: all 0.3s;
}
.report-block:hover { border-color: rgba(96, 165, 250, 0.18); }
.report-block h4 {
    color: #60a5fa; margin: 0 0 0.8rem; font-size: 1rem;
    display: flex; align-items: center; gap: 0.5rem;
}

/* ── Feature Bento Grid ───────────────────────────── */
.bento { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; margin: 1.5rem 0; }
.bento-card {
    background: rgba(15, 20, 40, 0.5);
    border: 1px solid rgba(96, 165, 250, 0.08);
    border-radius: 14px; padding: 1.3rem;
    transition: all 0.35s;
}
.bento-card:hover { border-color: rgba(96,165,250,0.25); transform: translateY(-3px); }
.bento-icon { font-size: 1.8rem; margin-bottom: 0.5rem; }
.bento-title { font-size: 0.9rem; font-weight: 600; color: #e2e8f0; }
.bento-desc { font-size: 0.75rem; color: #64748b; margin-top: 0.3rem; line-height: 1.4; }

/* ── Sidebar Brand ────────────────────────────────── */
.sidebar-brand {
    text-align: center; padding: 1.5rem 0 1rem;
    border-bottom: 1px solid rgba(96,165,250,0.08);
    margin-bottom: 1rem;
}
.sidebar-logo {
    width: 48px; height: 48px; margin: 0 auto 0.5rem;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border-radius: 14px; display: flex; align-items: center;
    justify-content: center; font-size: 1.5rem;
    animation: pulse 3s ease-in-out infinite;
}
.sidebar-name { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; }
.sidebar-tag { font-size: 0.65rem; color: #475569; letter-spacing: 1px; text-transform: uppercase; }

/* ── Query Examples ───────────────────────────────── */
.example-chip {
    display: inline-block; padding: 6px 14px; margin: 3px;
    background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.15);
    border-radius: 999px; color: #94a3b8; font-size: 0.8rem;
    cursor: pointer; transition: all 0.25s;
}
.example-chip:hover {
    background: rgba(59,130,246,0.18); border-color: rgba(59,130,246,0.35);
    color: #e2e8f0;
}

/* ── Scrollbar ────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }

/* ── Button Override ──────────────────────────────── */
.stButton>button {
    border-radius: 12px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s !important;
}
.stButton>button:hover { transform: translateY(-1px) !important; }
</style>
"""

BG_ORBS = """
<div class="bg-orbs">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
</div>
"""
