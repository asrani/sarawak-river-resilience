from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sarawak River Resilience", page_icon="🌊", layout="wide")
ROOT = Path(__file__).parent
st.title("🌊 Sarawak River Resilience")
st.caption("MESRA research demonstrator · All monitoring values, locations and incidents are simulated.")
st.warning("Research prototype only. These indicators are unvalidated and must not be used for operational warnings or emergency decisions.")

@st.cache_data
def make_data():
    rng = np.random.default_rng(42)
    sites = pd.DataFrame({"site": ["Demonstration site A", "Demonstration site B", "Demonstration site C"], "lat": [1.55, 1.46, 1.61], "lon": [110.35, 110.48, 110.58]})
    dates = pd.date_range("2026-09-01", periods=720, freq="h")
    frames = []
    for i, row in sites.iterrows():
        rain = np.where(rng.random(len(dates)) < .22, rng.gamma(2, 5, len(dates)), 0)
        level = 1.5 + i*.25 + pd.Series(rain).rolling(18, min_periods=1).sum().to_numpy() / 65 + .12*np.sin(np.arange(len(dates))/12) + rng.normal(0,.04,len(dates))
        frames.append(pd.DataFrame({"time":dates,"site":row.site,"rain_mm":rain,"river_m":level}))
    return sites, pd.concat(frames, ignore_index=True)

sites, data = make_data()
st.sidebar.header("Explore monitoring data")
site = st.sidebar.selectbox("Monitoring site", sites.site)
window = st.sidebar.slider("Days displayed", 1, 30, 7)
selected = data[data.site.eq(site)].copy()
view = selected.tail(window*24)
page = st.sidebar.radio("Page", ["Overview", "Explore data", "Community observations", "Scenario explorer", "Research evaluation"])
st.sidebar.caption("Fixed demonstration period: September 2026. No live feeds are connected.")

if page == "Overview":
    st.subheader("Simulated monitoring overview")
    a,b,c = st.columns(3)
    a.metric("Latest river level", f"{view.river_m.iloc[-1]:.2f} m")
    b.metric("Rainfall over last 24 hours", f"{selected.rain_mm.tail(24).sum():.1f} mm")
    c.metric("Demonstration sites", len(sites))
    st.write(f"Last simulated reading: {view.time.iloc[-1]:%d %B %Y, %H:%M}. This is historical demonstration data.")
    st.map(sites, latitude="lat", longitude="lon")
    st.caption("Markers indicate illustrative locations, not actual sensor installations.")
    st.line_chart(view.set_index("time")[["river_m"]], y_label="River level (m)")
    st.info("Research question: Can environmental measurements and community observations improve the usefulness of local flood-risk information?")

elif page == "Explore data":
    st.subheader(site)
    st.line_chart(view.set_index("time")[["river_m"]], y_label="River level (m)")
    st.bar_chart(view.set_index("time")[["rain_mm"]], y_label="Hourly rainfall (mm)")
    st.dataframe(view, hide_index=True, use_container_width=True)
    st.download_button("Download displayed simulated data", view.to_csv(index=False), "simulated_monitoring.csv", "text/csv")

elif page == "Community observations":
    st.subheader("Community observation notebook")
    st.caption("Entries remain in this browser session and disappear when the session ends. Export them to retain a copy. Avoid personal or sensitive information.")
    if "reports" not in st.session_state:
        st.session_state.reports = []
    with st.form("observation", clear_on_submit=True):
        location = st.selectbox("Observation site", sites.site)
        category = st.selectbox("Observation type", ["Flooding", "Blocked drainage", "Riverbank erosion", "Water quality", "Other"])
        observed = st.date_input("Observation date")
        notes = st.text_area("Description", max_chars=1500)
        submitted = st.form_submit_button("Save to session")
        if submitted:
            if not notes.strip():
                st.error("Add a description before saving.")
            else:
                st.session_state.reports.append({"site":location,"category":category,"date":str(observed),"description":notes.strip()})
                st.success("Observation saved to this session.")
    if st.session_state.reports:
        st.dataframe(pd.DataFrame(st.session_state.reports), hide_index=True)
        st.download_button("Export observations", json.dumps(st.session_state.reports, indent=2), "observations.json", "application/json")
    else:
        st.info("No observations recorded in this session.")

elif page == "Scenario explorer":
    st.subheader("Experimental threshold explorer")
    st.write("Compare a hypothetical river-level threshold against simulated historical readings. This is a sensitivity exercise, not a rainfall-to-flood forecast.")
    threshold = st.slider("Hypothetical river threshold (m)", 1.0, 5.0, 2.5, .1)
    offset = st.slider("Assumed river-level shift (m)", -.5, 1.5, 0.0, .1)
    scenario = view.set_index("time")[["river_m"]].rename(columns={"river_m":"Baseline"})
    scenario["Shifted scenario"] = scenario.Baseline + offset
    scenario["Hypothetical threshold"] = threshold
    st.line_chart(scenario, y_label="River level (m)")
    exceed = scenario["Shifted scenario"].ge(threshold)
    st.metric("Simulated hourly readings at or above threshold", f"{exceed.sum()} / {len(exceed)}")
    st.caption("A uniform level shift is an illustrative assumption and has no calibrated hydrological meaning.")

else:
    st.subheader("Research evaluation plan")
    st.info("No observed flood-event labels are available. Accuracy, missed-event rates and false-alarm rates cannot yet be estimated.")
    a,b = st.columns(2)
    a.metric("Expected hourly records per site", 720)
    b.metric("Missing simulated measurements", int(data[["river_m","rain_mm"]].isna().sum().sum()))
    st.markdown("""Before field evaluation:
- Obtain community participation agreements and define data governance.
- Calibrate sensors and document local reference levels.
- Collect independently verified event times and locations.
- Define evaluation windows and separate calibration and validation periods.
- Measure false alarms, missed events, lead time, usability and maintenance costs.
""")
    st.dataframe(data.groupby("site").agg(records=("time","size"), first_reading=("time","min"), last_reading=("time","max")), use_container_width=True)

st.divider()
st.caption("Prototype scope: synthetic monitoring, session-only observations, threshold sensitivity and evaluation planning. No operational alert delivery.")
