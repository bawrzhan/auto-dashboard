# ------------------------------------------------------------------
# Auto dashboard (Streamlit).  Question it answers:
#   "Did cars become more fuel efficient between 1970 and 1982,
#    and is that explained by weight, engine size or country of origin?"
# Linked visuals: select points (box / lasso) on the scatter plot and the
# other charts + the KPI numbers update to show only those cars.
# Filters: origin, model year, cylinders (sidebar).
# ------------------------------------------------------------------
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Auto dashboard", layout="wide")

# ---------- 1. Load data (local CSV, or the textbook's GitHub copy) ----------
URL = "https://raw.githubusercontent.com/intro-stat-learning/ISLP/main/ISLP/data/Auto.csv"


@st.cache_data
def load_auto() -> pd.DataFrame:
    here = Path(__file__).parent
    for p in (here / "Auto.csv", here / "data" / "Auto.csv", here.parent / "data" / "Auto.csv"):
        if p.exists():
            df = pd.read_csv(p)
            break
    else:
        df = pd.read_csv(URL)
    df = df.dropna().reset_index(drop=True)
    df["origin_name"] = df["origin"].map({1: "American", 2: "European", 3: "Japanese"})
    df["year_full"] = 1900 + df["year"]
    df["id"] = df.index
    return df


auto = load_auto()

# ---------- 2. Sidebar filters ----------
st.sidebar.header("Filters")
origins = st.sidebar.multiselect(
    "Origin", ["American", "European", "Japanese"], default=["American", "European", "Japanese"]
)
years = st.sidebar.slider("Model year", 1970, 1982, (1970, 1982))
all_cyls = sorted(auto["cylinders"].unique())
cyls = st.sidebar.multiselect("Cylinders", all_cyls, default=all_cyls)

filtered = auto[
    auto["origin_name"].isin(origins)
    & auto["year_full"].between(*years)
    & auto["cylinders"].isin(cyls)
]

st.title("Fuel economy of cars, 1970 to 1982")
st.markdown(
    "**Question:** did cars become more fuel efficient, and is it because they got "
    "lighter or because more small foreign cars were sold?  \n"
    "**How to use it:** change the filters on the left. Then draw a box or lasso on the "
    "scatter plot (chart A): the other charts and the numbers show only the cars you selected."
)

if filtered.empty:
    st.warning("No cars match these filters. Widen the filters on the left.")
    st.stop()

# ---------- 3. Chart A: scatter (the 'control' chart) ----------
colors = {"American": "#1f77b4", "European": "#2ca02c", "Japanese": "#d62728"}
left, right = st.columns(2)

with left:
    st.subheader("A. Weight vs fuel economy (select here)")
    fig_a = px.scatter(
        filtered, x="weight", y="mpg", color="origin_name", color_discrete_map=colors,
        custom_data=["id"], hover_name="name",
        labels={"weight": "Weight (lbs)", "mpg": "Miles per gallon", "origin_name": "Origin"},
    )
    fig_a.update_layout(dragmode="lasso", margin=dict(t=10, b=10), legend_title_text="")
    event = st.plotly_chart(
        fig_a, key="scatter", on_select="rerun", selection_mode=("box", "lasso"),
        width="stretch",
    )

# Which cars did the user select?  (empty selection = all filtered cars)
try:
    selected_ids = [p["customdata"][0] for p in event.selection["points"]]
except Exception:
    selected_ids = []
view = filtered[filtered["id"].isin(selected_ids)] if selected_ids else filtered
if view.empty:  # selection made before a filter change
    view = filtered
    selected_ids = []

# ---------- 4. KPI numbers ----------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Cars shown", len(view))
k2.metric("Mean mpg", f"{view['mpg'].mean():.1f}")
k3.metric("Mean horsepower", f"{view['horsepower'].mean():.0f}")
k4.metric("Mean weight (lbs)", f"{view['weight'].mean():.0f}")
if selected_ids:
    st.caption(f"Showing the {len(view)} cars selected in chart A.")

# ---------- 5. Chart B: histogram ----------
with right:
    st.subheader("B. How are mpg values spread?")
    fig_b = px.histogram(
        view, x="mpg", nbins=25, color="origin_name", color_discrete_map=colors,
        labels={"mpg": "Miles per gallon", "origin_name": "Origin"},
    )
    fig_b.update_layout(barmode="stack", margin=dict(t=10, b=10), legend_title_text="")
    st.plotly_chart(fig_b, width="stretch")

# ---------- 6. Chart C: boxplot, Chart D: line ----------
c3, c4 = st.columns(2)
with c3:
    st.subheader("C. mpg by number of cylinders")
    fig_c = px.box(
        view, x="cylinders", y="mpg", points="all",
        labels={"cylinders": "Cylinders", "mpg": "Miles per gallon"},
    )
    fig_c.update_layout(margin=dict(t=10, b=10))
    fig_c.update_xaxes(type="category")
    st.plotly_chart(fig_c, width="stretch")

with c4:
    st.subheader("D. Average mpg by model year")
    by_year = view.groupby(["year_full", "origin_name"], as_index=False)["mpg"].mean()
    fig_d = px.line(
        by_year, x="year_full", y="mpg", color="origin_name", markers=True,
        color_discrete_map=colors,
        labels={"year_full": "Model year", "mpg": "Average mpg", "origin_name": "Origin"},
    )
    fig_d.update_layout(margin=dict(t=10, b=10), legend_title_text="")
    st.plotly_chart(fig_d, width="stretch")

st.caption("Data: Auto data set from the ISLP textbook (392 cars).")
