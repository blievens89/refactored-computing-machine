import time
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PageSpeed Bulk Checker", layout="wide")

# Get API key from secrets
API_KEY = st.secrets.get("pagespeed", {}).get("api_key", None)
if not API_KEY:
    st.error("API key not set. Add it in Streamlit Cloud → Settings → Secrets.")
    st.stop()

st.title("PageSpeed Insights — Bulk Checker")

# UI inputs
strategy = st.radio("Choose strategy", ["mobile", "desktop"], horizontal=True)
urls_text = st.text_area("Paste URLs (one per line)")
run = st.button("Run checks")

def fetch_pagespeed(url, strategy, api_key):
    try:
        r = requests.get(
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
            params={"url": url, "key": api_key, "strategy": strategy},
            timeout=180,  # allow up to 3 minutes
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
    except requests.exceptions.Timeout:
        return {"url": url, "strategy": strategy, "error": "timeout"}
    except Exception as e:
        return {"url": url, "strategy": strategy, "error": str(e)}

if run:
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    if not urls:
        st.warning("Please paste at least one URL.")
    else:
        rows = []
        prog = st.progress(0)
        for i, u in enumerate(urls, start=1):
            rows.append(fetch_pagespeed(u, strategy, API_KEY))
            prog.progress(i / len(urls))
            time.sleep(2)  # pause between requests to avoid throttling
        df = pd.DataFrame(rows)
        st.subheader("Results")
        st.dataframe(df, use_container_width=True)

        # Download CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download results as CSV", csv, file_name=f"psi_{strategy}.csv", mime="text/csv")
