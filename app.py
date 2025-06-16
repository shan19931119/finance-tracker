import streamlit as st
import pandas as pd
from datetime import date
import os

# --- SETTINGS ---
DATA_FILE = "data.csv"
BANKS = ["Commercial Bank", "DFCC Bank", "Sampath Bank", "BOC"]

# --- PAGE SETUP ---
st.set_page_config(page_title="Villa by 11.11 - Finance Tracker", layout="wide")
st.title("Finance Tracker")

# --- LOAD DATA ---
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Date", "Category", "Type", "Amount", "Note", "Bank", "Paid From Bank", "Purpose"
    ])

# --- FORMAT DATA ---
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

# --- CALCULATE BANK BALANCES ---
bank_balances = {bank: 0 for bank in BANKS}

for _, row in df.iterrows():
    if row["Type"] == "Income" and row["Bank"] in BANKS:
        bank_balances[row["Bank"]] += row["Amount"]
    elif row["Type"] == "Expense" and row["Paid From Bank"] in BANKS:
        bank_balances[row["Paid From Bank"]] -= row["Amount"]

# --- DISPLAY BANK BALANCES ---
st.subheader("🏦 Bank Balances")
col1, col2, col3, col4 = st.columns(4)
for i, bank in enumerate(BANKS):
    formatted_amount = f"Rs. {bank_balances[bank]:,.2f}"
    with [col1, col2, col3, col4][i]:
        st.metric(label=bank, value=formatted_amount)

st.markdown(f"🕒 _Last updated on: {date.today().strftime('%B %d, %Y')}_")
st.divider()

# --- ADD ENTRY FORM ---
st.subheader("➕ Add New Entry")
with st.form("entry_form"):
    entry_date = st.date_input("Date", date.today())
    category = st.selectbox("Category", ["Villa", "Personal"])
    entry_type = st.selectbox("Type", ["Income", "Expense"])
    amount = st.number_input("Amount (LKR)", min_value=0.0, step=100.0)
    note = st.text_input("Note")

    bank = ""
    paid_from = ""
    purpose = ""

    if entry_type == "Income":
        bank = st.selectbox("Deposit To Bank", BANKS)
    else:
        purpose = st.text_input("Purpose of Payment")
        paid_from = st.selectbox("Paid From Bank", BANKS)

    submitted = st.form_submit_button("✅ Save Entry")

    if submitted:
        new_row = {
            "Date": entry_date,
            "Category": category,
            "Type": entry_type,
            "Amount": amount,
            "Note": note,
            "Bank": bank if entry_type == "Income" else "",
            "Paid From Bank": paid_from if entry_type == "Expense" else "",
            "Purpose": purpose if entry_type == "Expense" else ""
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Entry saved successfully!")
        st.rerun()  # ✅ CORRECT PLACEMENT

# --- SHOW TABLE ---
st.subheader("📋 All Entries")
st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
# --- SAVINGS & GROWTH LINE CHART ---
st.subheader("📈 Finance Growth Overview")

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Total income across all banks
    income_df = df[df["Type"] == "Income"]
    income_grouped = income_df.groupby("Date")["Amount"].sum()

    # Total villa expenses (Category = Villa + Type = Expense)
    villa_expense_df = df[(df["Category"] == "Villa") & (df["Type"] == "Expense")]
    villa_expense_grouped = villa_expense_df.groupby("Date")["Amount"].sum()

    # Total personal expenses (Category = Personal + Type = Expense)
    personal_expense_df = df[(df["Category"] == "Personal") & (df["Type"] == "Expense")]
    personal_expense_grouped = personal_expense_df.groupby("Date")["Amount"].sum()

    # BOC savings
    boc_df = df[(df["Type"] == "Income") & (df["Bank"] == "BOC")]
    boc_df["Date"] = pd.to_datetime(boc_df["Date"])
    boc_savings = boc_df.groupby("Date")["Amount"].sum().cumsum()

    # Merge all into a single DataFrame
    chart_df = pd.DataFrame({
        "Income (LKR)": income_grouped,
        "Villa Expenses (LKR)": villa_expense_grouped,
        "Personal Expenses (LKR)": personal_expense_grouped,
        "Savings (BOC)": boc_savings
    }).fillna(0)

    chart_df = chart_df.sort_index()
    chart_df = chart_df.cumsum()  # show cumulative growth

    st.line_chart(chart_df, use_container_width=True)
else:
    st.info("No financial data yet. Add entries to see the chart.")
