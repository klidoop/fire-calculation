#@title Full FIRE Calculator App with Retirement, Inflation, Scenarios, and Export
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

st.set_page_config(page_title="FIRE Calculator", layout="centered")
st.title("🔥 FIRE (Financial Independence, Retire Early) Calculator")

# --- Inputs ---
st.header("Input Your Financial Info")
col1, col2 = st.columns(2)
with col1:
    annual_expenses = st.number_input("Annual Expenses ($) - No Kid", value=40000, step=1000)
    current_savings = st.number_input("Current Savings ($)", value=50000, step=1000)
    annual_savings = st.number_input("Annual Savings ($)", value=15000, step=1000)
    return_rate = st.number_input("Expected Return Before FIRE (%)", value=5.0, step=0.1) / 100
    inflation_rate = st.number_input("Expected Inflation Rate (%)", value=2.0, step=0.1) / 100
with col2:
    withdrawal_rate = st.number_input("Withdrawal Rate (%)", value=4.0, step=0.1) / 100
    retirement_return = st.number_input("Return During Retirement (%)", value=4.0, step=0.1) / 100
    retirement_years = st.number_input("Planned Retirement Duration (years)", value=30, step=1)
    expense_reduction = st.number_input("% Expense Reduction in FIRE (0 = none)", value=0.0, step=1.0)
    enable_download = st.checkbox("Enable CSV Export", value=True)

have_kid = st.checkbox("Add scenario: Have Kid", value=True)
if have_kid:
    st.markdown("### Additional Info for 'Have Kid' Scenario")
    kid_expense = st.number_input("Estimated Annual Expenses with Kid ($)", value=60000, step=1000)
    kid_savings = st.number_input("Annual Savings with Kid ($)", value=10000, step=1000)

part_time = st.checkbox("Add scenario: Part-Time Work in Retirement", value=True)
if part_time:
    st.markdown("### Additional Info for Part-Time Scenario")
    pt_income = st.number_input("Annual Part-Time Income in Retirement ($)", value=10000, step=1000)

# --- Scenario Function ---
def simulate_fire(expenses, savings, yearly_savings, label, pt_income=0):
    adjusted_expenses = expenses * (1 - expense_reduction / 100)
    fire_number = adjusted_expenses / withdrawal_rate
    projection = []
    total = savings
    year = 0

    while total < fire_number and year < 100:
        projection.append({"Year": year, "Savings": total, "Scenario": label})
        total = total * (1 + return_rate) + yearly_savings
        year += 1

    projection.append({"Year": year, "Savings": total, "Scenario": label})
    accumulated_years = year

    for i in range(1, retirement_years + 1):
        annual_draw = max(0, adjusted_expenses * ((1 + inflation_rate) ** i) - pt_income)
        total = total * (1 + retirement_return) - annual_draw
        projection.append({"Year": accumulated_years + i, "Savings": total, "Scenario": label})

    return pd.DataFrame(projection), fire_number, accumulated_years

# --- Run Simulations ---
df_list = []

# No Kid
df1, fire1, years1 = simulate_fire(annual_expenses, current_savings, annual_savings, "No Kid")
df_list.append(df1)

# With Kid
if have_kid:
    df2, fire2, years2 = simulate_fire(kid_expense, current_savings, kid_savings, "With Kid")
    df_list.append(df2)

# Part-Time Work
if part_time:
    df3, fire3, years3 = simulate_fire(annual_expenses, current_savings, annual_savings, "Part-Time Work", pt_income=pt_income)
    df_list.append(df3)

# --- Display Results ---
df = pd.concat(df_list, ignore_index=True)

scenarios = df["Scenario"].unique()
cols = st.columns(len(scenarios))
for i, scenario in enumerate(scenarios):
    sub = df[df["Scenario"] == scenario]
    fire = sub[sub["Year"] == sub["Year"].min()]["Savings"].iloc[-1] * (1 + withdrawal_rate)
    years = sub["Year"].max() - retirement_years
    with cols[i]:
        st.metric(f"FIRE Number ({scenario})", f"${fire:,.0f}")
        st.metric(f"Years to FIRE ({scenario})", years)

# --- Chart ---
st.line_chart(df.pivot(index="Year", columns="Scenario", values="Savings"), use_container_width=True)

# --- Table ---
with st.expander("📅 Year-by-Year Details"):
    st.dataframe(df)

# --- Download ---
if enable_download:
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="fire_projection.csv">📥 Download CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

# --- Notes ---
st.markdown("""
---
### About This App
This tool helps you:
- Estimate your FIRE number with or without a kid
- Project timelines to reach FIRE
- Model post-retirement drawdown with inflation and part-time income
- Compare side-by-side outcomes
""")
