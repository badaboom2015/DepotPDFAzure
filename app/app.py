import streamlit as st
from portfolio.importer import read_uploaded_file
from portfolio.analyzer import analyze_portfolio
from portfolio.commentary import generate_commentary
from portfolio.storage import save_uploaded_file_if_configured

st.set_page_config(page_title="CSS Portfolio Analyzer", layout="wide")
st.title("CSS Portfolio Analyzer")
st.caption("Azure PaaS MVP for depot statement analysis – no investment advice.")

uploaded_file = st.file_uploader("Upload depot statement", type=["csv", "pdf"])

if uploaded_file:
    try:
        saved_uri = save_uploaded_file_if_configured(uploaded_file)
        positions = read_uploaded_file(uploaded_file)
        result = analyze_portfolio(positions)
        comment = generate_commentary(result)

        st.success("File imported and positions detected.")
        if saved_uri:
            st.caption(f"Stored in Blob Storage: {saved_uri}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total portfolio value", f"{result.total_value:,.2f}")
        col2.metric("Positions", len(result.positions))
        col3.metric("Largest position", f"{result.max_weight:.1f}%")

        st.subheader("Structured positions")
        st.dataframe(result.positions, use_container_width=True)

        st.subheader("Top 5 positions")
        st.dataframe(result.top5, use_container_width=True)

        st.subheader("Concentration risks")
        if result.risks:
            for risk in result.risks:
                st.warning(risk)
        else:
            st.success("No obvious concentration risks detected.")

        st.subheader("AI-style investor comment")
        st.write(comment)

    except Exception as exc:
        st.error(f"Processing failed: {exc}")
else:
    st.info("Upload a CSV/PDF file. Demo file: samples/sample_depot.csv")
