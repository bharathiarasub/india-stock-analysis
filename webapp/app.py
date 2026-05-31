import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json, os, time, requests

try:
    from nsepython import nse_eq, nse_eq_history
    NSE_AVAILABLE = True
except Exception:
    NSE_AVAILABLE = False

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Top 25 — Stock Analysis",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Static ticker/link metadata (never changes) ───────────────────────────────
TICKER_META = {
    "HDFC Bank":                    {"ticker": "HDFCBANK.NS",   "sector": "Banking",       "screener": "HDFCBANK",     "mc": "hdfc-bank"},
    "Bajaj Finance":                {"ticker": "BAJFINANCE.NS", "sector": "NBFC",           "screener": "BAJFINANCE",   "mc": "bajaj-finance"},
    "Hindustan Unilever":           {"ticker": "HINDUNILVR.NS", "sector": "Consumer",       "screener": "HINDUNILVR",   "mc": "hindustan-unilever"},
    "Maruti Suzuki India":          {"ticker": "MARUTI.NS",     "sector": "Automobile",     "screener": "MARUTI",       "mc": "maruti-suzuki-india"},
    "UltraTech Cement":             {"ticker": "ULTRACEMCO.NS", "sector": "Infrastructure", "screener": "ULTRACEMCO",   "mc": "ultratech-cement"},
    "Bharti Airtel":                {"ticker": "BHARTIARTL.NS", "sector": "Telecom",        "screener": "BHARTIARTL",   "mc": "bharti-airtel"},
    "ICICI Bank":                   {"ticker": "ICICIBANK.NS",  "sector": "Banking",        "screener": "ICICIBANK",    "mc": "icici-bank"},
    "JSW Steel":                    {"ticker": "JSWSTEEL.NS",   "sector": "Metals",         "screener": "JSWSTEEL",     "mc": "jsw-steel"},
    "NTPC Limited":                 {"ticker": "NTPC.NS",       "sector": "Energy",         "screener": "NTPC",         "mc": "ntpc"},
    "Larsen & Toubro":              {"ticker": "LT.NS",         "sector": "Infrastructure", "screener": "LT",           "mc": "larsen-and-toubro"},
    "Larsen and Toubro":            {"ticker": "LT.NS",         "sector": "Infrastructure", "screener": "LT",           "mc": "larsen-and-toubro"},
    "Titan Company":                {"ticker": "TITAN.NS",      "sector": "Consumer",       "screener": "TITAN",        "mc": "titan-company"},
    "State Bank of India":          {"ticker": "SBIN.NS",       "sector": "Banking",        "screener": "SBIN",         "mc": "state-bank-of-india"},
    "Sun Pharmaceutical":           {"ticker": "SUNPHARMA.NS",  "sector": "Pharma",         "screener": "SUNPHARMA",    "mc": "sun-pharmaceutical-industries"},
    "Tata Consultancy Services":    {"ticker": "TCS.NS",        "sector": "IT",             "screener": "TCS",          "mc": "tata-consultancy-services"},
    "Infosys":                      {"ticker": "INFY.NS",       "sector": "IT",             "screener": "INFY",         "mc": "infosys"},
    "Reliance Industries":          {"ticker": "RELIANCE.NS",   "sector": "Conglomerate",   "screener": "RELIANCE",     "mc": "reliance-industries"},
    "Kotak Mahindra Bank":          {"ticker": "KOTAKBANK.NS",  "sector": "Banking",        "screener": "KOTAKBANK",    "mc": "kotak-mahindra-bank"},
    "Axis Bank":                    {"ticker": "AXISBANK.NS",   "sector": "Banking",        "screener": "AXISBANK",     "mc": "axis-bank"},
    "ITC":                          {"ticker": "ITC.NS",        "sector": "Consumer",       "screener": "ITC",          "mc": "itc"},
    "Mahindra & Mahindra":          {"ticker": "M&M.NS",        "sector": "Automobile",     "screener": "M&M",          "mc": "mahindra-and-mahindra"},
    "Adani Ports & SEZ":            {"ticker": "ADANIPORTS.NS", "sector": "Infrastructure", "screener": "ADANIPORTS",   "mc": "adani-ports-and-sez"},
    "Oil & Natural Gas Corp":       {"ticker": "ONGC.NS",       "sector": "Energy",         "screener": "ONGC",         "mc": "oil-and-natural-gas-corporation"},
    "Adani Enterprises":            {"ticker": "ADANIENT.NS",   "sector": "Conglomerate",   "screener": "ADANIENT",     "mc": "adani-enterprises"},
    "Adani Power":                  {"ticker": "ADANIPOWER.NS", "sector": "Energy",         "screener": "ADANIPOWER",   "mc": "adani-power"},
}

