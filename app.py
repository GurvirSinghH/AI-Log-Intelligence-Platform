import streamlit as st

import analyzer
import anomaly_detector
import clustering
import feature_engineering
import log_parser
import search
import visualizer
import prompt_builder
import llm_summary

st.set_page_config(
    page_title="AI Log Intelligence Platform",
    page_icon="log.png",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_and_parse(raw_text):
    return log_parser.parse_logs(raw_text)


@st.cache_data(show_spinner=False)
def build_features(parsed_df):
    return feature_engineering.create_features(parsed_df)


@st.cache_data(show_spinner=False)
def score_anomalies(feature_df):
    return anomaly_detector.detect_anomalies(feature_df)


@st.cache_data(show_spinner=False)
def cluster_anomalies(scored_df):
    return clustering.cluster_logs(scored_df)


#sidebar
with st.sidebar:
    st.header("Log Intelligence")
    st.caption("Upload a Linux syslog file to parse, analyze, and detect anomalies.")
    uploaded_file = st.file_uploader("Log file", type=["log", "txt"])
    st.divider()
    st.caption("Built with Streamlit · scikit-learn · Plotly")


st.title("AI Log Intelligence Platform")

if uploaded_file is None:
    st.info("Upload a `.log` or `.txt` syslog file from the sidebar to begin.")
    st.stop()

#read+parse
try:
    raw_text = uploaded_file.read().decode("utf-8", errors="replace")
except Exception as exc:  # pragma: no cover - defensive
    st.error(f"Could not read the uploaded file: {exc}")
    st.stop()

with st.spinner("Parsing logs..."):
    parsed_df = load_and_parse(raw_text)

if parsed_df.empty:
    st.warning(
        "No lines matched the expected syslog format "
        "`Month Day HH:MM:SS host process(module)[pid]: message`. "
        "Please upload a compatible Linux syslog file."
    )
    st.stop()

st.success(f"Parsed {len(parsed_df):,} log entries successfully.")


#ML pipeline
try:
    with st.spinner("Engineering features and detecting anomalies..."):
        feature_df = build_features(parsed_df)
        scored_df = score_anomalies(feature_df)
        clustered_df = cluster_anomalies(scored_df)
except Exception as exc:
    st.error(f"Analysis failed: {exc}")
    st.stop()

display_df = parsed_df.assign(
    anomaly=scored_df["anomaly"].values,
    cluster=clustered_df["cluster"].values,
)
anomalies_df = display_df[display_df["anomaly"] == 1]

total_logs = len(display_df)
n_anomalies = len(anomalies_df)
anomaly_rate = (n_anomalies / total_logs * 100) if total_logs else 0.0


#tabs
tab_overview, tab_logs, tab_charts, tab_anomaly, tab_cluster, tab_report = st.tabs(
    ["Overview", "Parsed Logs", "Visualizations", "Anomaly Detection", "Clustering", "AI Report"]
)

with tab_overview:
    st.subheader("Log Summary")
    stats = analyzer.analyze_log(parsed_df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Logs", f"{stats['Total Logs']:,}")
    c2.metric("Unique Hosts", stats["Unique Hosts"])
    c3.metric("Unique Processes", stats["Unique Processes"])

    c4, c5, c6 = st.columns(3)
    c4.metric("Unique Messages", stats["Unique Messages"])
    c5.metric("Anomalies", f"{n_anomalies:,}")
    c6.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")

    st.divider()
    st.write(f"**Most common process:** `{stats['Most Common Process']}`")
    st.write(f"**Most common message:** {stats['Most Common Message']}")

with tab_logs:
    st.subheader("Parsed Log Entries")
    st.caption("Logs parsed into structured fields. Search filters by message text.")

    search_term = st.text_input(
        "Search messages", placeholder="e.g. authentication failure"
    )
    filtered = search.search_logs(display_df, search_term)
    if search_term:
        st.info(f"{len(filtered):,} of {total_logs:,} entries match “{search_term}”.")

    st.dataframe(filtered, width="stretch", height=420)

with tab_charts:
    st.subheader("Log Distributions")
    st.plotly_chart(visualizer.plot_process_distribution(parsed_df), width="stretch")

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(visualizer.plot_host_distribution(parsed_df), width="stretch")
    with col_b:
        st.plotly_chart(visualizer.plot_message_distribution(parsed_df), width="stretch")

with tab_anomaly:
    st.subheader("Isolation Forest Anomaly Detection")

    m1, m2, m3 = st.columns(3)
    m1.metric("Normal", f"{total_logs - n_anomalies:,}")
    m2.metric("Anomalous", f"{n_anomalies:,}")
    m3.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")

    st.plotly_chart(visualizer.plot_anomaly_scatter(scored_df), width="stretch")

    st.markdown("**Anomalous log entries**")
    if anomalies_df.empty:
        st.info("No anomalies detected in this log set.")
    else:
        st.dataframe(anomalies_df, width="stretch", height=360)

with tab_cluster:
    st.subheader("Anomaly Clustering (KMeans)")

    clustered_anomalies = display_df[display_df["cluster"] != -1]
    if clustered_anomalies.empty:
        st.info("Not enough anomalies to form clusters (at least 2 are required).")
    else:
        sizes = clustered_anomalies["cluster"].value_counts().sort_index()
        cols = st.columns(len(sizes))
        for col, (cluster_id, size) in zip(cols, sizes.items()):
            col.metric(f"Cluster {int(cluster_id)}", f"{size:,}")

        st.dataframe(
            clustered_anomalies.sort_values("cluster"),
            width="stretch", height=360,
        )

with tab_report:
    st.subheader("AI Incident Report")
    st.caption(
        "A short report written by an LLM (Google Gemini) from the statistics, "
        "anomalies, clusters, and a few example logs - the raw log file is never sent."
    )

    stats = analyzer.analyze_log(parsed_df)
    prompt = prompt_builder.build_prompt(stats, display_df, anomalies_df)

    with st.expander("See the exact text sent to the LLM"):
        st.text(prompt)

    if st.button("Generate Incident Report"):
        with st.spinner("Asking Gemini to write the report..."):
            try:
                report = llm_summary.generate_incident_report(prompt)
                st.success("Report generated.")
                st.markdown(report)
            except Exception as exc:
                st.error(f"Could not generate the report: {exc}")
