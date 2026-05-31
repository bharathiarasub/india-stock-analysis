#!/usr/bin/env python
import os
import re
import json
import time
from datetime import datetime
from financial_researcher.crew import ResearchCrew
from financial_researcher.ranker_crew import StockRankerCrew

TICKER_MAP = {
    "Reliance Industries":          "RELIANCE.NS",
    "HDFC Bank":                    "HDFCBANK.NS",
    "Bharti Airtel":                "BHARTIARTL.NS",
    "ICICI Bank":                   "ICICIBANK.NS",
    "State Bank of India":          "SBIN.NS",
    "Tata Consultancy Services":    "TCS.NS",
    "Bajaj Finance":                "BAJFINANCE.NS",
    "Larsen and Toubro":            "LT.NS",
    "Hindustan Unilever":           "HINDUNILVR.NS",
    "Life Insurance Corporation of India": "LICI.NS",
    "Infosys":                      "INFY.NS",
    "Sun Pharmaceutical":           "SUNPHARMA.NS",
    "Adani Power":                  "ADANIPOWER.NS",
    "Maruti Suzuki India":          "MARUTI.NS",
    "Adani Ports and SEZ":          "ADANIPORTS.NS",
    "ITC":                          "ITC.NS",
    "Axis Bank":                    "AXISBANK.NS",
    "Kotak Mahindra Bank":          "KOTAKBANK.NS",
    "NTPC Limited":                 "NTPC.NS",
    "Oil and Natural Gas Corporation": "ONGC.NS",
    "Mahindra and Mahindra":        "M&M.NS",
    "Adani Enterprises":            "ADANIENT.NS",
    "Titan Company":                "TITAN.NS",
    "UltraTech Cement":             "ULTRACEMCO.NS",
    "JSW Steel":                    "JSWSTEEL.NS",
    "HCL Technologies":             "HCLTECH.NS",
    "Larsen & Toubro":              "LT.NS",
    "Oil & Natural Gas Corp":       "ONGC.NS",
    "Adani Ports & SEZ":            "ADANIPORTS.NS",
}