# ── Load AI ranking from JSON (updated daily by crew) ─────────────────────────
JSON_PATH = os.path.join(os.path.dirname(__file__), "../output/ranking.json")

def load_ai_data():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH) as f:
            data = json.load(f)
        companies = []
        for c in data.get("top_companies", []):
            meta = TICKER_META.get(c["name"], {
                "ticker": "", "sector": "Unknown", "screener": "", "mc": ""
            })
            companies.append({**c, **meta})
        portfolio = data.get("portfolio", [])
        generated = data.get("generated_date", "Unknown")
        return companies, portfolio, generated
    return [], [], "Not yet generated"

AI_COMPANIES, AI_PORTFOLIO, AI_GENERATED = load_ai_data()

# ── Fallback static data (shown if JSON not yet generated) ────────────────────
COMPANIES = AI_COMPANIES if AI_COMPANIES else [
    {"rank": 1,  "name": "HDFC Bank",                      "ticker": "HDFCBANK.NS",    "sector": "Banking",         "score": 43, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Moderate",    "thesis": "Strong fundamentals and leading market position in Indian banking.", "key_risk": "Regulatory risk related to RBI policies.", "screener": "HDFCBANK", "mc": "hdfc-bank"},
    {"rank": 2,  "name": "Bajaj Finance",                   "ticker": "BAJFINANCE.NS",  "sector": "NBFC",            "score": 43, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "High growth potential in lending, benefiting from fintech trends.", "key_risk": "Regulatory constraints from RBI on lending.", "screener": "BAJFINANCE", "mc": "bajaj-finance"},
    {"rank": 3,  "name": "Hindustan Unilever",              "ticker": "HINDUNILVR.NS",  "sector": "Consumer",        "score": 42, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Conservative","thesis": "Strong brand portfolio with resilience in consumer products.", "key_risk": "Competition from emerging local brands.", "screener": "HINDUNILVR", "mc": "hindustan-unilever"},
    {"rank": 4,  "name": "Maruti Suzuki India",             "ticker": "MARUTI.NS",      "sector": "Automobile",      "score": 42, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "Leading player in auto sector with strong demand recovery.", "key_risk": "Emission regulations and EV competition.", "screener": "MARUTI", "mc": "maruti-suzuki-india"},
    {"rank": 5,  "name": "UltraTech Cement",                "ticker": "ULTRACEMCO.NS",  "sector": "Infrastructure",  "score": 38, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Moderate",    "thesis": "Key player in cement with growth linkages to infrastructure development.", "key_risk": "Fluctuations in construction demand.", "screener": "ULTRACEMCO", "mc": "ultratech-cement"},
    {"rank": 6,  "name": "Bharti Airtel",                   "ticker": "BHARTIARTL.NS",  "sector": "Telecom",         "score": 38, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "Strong telecom infrastructure and diversified services.", "key_risk": "Pricing wars in the telecom sector.", "screener": "BHARTIARTL", "mc": "bharti-airtel"},
    {"rank": 7,  "name": "ICICI Bank",                      "ticker": "ICICIBANK.NS",   "sector": "Banking",         "score": 38, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "Good asset management and growth prospects in retail banking.", "key_risk": "Non-Performing Assets (NPA) levels.", "screener": "ICICIBANK", "mc": "icici-bank"},
    {"rank": 8,  "name": "JSW Steel",                       "ticker": "JSWSTEEL.NS",    "sector": "Metals",          "score": 35, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "Solid operator in cyclical industry with global demand linkages.", "key_risk": "Volatility in steel prices.", "screener": "JSWSTEEL", "mc": "jsw-steel"},
    {"rank": 9,  "name": "NTPC Limited",                    "ticker": "NTPC.NS",        "sector": "Energy",          "score": 35, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Conservative","thesis": "Leading power generator transitioning to renewables.", "key_risk": "Regulatory issues on environmental norms.", "screener": "NTPC", "mc": "ntpc"},
    {"rank": 10, "name": "Larsen & Toubro",                 "ticker": "LT.NS",          "sector": "Infrastructure",  "score": 35, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Moderate",    "thesis": "Established player in infrastructure with multiple project streams.", "key_risk": "Delays in project execution.", "screener": "LT", "mc": "larsen-and-toubro"},
    {"rank": 11, "name": "Titan Company",                   "ticker": "TITAN.NS",       "sector": "Consumer",        "score": 34, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Moderate",    "thesis": "Strong brand in watches and jewellery with premium positioning.", "key_risk": "Gold price volatility.", "screener": "TITAN", "mc": "titan-company"},
    {"rank": 12, "name": "State Bank of India",             "ticker": "SBIN.NS",        "sector": "Banking",         "score": 33, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "Largest public sector bank with recovery potential.", "key_risk": "Political and regulatory risk.", "screener": "SBIN", "mc": "state-bank-of-india"},
    {"rank": 13, "name": "Sun Pharmaceutical",              "ticker": "SUNPHARMA.NS",   "sector": "Pharma",          "score": 33, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Moderate",    "thesis": "Strong pipeline with global generics presence.", "key_risk": "Patent expiration and US FDA risk.", "screener": "SUNPHARMA", "mc": "sun-pharmaceutical-industries"},
    {"rank": 14, "name": "Tata Consultancy Services",       "ticker": "TCS.NS",         "sector": "IT",              "score": 32, "risk": "Low",    "horizon": "Long (3+ yr)",    "profile": "Conservative","thesis": "Global IT services leader with consistent dividend payout.", "key_risk": "Slowdown in US/Europe IT spending.", "screener": "TCS", "mc": "tata-consultancy-services"},
    {"rank": 15, "name": "Infosys",                         "ticker": "INFY.NS",        "sector": "IT",              "score": 32, "risk": "Low",    "horizon": "Long (3+ yr)",    "profile": "Conservative","thesis": "Strong AI and digital transformation capabilities.", "key_risk": "Revenue concentration in banking/finance clients.", "screener": "INFY", "mc": "infosys"},
    {"rank": 16, "name": "Reliance Industries",             "ticker": "RELIANCE.NS",    "sector": "Conglomerate",    "score": 31, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Moderate",    "thesis": "Diversified giant with retail, telecom, and energy verticals.", "key_risk": "High capex and debt levels.", "screener": "RELIANCE", "mc": "reliance-industries"},
    {"rank": 17, "name": "Kotak Mahindra Bank",             "ticker": "KOTAKBANK.NS",   "sector": "Banking",         "score": 31, "risk": "Medium", "horizon": "Long (3+ yr)",    "profile": "Moderate",    "thesis": "Premium private bank with strong asset quality.", "key_risk": "Management transition risk.", "screener": "KOTAKBANK", "mc": "kotak-mahindra-bank"},
    {"rank": 18, "name": "Axis Bank",                       "ticker": "AXISBANK.NS",    "sector": "Banking",         "score": 30, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "Improving asset quality with retail banking growth.", "key_risk": "NPA levels in corporate book.", "screener": "AXISBANK", "mc": "axis-bank"},
    {"rank": 19, "name": "ITC",                             "ticker": "ITC.NS",         "sector": "Consumer",        "score": 30, "risk": "Low",    "horizon": "Long (3+ yr)",    "profile": "Conservative","thesis": "High dividend yield with diversification into FMCG and hotels.", "key_risk": "Tobacco regulatory risk.", "screener": "ITC", "mc": "itc"},
    {"rank": 20, "name": "Mahindra & Mahindra",             "ticker": "M&M.NS",         "sector": "Automobile",      "score": 29, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "Leading SUV maker with strong EV pipeline.", "key_risk": "EV competition from new entrants.", "screener": "M&M", "mc": "mahindra-and-mahindra"},
    {"rank": 21, "name": "Adani Ports & SEZ",               "ticker": "ADANIPORTS.NS",  "sector": "Infrastructure",  "score": 28, "risk": "High",   "horizon": "Long (3+ yr)",    "profile": "Aggressive",  "thesis": "India's largest port operator with logistics expansion.", "key_risk": "Governance and regulatory risk.", "screener": "ADANIPORTS", "mc": "adani-ports-and-sez"},
    {"rank": 22, "name": "Oil & Natural Gas Corp",          "ticker": "ONGC.NS",        "sector": "Energy",          "score": 27, "risk": "Medium", "horizon": "Medium (1-3 yr)", "profile": "Moderate",    "thesis": "State-owned energy major positioning in renewables.", "key_risk": "Oil price volatility and govt pricing control.", "screener": "ONGC", "mc": "oil-and-natural-gas-corporation"},
    {"rank": 23, "name": "NTPC Limited",                    "ticker": "NTPC.NS",        "sector": "Energy",          "score": 26, "risk": "Low",    "horizon": "Long (3+ yr)",    "profile": "Conservative","thesis": "Steady state-backed power utility.", "key_risk": "Slow renewable transition.", "screener": "NTPC", "mc": "ntpc"},
    {"rank": 24, "name": "Adani Enterprises",               "ticker": "ADANIENT.NS",    "sector": "Conglomerate",    "score": 25, "risk": "High",   "horizon": "Long (3+ yr)",    "profile": "Aggressive",  "thesis": "Group flagship with airport, green energy, and data centre bets.", "key_risk": "High debt and governance concerns.", "screener": "ADANIENT", "mc": "adani-enterprises"},
    {"rank": 25, "name": "Adani Power",                     "ticker": "ADANIPOWER.NS",  "sector": "Energy",          "score": 24, "risk": "High",   "horizon": "Medium (1-3 yr)", "profile": "Aggressive",  "thesis": "Largest private thermal power producer with capacity expansion.", "key_risk": "Regulatory and promoter governance risk.", "screener": "ADANIPOWER", "mc": "adani-power"},
]

PORTFOLIO = [(p["name"], p["allocation"]) for p in AI_PORTFOLIO] if AI_PORTFOLIO else [
    ("HDFC Bank", 15), ("Bajaj Finance", 15), ("Hindustan Unilever", 10),
    ("Maruti Suzuki India", 10), ("UltraTech Cement", 10), ("Bharti Airtel", 10),
    ("ICICI Bank", 10), ("JSW Steel", 8), ("NTPC Limited", 7), ("Larsen & Toubro", 5),
]

RISK_COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
SECTOR_COLORS = {
    "Banking": "#1d4ed8", "NBFC": "#7c3aed", "Consumer": "#059669",
    "Automobile": "#d97706", "Infrastructure": "#dc2626", "Telecom": "#0891b2",
    "Metals": "#6b7280", "Energy": "#ea580c", "Pharma": "#db2777",
    "IT": "#4f46e5", "Conglomerate": "#92400e",
}

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header { background: linear-gradient(135deg,#1a237e,#1565c0); padding:32px;
  border-radius:12px; text-align:center; margin-bottom:24px; }
.main-header h1 { color:#fff; font-size:2rem; margin:0; }
.main-header p  { color:#93c5fd; margin:8px 0 0; }
.stock-card { background:#1a1f2e; border:1px solid #2d3748; border-radius:12px;
  padding:18px; margin-bottom:12px; }
.rank-badge { background:#0d47a1; color:#93c5fd; border-radius:50%;
  width:40px;height:40px; display:inline-flex; align-items:center;
  justify-content:center; font-weight:700; font-size:1rem; margin-right:12px; }
.disclaimer { background:#1c1a10; border-left:4px solid #f59e0b;
  padding:12px 18px; border-radius:8px; color:#fbbf24; font-size:0.85rem; }
.metric-card { background:#1e2132; border:1px solid #2d3748;
  border-radius:10px; padding:16px; text-align:center; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇮🇳 India Stock Analysis")
    st.markdown("---")
    page = st.radio("Navigate", [
        "📊 Dashboard",
        "🏆 Top 10 Rankings",
        "🔍 Company Deep Dive",
        "💼 Portfolio Allocator",
        "📈 Live Charts",
    ])
    st.markdown("---")
    auto_refresh = st.toggle("🔄 Auto Refresh (5 min)", value=False)
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption(f"📊 AI Analysis: {AI_GENERATED}")
    st.caption(f"📈 Market data: {datetime.now().strftime('%d %b %Y %H:%M')}")
    st.caption("⚠️ Not financial advice. Consult a SEBI-registered advisor.")

# ── Data fetching ──────────────────────────────────────────────────────────────
def _nse_symbol(ticker):
    """Strip .NS / .BO suffix to get NSE symbol."""
    return ticker.replace(".NS", "").replace(".BO", "")

@st.cache_data(ttl=300)
def fetch_price(ticker):
    """Fetch live price from NSE."""
    symbol = _nse_symbol(ticker)
    if NSE_AVAILABLE:
        try:
            data = nse_eq(symbol)
            price = float(data["priceInfo"]["lastPrice"])
            prev  = float(data["priceInfo"]["previousClose"])
            chg   = ((price - prev) / prev) * 100
            return round(price, 2), round(chg, 2)
        except Exception:
            pass
    return None, None

@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    """Return (info_dict, history_df) from NSE only."""
    symbol = _nse_symbol(ticker)
    info = {}
    hist = pd.DataFrame()
    if NSE_AVAILABLE:
        try:
            data = nse_eq(symbol)
            pi = data.get("priceInfo", {})
            md = data.get("metadata", {})
            info = {
                "currentPrice":        pi.get("lastPrice"),
                "previousClose":       pi.get("previousClose"),
                "fiftyTwoWeekHigh":    pi.get("weekHighLow", {}).get("max"),
                "fiftyTwoWeekLow":     pi.get("weekHighLow", {}).get("min"),
                "marketCap":           None,
                "trailingPE":          None,
                "dividendYield":       None,
                "returnOnEquity":      None,
                "beta":                None,
                "longBusinessSummary": md.get("pdSectorInd", ""),
            }
        except Exception:
            pass
        try:
            end = datetime.today().strftime("%d-%m-%Y")
            start = (datetime.today() - timedelta(days=30)).strftime("%d-%m-%Y")
            hist = nse_eq_history(symbol, start, end)
            if hist is not None and not hist.empty:
                hist.index = pd.to_datetime(hist.index)
        except Exception:
            hist = pd.DataFrame()
    return info, hist

@st.cache_data(ttl=300)
def fetch_history(ticker, days=180):
    """Fetch price history from NSE for charts."""
    symbol = _nse_symbol(ticker)
    if NSE_AVAILABLE:
        try:
            end = datetime.today().strftime("%d-%m-%Y")
            start = (datetime.today() - timedelta(days=days)).strftime("%d-%m-%Y")
            hist = nse_eq_history(symbol, start, end)
            if hist is not None and not hist.empty:
                hist.index = pd.to_datetime(hist.index)
                return hist
        except Exception:
            pass
    return pd.DataFrame()

# ── Auto refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    elapsed = time.time() - st.session_state.last_refresh
    if elapsed >= 300:
        st.session_state.last_refresh = time.time()
        st.cache_data.clear()
        st.rerun()
    else:
        remaining = int(300 - elapsed)
        st.sidebar.caption(f"⏱ Next refresh in {remaining}s")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.markdown("""
    <div class="main-header">
      <h1>🇮🇳 India Top 25 — Investment Analysis</h1>
      <p>AI-powered research · Live market data · Updated every 5 minutes</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="disclaimer">⚠️ <b>Disclaimer:</b> AI-generated analysis for educational purposes only. Not personal financial advice. Always consult a SEBI-registered investment advisor before investing.</div>', unsafe_allow_html=True)
    st.markdown("")

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies Analysed", "25")
    col2.metric("Top Picks", "10")
    col3.metric("Sectors Covered", "11")
    col4.metric("Highest AI Score", "43 / 50")

    st.markdown("---")

    # Score chart
    st.subheader("📊 AI Fundamental Scores — All 25 Companies")
    df_scores = pd.DataFrame(COMPANIES)[["rank","name","score","sector","risk"]]
    df_scores = df_scores.sort_values("score", ascending=True)
    colors = [SECTOR_COLORS.get(s, "#6b7280") for s in df_scores["sector"]]
    fig = go.Figure(go.Bar(
        x=df_scores["score"], y=df_scores["name"],
        orientation='h',
        marker_color=colors,
        text=df_scores["score"],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Score: %{x}/50<extra></extra>',
    ))
    fig.update_layout(
        height=700, xaxis_range=[0, 55],
        xaxis_title="AI Score (/50)", yaxis_title="",
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        font_color="#e2e8f0",
        xaxis=dict(gridcolor="#1e2132"),
        margin=dict(l=10, r=40, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sector breakdown pie
    st.subheader("🏭 Sector Distribution (Top 10)")
    top10 = [c for c in COMPANIES if c["rank"] <= 10]
    sector_counts = pd.DataFrame(top10).groupby("sector").size().reset_index(name="count")
    fig2 = px.pie(sector_counts, names="sector", values="count",
                  color_discrete_sequence=px.colors.qualitative.Bold)
    fig2.update_layout(plot_bgcolor="#0f1117", paper_bgcolor="#0f1117", font_color="#e2e8f0")
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TOP 10
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Top 10 Rankings":
    st.title("🏆 Top 10 Ranked Stocks")
    st.markdown('<div class="disclaimer">⚠️ AI analysis only. Consult a SEBI advisor before investing.</div>', unsafe_allow_html=True)
    st.markdown("")

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        profile_filter = st.multiselect("Filter by Investor Profile",
            ["Conservative", "Moderate", "Aggressive"], default=[])
    with filter_col2:
        horizon_filter = st.multiselect("Filter by Horizon",
            ["Short (< 1 yr)", "Medium (1-3 yr)", "Long (3+ yr)"], default=[])

    top10 = [c for c in COMPANIES if c["rank"] <= 10]
    if profile_filter:
        top10 = [c for c in top10 if c["profile"] in profile_filter]
    if horizon_filter:
        top10 = [c for c in top10 if c["horizon"] in horizon_filter]

    for c in top10:
        with st.container():
            col_rank, col_info, col_score = st.columns([1, 6, 2])
            with col_rank:
                medal = "🥇" if c["rank"]==1 else "🥈" if c["rank"]==2 else "🥉" if c["rank"]==3 else f"#{c['rank']}"
                st.markdown(f"<div style='font-size:2rem;text-align:center;padding-top:12px'>{medal}</div>", unsafe_allow_html=True)
            with col_info:
                st.markdown(f"### {c['name']}")
                st.caption(f"**Sector:** {c['sector']}  ·  **Horizon:** {c['horizon']}  ·  **Profile:** {c['profile']}  ·  **Risk:** {RISK_COLOR[c['risk']]} {c['risk']}")
                st.markdown(f"💡 *{c['thesis']}*")
                st.markdown(f"⚠️ **Key Risk:** {c['key_risk']}")
                # Dynamic links
                links = (
                    f"[📊 Screener.in](https://www.screener.in/company/{c['screener']}/consolidated/) · "
                    f"[📰 Moneycontrol](https://www.moneycontrol.com/india/stockpricequote/{c['mc']}) · "
                    f"[📈 Yahoo Finance](https://finance.yahoo.com/quote/{c['ticker']}) · "
                    f"[🌐 NSE India](https://www.nseindia.com/get-quotes/equity?symbol={c['screener']})"
                )
                st.markdown(links)
            with col_score:
                st.metric("AI Score", f"{c['score']}/50")
                score_pct = c['score'] / 50
                st.progress(score_pct)
                # Live price
                with st.spinner(""):
                    price, chg = fetch_price(c['ticker'])
                if price:
                    delta_str = f"{chg:+.2f}%"
                    st.metric("Live Price", f"₹{price:,.2f}", delta=delta_str)
            st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: COMPANY DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Company Deep Dive":
    st.title("🔍 Company Deep Dive")

    company_names = [c["name"] for c in COMPANIES]
    selected = st.selectbox("Select a company", company_names)
    c = next(x for x in COMPANIES if x["name"] == selected)

    st.markdown(f"## {c['name']}")
    st.caption(f"Rank #{c['rank']} · {c['sector']} · {c['ticker']}")

    # Live data
    with st.spinner("Fetching live market data..."):
        info, hist = fetch_stock_data(c['ticker'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        st.metric("Current Price", f"₹{price:,.2f}" if price else "N/A")
    with col2:
        mktcap = info.get('marketCap')
        if mktcap:
            st.metric("Market Cap", f"₹{mktcap/1e12:.2f}T")
        else:
            st.metric("Market Cap", "N/A")
    with col3:
        pe = info.get('trailingPE')
        st.metric("P/E Ratio", f"{pe:.1f}x" if pe else "N/A")
    with col4:
        div = info.get('dividendYield')
        st.metric("Dividend Yield", f"{div*100:.2f}%" if div else "N/A")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh','N/A'):,.2f}" if info.get('fiftyTwoWeekHigh') else "N/A")
    with col6:
        st.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow','N/A'):,.2f}" if info.get('fiftyTwoWeekLow') else "N/A")
    with col7:
        roe = info.get('returnOnEquity')
        st.metric("ROE", f"{roe*100:.1f}%" if roe else "N/A")
    with col8:
        beta = info.get('beta')
        st.metric("Beta", f"{beta:.2f}" if beta else "N/A")

    # AI Analysis
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🤖 AI Analysis")
        st.info(f"**Investment Thesis:** {c['thesis']}")
        st.error(f"**Key Risk:** {c['key_risk']}")
        st.markdown(f"**AI Score:** {c['score']}/50")
        st.progress(c['score']/50)
        st.markdown(f"**Risk:** {RISK_COLOR[c['risk']]} {c['risk']}  ·  **Horizon:** {c['horizon']}  ·  **Profile:** {c['profile']}")
    with col_b:
        st.markdown("### 🔗 Research Links")
        st.markdown(f"""
- [📊 Screener.in — Financials & Ratios](https://www.screener.in/company/{c['screener']}/consolidated/)
- [📰 Moneycontrol — News & Analysis](https://www.moneycontrol.com/india/stockpricequote/{c['mc']})
- [📈 Yahoo Finance — Charts & Data](https://finance.yahoo.com/quote/{c['ticker']})
- [🏛️ NSE India — Exchange Data](https://www.nseindia.com/get-quotes/equity?symbol={c['screener']})
- [📋 BSE India](https://www.bseindia.com/stock-share-price/{c['screener'].lower()})
- [🔍 Economic Times](https://economictimes.indiatimes.com/{c['mc'].replace('-','_')}/stocks/companyid-{c['screener']}.cms)
        """)

    # Price chart
    st.markdown("---")
    period = st.selectbox("Chart period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
    period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    with st.spinner("Loading chart..."):
        hist_period = fetch_history(c['ticker'], days=period_days[period])

    if not hist_period.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist_period.index,
            open=hist_period['Open'], high=hist_period['High'],
            low=hist_period['Low'], close=hist_period['Close'],
            name="Price",
        ))
        fig.add_trace(go.Bar(
            x=hist_period.index, y=hist_period['Volume'],
            name="Volume", yaxis="y2",
            marker_color="rgba(59,130,246,0.3)",
        ))
        fig.update_layout(
            title=f"{c['name']} — Price Chart",
            yaxis2=dict(overlaying='y', side='right', showgrid=False),
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
            font_color="#e2e8f0",
            xaxis=dict(gridcolor="#1e2132"),
            yaxis=dict(gridcolor="#1e2132"),
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Could not fetch chart data for this ticker.")

    # Company description
    desc = info.get('longBusinessSummary')
    if desc:
        st.markdown("---")
        st.markdown("### 🏢 Company Overview")
        st.markdown(desc)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PORTFOLIO ALLOCATOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💼 Portfolio Allocator":
    st.title("💼 Suggested Portfolio — Moderate Risk Investor")
    st.markdown('<div class="disclaimer">⚠️ This is an illustrative model portfolio only. Not personalised financial advice.</div>', unsafe_allow_html=True)
    st.markdown("")

    investment = st.number_input("Enter your investment amount (₹)", min_value=10000, value=100000, step=10000)

    portfolio_data = []
    for name, alloc_pct in PORTFOLIO:
        c = next((x for x in COMPANIES if x["name"] == name), None)
        if c:
            amount = investment * alloc_pct / 100
            portfolio_data.append({
                "Company": name, "Sector": c["sector"],
                "Allocation %": alloc_pct,
                "Amount (₹)": f"₹{amount:,.0f}",
                "Horizon": c["horizon"],
                "Risk": f"{RISK_COLOR[c['risk']]} {c['risk']}",
                "AI Score": f"{c['score']}/50",
            })

    df_port = pd.DataFrame(portfolio_data)
    st.dataframe(df_port, use_container_width=True, hide_index=True)

    # Pie chart
    fig = px.pie(df_port, names="Company", values="Allocation %",
                 title="Portfolio Allocation",
                 color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_layout(plot_bgcolor="#0f1117", paper_bgcolor="#0f1117", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True)

    # Sector pie
    sector_alloc = df_port.groupby("Sector")["Allocation %"].sum().reset_index()
    fig2 = px.pie(sector_alloc, names="Sector", values="Allocation %",
                  title="Sector Allocation",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig2.update_layout(plot_bgcolor="#0f1117", paper_bgcolor="#0f1117", font_color="#e2e8f0")
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE CHARTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Live Charts":
    st.title("📈 Live Price Comparison")

    selected_companies = st.multiselect(
        "Select companies to compare",
        [c["name"] for c in COMPANIES],
        default=[c["name"] for c in COMPANIES[:5]]
    )
    period = st.select_slider("Period", ["1mo","3mo","6mo","1y","2y"], value="6mo")
    period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}

    if selected_companies:
        fig = go.Figure()
        with st.spinner("Fetching live data..."):
            for name in selected_companies:
                c = next((x for x in COMPANIES if x["name"] == name), None)
                if c:
                    hist = fetch_history(c['ticker'], days=period_days[period])
                    if not hist.empty:
                        # Normalise to 100 for comparison
                        normalised = (hist['Close'] / hist['Close'].iloc[0]) * 100
                        fig.add_trace(go.Scatter(
                            x=hist.index, y=normalised,
                            name=name, mode='lines',
                        ))
        fig.update_layout(
            title="Normalised Price Performance (Base = 100)",
            yaxis_title="Indexed Price",
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
            font_color="#e2e8f0",
            xaxis=dict(gridcolor="#1e2132"),
            yaxis=dict(gridcolor="#1e2132"),
            height=500,
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Normalised to 100 at start of period for easy comparison.")
    else:
        st.info("Select at least one company above.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Built with CrewAI · yfinance · Streamlit · Not financial advice · Consult a SEBI-registered advisor · [GitHub](https://github.com/bharathiarasub/india-stock-analysis)")
