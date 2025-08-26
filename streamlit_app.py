# streamlit_app.py
import requests, pandas as pd, streamlit as st

st.set_page_config(page_title="PSI Bulk", layout="wide")
API_KEY = st.secrets["pagespeed"]["api_key"]

st.title("PageSpeed Insights — Bulk")
strategy = st.radio("Strategy", ["mobile", "desktop"], horizontal=True)
urls_text = st.text_area("Paste URLs (one per line)")
run = st.button("Run")

def fetch(url, strategy):
    r = requests.get(
        "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
        params={"url": url, "key": API_KEY, "strategy": strategy},
        timeout=90,
    )
    r.raise_for_status()
    j = r.json()
    LHR = j.get("lighthouseResult", {})
    cats = LHR.get("categories", {})
    audits = LHR.get("audits", {})
    def val(key, field="numericValue"):
        a = audits.get(key, {})
        return a.get(field)
    return {
        "url": url,
        "strategy": strategy,
        "perf_score": (cats.get("performance", {}).get("score") or 0) * 100,
        "FCP_ms": val("first-contentful-paint"),
        "LCP_ms": val("largest-contentful-paint"),
        "TBT_ms": val("total-blocking-time"),
        "CLS": audits.get("cumulative-layout-shift", {}).get("displayValue"),
        "SpeedIndex_ms": val("speed-index"),
        "TTI_ms": val("interactive"),
    }

if run:
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    rows = []
    prog = st.progress(0)
    for i, u in enumerate(urls, start=1):
        try:
            rows.append(fetch(u, strategy))
        except Exception as e:
            rows.append({"url": u, "strategy": strategy, "error": str(e)})
        prog.progress(i/len(urls))
    df = pd.DataFrame(rows)
    st.subheader("Results")
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, file_name=f"psi_{strategy}.csv", mime="text/csv")