def fetch_stock_metrics(name: str) -> dict:
    """Fetch key stock metrics via yfinance. Returns empty dict on failure."""
    ticker = TICKER_MAP.get(name)
    if not ticker:
        return {}
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="2d")
        price, chg = None, None
        if len(hist) >= 2:
            price = round(float(hist['Close'].iloc[-1]), 2)
            prev  = float(hist['Close'].iloc[-2])
            chg   = round((price - prev) / prev * 100, 2)
        elif len(hist) == 1:
            price = round(float(hist['Close'].iloc[-1]), 2)
            chg   = 0.0
        return {
            "ticker":           ticker,
            "price":            price,
            "change_pct":       chg,
            "market_cap":       info.get("marketCap"),
            "pe_ratio":         info.get("trailingPE"),
            "dividend_yield":   info.get("dividendYield"),
            "roe":              info.get("returnOnEquity"),
            "beta":             info.get("beta"),
            "week52_high":      info.get("fiftyTwoWeekHigh"),
            "week52_low":       info.get("fiftyTwoWeekLow"),
            "fetched_at":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as e:
        print(f"  ⚠ Could not fetch metrics for {name}: {e}")
        return {}

os.makedirs('output', exist_ok=True)

TOP_25_INDIAN_COMPANIES = [
    "Reliance Industries",
    "HDFC Bank",
    "Bharti Airtel",
    "ICICI Bank",
    "State Bank of India",
    "Tata Consultancy Services",
    "Bajaj Finance",
    "Larsen and Toubro",
    "Hindustan Unilever",
    "Life Insurance Corporation of India",
    "Infosys",
    "Sun Pharmaceutical",
    "Adani Power",
    "Maruti Suzuki India",
    "Adani Ports and SEZ",
    "ITC",
    "Axis Bank",
    "Kotak Mahindra Bank",
    "NTPC Limited",
    "Oil and Natural Gas Corporation",
    "Mahindra and Mahindra",
    "Adani Enterprises",
    "Titan Company",
    "UltraTech Cement",
    "JSW Steel",
]


def run_research():
    """Phase 1: Research all 25 companies and save individual reports."""
    failed = []
    for i, company in enumerate(TOP_25_INDIAN_COMPANIES, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/25] Researching: {company}")
        print('='*60)
        safe_name = company.replace(' ', '_').replace('/', '_')
        report_path = f"output/{i:02d}_{safe_name}.md"

        # Skip if already done (resume-friendly)
        if os.path.exists(report_path):
            print(f"  ↳ Already exists, skipping.")
            continue

        try:
            result = ResearchCrew().crew().kickoff(inputs={'company': company})
            with open(report_path, "w") as f:
                f.write(f"# {company}\n\n")
                f.write(result.raw)
            print(f"  ✓ Saved: {report_path}")
        except Exception as e:
            print(f"  ✗ Failed: {company} — {e}")
            failed.append(company)

        time.sleep(2)

    print(f"\nResearch complete. {25 - len(failed)}/25 reports generated.")
    if failed:
        print(f"Failed companies: {failed}")
    return failed


def run_ranking():
    """Phase 2: Read all reports and produce a ranked investment shortlist."""
    print(f"\n{'='*60}")
    print("PHASE 2: Stock Ranking & Investment Analysis")
    print('='*60)

    # Load all generated reports
    reports = {}
    for i, company in enumerate(TOP_25_INDIAN_COMPANIES, 1):
        safe_name = company.replace(' ', '_').replace('/', '_')
        path = f"output/{i:02d}_{safe_name}.md"
        if os.path.exists(path):
            with open(path, "r") as f:
                reports[company] = f.read()
        else:
            reports[company] = f"No report available for {company}."

    combined_reports = "\n\n---\n\n".join(
        [f"## {company}\n\n{content}" for company, content in reports.items()]
    )

    result = StockRankerCrew().crew().kickoff(inputs={
        "company_reports": combined_reports,
        "num_companies": "25",
    })

    with open("output/STOCK_RANKING_REPORT.md", "w") as f:
        f.write(result.raw)

    # ── Parse and save structured JSON for the Streamlit app ──────────────────
    save_ranking_json(result.raw)

    print("\n✓ Stock ranking report saved to output/STOCK_RANKING_REPORT.md")
    print("✓ Structured JSON saved to output/ranking.json")
    print("\n⚠️  DISCLAIMER: This is AI-generated analysis for educational purposes only.")
    print("   Always consult a SEBI-registered financial advisor before investing.")
    return result


def save_ranking_json(report_text: str):
    """Parse the markdown report and save structured JSON for the Streamlit app."""
    companies = []
    # Extract top 10 table rows: | rank | name | score | risk | horizon | profile | thesis | key_risk |
    table_pattern = re.compile(
        r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(Low|Medium|High)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
    )
    for m in table_pattern.finditer(report_text):
        try:
            companies.append({
                "rank":     int(m.group(1)),
                "name":     m.group(2).strip(),
                "score":    int(m.group(3)),
                "risk":     m.group(4).strip(),
                "horizon":  m.group(5).strip(),
                "profile":  m.group(6).strip(),
                "thesis":   m.group(7).strip(),
                "key_risk": m.group(8).strip(),
            })
        except Exception:
            continue

    # Extract portfolio allocation table
    portfolio = []
    alloc_pattern = re.compile(r'\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|')
    in_portfolio = False
    for line in report_text.splitlines():
        if "DIVERSIFIED PORTFOLIO" in line.upper() or "PORTFOLIO SUGGESTION" in line.upper():
            in_portfolio = True
        if in_portfolio:
            m = alloc_pattern.match(line)
            if m and not m.group(1).strip().lower().startswith("company"):
                portfolio.append({
                    "name": m.group(1).strip(),
                    "allocation": int(m.group(2)),
                })

    # Fetch live stock metrics for each ranked company
    print("\nFetching stock metrics from yfinance...")
    for c in companies:
        metrics = fetch_stock_metrics(c["name"])
        c.update(metrics)
        if metrics.get("price"):
            print(f"  ✓ {c['name']}: ₹{metrics['price']}")

    output = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "generated_date": datetime.now().strftime("%d %b %Y"),
        "top_companies": companies if companies else [],
        "portfolio": portfolio if portfolio else [],
        "raw_report": report_text,
    }

    with open("output/ranking.json", "w") as f:
        json.dump(output, f, indent=2)



def run():
    """Run research on top 25 Indian companies, then rank them."""
    run_research()
    run_ranking()


if __name__ == "__main__":
    run()
