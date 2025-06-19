#@title Full FIRE Calculator App with Retirement, Inflation, Scenarios, and Export
import streamlit as st
import pandas as pd
from io import BytesIO
import base64

st.set_page_config(page_title="FIRE Calculator", layout="centered")
st.title("🔥 FIRE (Financial Independence, Retire Early) Calculator")

# --- Inputs ---
st.header("Input Your Financial Info")
col1, col2 = st.columns(2)
with col1:
    current_age = st.number_input("Your Current Age", value=30, step=1)
    expected_lifespan = st.number_input("Expected Age at Death", value=90, step=1)
    annual_expenses = st.number_input("Annual Expenses ($) - No Kid", value=40000, step=1000)
    current_savings = st.number_input("Current Savings ($)", value=50000, step=1000)
    annual_savings = st.number_input("Annual Savings ($)", value=15000, step=1000)
    return_rate = st.number_input("Expected Return Before FIRE (%)", value=5.0, step=0.1) / 100
    inflation_rate = st.number_input("Expected Inflation Rate (%)", value=2.0, step=0.1) / 100
with col2:
    withdrawal_rate = st.number_input("Withdrawal Rate (%)", value=4.0, step=0.1) / 100
    retirement_return = st.number_input("Return During Retirement (%)", value=4.0, step=0.1) / 100
    expense_reduction = st.number_input("% Expense Reduction in FIRE (0 = none)", value=0.0, step=1.0)
    enable_download = st.checkbox("Enable CSV Export", value=True)

have_kid = st.checkbox("Add scenario: Have Kid", value=True)
if have_kid:
    st.markdown("### Additional Info for 'Have Kid' Scenario")
    kid_start_age = st.number_input("Age When Kid Is Born", value=32, step=1)
    kid_support_years = st.number_input("Years of Child-Related Expenses", value=23, step=1)
    kid_expense = st.number_input("Estimated Annual Expenses with Kid ($)", value=60000, step=1000)
    kid_savings = st.number_input("Annual Savings with Kid ($)", value=10000, step=1000)

part_time = st.checkbox("Add scenario: Part-Time Work in Retirement", value=True)
if part_time:
    st.markdown("### Additional Info for Part-Time Scenario")
    pt_income = st.number_input("Annual Part-Time Income in Retirement ($)", value=10000, step=1000)

# --- Scenario Function ---
def simulate_fire(expenses, savings, yearly_savings, label, pt_income=0, kid_start_age=None, kid_end_age=None, kid_expense=None, base_expense=None, kid_savings=None):
    if base_expense is None:
        base_expense = expenses

    projection = []
    total = savings
    year = 0

    while True:
        age = current_age + year
        if age >= expected_lifespan:
            return pd.DataFrame([], columns=["Age", "Savings", "Scenario"]), 0, 0

        # Pre-retirement expense and savings logic
        if kid_start_age and kid_start_age <= age < kid_end_age:
            expense_now = kid_expense
            savings_now = kid_savings
        else:
            expense_now = expenses
            savings_now = yearly_savings

        adjusted_expense = expense_now * (1 - expense_reduction / 100)
        projection.append({"Age": age, "Savings": total, "Scenario": label})
        total = total * (1 + return_rate) + savings_now
        year += 1

        retire_savings = total
        success = True
        for i in range(1, expected_lifespan - age + 1):
            check_age = age + i
            if kid_start_age and kid_start_age <= check_age < kid_end_age:
                use_expense = kid_expense
            else:
                use_expense = base_expense
            use_expense = use_expense * (1 - expense_reduction / 100)
            annual_draw = max(0, use_expense * ((1 + inflation_rate) ** i) - pt_income)
            retire_savings = retire_savings * (1 + retirement_return) - annual_draw
            if retire_savings < 0:
                success = False
                break

        if success:
            break

    for i in range(1, expected_lifespan - age + 1):
        check_age = age + i
        if kid_start_age and kid_start_age <= check_age < kid_end_age:
            use_expense = kid_expense
        else:
            use_expense = base_expense
        use_expense = use_expense * (1 - expense_reduction / 100)
        draw = max(0, use_expense * ((1 + inflation_rate) ** i) - pt_income)
        total = total * (1 + retirement_return) - draw
        projection.append({"Age": check_age, "Savings": total, "Scenario": label})

    fire_number = projection[-(expected_lifespan - age + 1)]["Savings"]
    return pd.DataFrame(projection), fire_number, age

# --- Run Simulations ---
df_list = []
summary_metrics = []

# No Kid
df1, fire1, age1 = simulate_fire(annual_expenses, current_savings, annual_savings, "No Kid")
df_list.append(df1)
summary_metrics.append(("No Kid", fire1, age1))

# With Kid
if have_kid:
    kid_end_age = kid_start_age + kid_support_years
    df2, fire2, age2 = simulate_fire(
        annual_expenses,
        current_savings,
        annual_savings,
        "With Kid",
        pt_income=pt_income if part_time else 0,
        kid_start_age=kid_start_age,
        kid_end_age=kid_end_age,
        kid_expense=kid_expense,
        base_expense=annual_expenses,
        kid_savings=kid_savings
    )
    df_list.append(df2)
    summary_metrics.append(("With Kid", fire2, age2))

# Part-Time Work
if part_time:
    df3, fire3, age3 = simulate_fire(annual_expenses, current_savings, annual_savings, "Part-Time Work", pt_income=pt_income)
    df_list.append(df3)
    summary_metrics.append(("Part-Time Work", fire3, age3))

# --- Display Results ---
df = pd.concat(df_list, ignore_index=True)

cols = st.columns(len(summary_metrics))
for i, (scenario, fire_val, retire_age) in enumerate(summary_metrics):
    with cols[i]:
        st.metric(f"FIRE Number ({scenario})", f"${fire_val:,.0f}")
        st.metric(f"You can retire at age ({scenario})", f"{retire_age}")

# --- Chart ---
st.line_chart(df.pivot(index="Age", columns="Scenario", values="Savings"), use_container_width=True)

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
- Specify when the child is born and how long expenses last
- Model transitions from kid-related to normal expenses accurately
- Calculate the earliest retirement age that results in $0 at your chosen death age
- Compare side-by-side scenarios including part-time income
""")
