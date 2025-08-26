import streamlit as st, requests

API_KEY = st.secrets["pagespeed"]["api_key"]

def run(url, strategy="mobile"):
    r = requests.get(
        "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
        params={"url": url, "key": API_KEY, "strategy": strategy},
        timeout=60
    )
    r.raise_for_status()
    return r.json()
