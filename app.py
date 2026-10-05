import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from io import BytesIO
from database import init_db, save_daily_record, bulk_insert_records, get_all_generation_data, get_plant_settings, update_plant_settings
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Initialize Database
init_db()

# Page Setup
st.set_page_config(page_title="Pankaj Solars | Solar Generation Portal", page_icon="⚡", layout="wide")

# Custom Styling (CSS)
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #0d47a1 0%, #1976d2 100%);
        padding: 24px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .main-header h1 { color: #ffffff !important; margin: 0; }
    .main-header p { color: #e0e0e0 !important; margin-top: 5px; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
    <div class="main-header">
        <h1>⚡ Pankaj Solars - Generation Analytics Portal</h1>
        <p>Location: Noida, Uttar Pradesh | Official Performance & Reporting Platform</p>
    </div>
""", unsafe_allow_html=True)

# Load Saved Settings
saved_capacity, saved_tariff = get_plant_settings()

# Sidebar Configuration
st.sidebar.image("https://img.icons8.com/color/96/solar-panel.png", width=80)
st.sidebar.title("⚙️ System Control")
capacity_kwp = st.sidebar.number_input("Plant Capacity (kWp)", min_value=1.0, value=float(saved_capacity), step=5.0)
tariff_rate = st.sidebar.number_input("Tariff Rate (₹ / kWh)", min_value=0.0, value=float(saved_tariff), step=0.5)

if st.sidebar.button("💾 Save Settings", use_container_width=True):
    update_plant_settings(capacity_kwp, tariff_rate)
    st.sidebar.success("Plant Settings Updated!")

# Main Tabs Navigation
tab_dash, tab_entry, tab_monthly, tab_yearly = st.tabs([
    "📊 Executive Dashboard", 
    "➕ Data Input / Upload", 
    "📅 Monthly Generation Report", 
    "📈 Yearly Generation Report"
])

# Fetch Data from DB
df = get_all_generation_data()

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.strftime("%B")
    df["Month_Num"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day

# --- TAB 1: EXECUTIVE DASHBOARD ---
with tab_dash:
    if not df.empty:
        total_gen = df["Generation_kWh"].sum()
        total_revenue = total_gen * tariff_rate
        total_co2 = total_gen * 0.82 / 1000  # Metric Tons

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Lifetime Generation", f"{total_gen:,.1f} kWh")
        c2.metric("Lifetime Cost Savings", f"₹{total_revenue:,.2f}")
        c3.metric("CO₂ Carbon Offset", f"{total_co2:,.2f} Tons")
        c4.metric("Active Capacity", f"{capacity_kwp} kWp")

        st.markdown("---")
        st.subheader("⚡ Generation Overview Over Time")
        fig_overview = px.line(df, x="Date", y="Generation_kWh", title="Daily Generation Trend (kWh)",
                               labels={"Generation_kWh": "Units (kWh)"}, template="plotly_white")
        fig_overview.update_traces(line_color="#1976d2", line_width=2)
        st.plotly_chart(fig_overview, use_container_width=True)
    else:
        st.info("👋 Welcome to Pankaj Solars Portal! Please add data in 'Data Input / Upload' tab to view analytics.")

# --- TAB 2: DATA INPUT / UPLOAD ---
with tab_entry:
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("📝 Manual Entry")
        with st.form("entry_form", clear_on_submit=True):
            input_date = st.date_input("Select Date", datetime.date.today())
            input_kwh = st.number_input("Daily Units Generated (kWh)", min_value=0.0, step=10.0)
            submitted = st.form_submit_button("Save Daily Record")
            
            if submitted:
                save_daily_record(str(input_date), input_kwh)
                st.success(f"Record saved for {input_date}: {input_kwh} kWh")
                st.rerun()

    with col_b:
        st.subheader("📁 Bulk CSV / Excel Upload")
        st.caption("Required File Format: CSV/Excel with column headers 'Date' (YYYY-MM-DD) and 'Generation_kWh'.")
        uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    file_df = pd.read_csv(uploaded_file)
                else:
                    file_df = pd.read_excel(uploaded_file)
                
                file_df['Date'] = pd.to_datetime(file_df['Date']).dt.strftime('%Y-%m-%d')
                bulk_insert_records(file_df)
                st.success("All records imported into database successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to process file: {e}")

# PDF Export Helper Function
def create_pdf_report(report_title, summary_items, table_df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    h_style = ParagraphStyle('HeaderStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#0d47a1"), spaceAfter=4)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=10, textColor=colors.dimgrey)

    story.append(Paragraph("PANKAJ SOLARS", h_style))
    story.append(Paragraph("Address: Noida, Uttar Pradesh | Contact: Official Solar Report", sub_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>{report_title}</b>", styles['Heading2']))
    story.append(Paragraph(f"Generated Date: {datetime.date.today().strftime('%d %B, %Y')}", sub_style))
    story.append(Spacer(1, 15))

    # Metrics Summary Box
    t_summary = Table(summary_items, colWidths=[220, 280])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))

    # Data Table
    table_data = [table_df.columns.tolist()] + table_df.astype(str).values.tolist()
    t_data = Table(table_data)
    t_data.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0d47a1")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_data)

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- TAB 3: MONTHLY REPORT ---
with tab_monthly:
    if not df.empty:
        col_y, col_m = st.columns(2)
        with col_y:
            sel_year = st.selectbox("Select Year ", sorted(df["Year"].unique(), reverse=True), key="m_year")
        with col_m:
            avail_months = df[df["Year"] == sel_year]["Month"].unique()
            sel_month = st.selectbox("Select Month", avail_months, key="m_month")

        m_filtered = df[(df["Year"] == sel_year) & (df["Month"] == sel_month)].sort_values("Date")
        
        m_total = m_filtered["Generation_kWh"].sum()
        m_avg = m_filtered["Generation_kWh"].mean()
        m_max = m_filtered["Generation_kWh"].max()
        m_savings = m_total * tariff_rate
        m_co2 = m_total * 0.82

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Monthly Total", f"{m_total:,.1f} kWh")
        mc2.metric("Daily Average", f"{m_avg:,.1f} kWh")
        mc3.metric("Peak Generation", f"{m_max:,.1f} kWh")
        mc4.metric("Estimated Savings", f"₹{m_savings:,.2f}")

        st.subheader(f"📊 Daily Breakdown - {sel_month} {sel_year}")
        fig_m = px.bar(m_filtered, x="Day", y="Generation_kWh", text_auto=True,
                       labels={"Day": "Day of Month", "Generation_kWh": "kWh"},
                       title=f"{sel_month} {sel_year} Daily Generation Chart")
        fig_m.update_traces(marker_color="#1976d2")
        st.plotly_chart(fig_m, use_container_width=True)

        # PDF Download Button
        pdf_summary = [
            ["Company Name", "Pankaj Solars"],
            ["Plant Location", "Noida, UP"],
            ["System Capacity", f"{capacity_kwp} kWp"],
            ["Total Monthly Units", f"{m_total:,.2f} kWh"],
            ["Daily Average Units", f"{m_avg:,.2f} kWh"],
            ["Estimated Electricity Bill Savings", f"Rs. {m_savings:,.2f}"],
            ["Carbon Footprint Offset", f"{m_co2:,.2f} kg CO2"]
        ]
        
        export_df = m_filtered[["Date", "Generation_kWh"]].copy()
        export_df["Date"] = export_df["Date"].dt.strftime('%Y-%m-%d')
        
        pdf_bytes = create_pdf_report(f"Monthly Solar Generation Report ({sel_month} {sel_year})", pdf_summary, export_df)

        st.download_button(
            label="📄 Download Official Monthly PDF Report",
            data=pdf_bytes,
            file_name=f"Pankaj_Solars_Monthly_Report_{sel_month}_{sel_year}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("No data available to generate monthly report.")

# --- TAB 4: YEARLY REPORT ---
with tab_yearly:
    if not df.empty:
        sel_year_y = st.selectbox("Select Year", sorted(df["Year"].unique(), reverse=True), key="y_year")
        
        y_filtered = df[df["Year"] == sel_year_y]
        y_grouped = y_filtered.groupby(["Month_Num", "Month"])["Generation_kWh"].sum().reset_index().sort_values("Month_Num")
        
        y_total = y_grouped["Generation_kWh"].sum()
        y_savings = y_total * tariff_rate
        y_co2 = y_total * 0.82 / 1000  # Tons

        yc1, yc2, yc3 = st.columns(3)
        yc1.metric("Annual Total Generation", f"{y_total:,.1f} kWh")
        yc2.metric("Annual Electricity Savings", f"₹{y_savings:,.2f}")
        yc3.metric("Annual Carbon Reduction", f"{y_co2:,.2f} Metric Tons")

        st.subheader(f"📈 Monthly Breakdown - Year {sel_year_y}")
        fig_y = px.bar(y_grouped, x="Month", y="Generation_kWh", text_auto=True,
                       title=f"Year {sel_year_y} Monthly Generation Trend",
                       labels={"Generation_kWh": "Total Units (kWh)"})
        fig_y.update_traces(marker_color="#0d47a1")
        st.plotly_chart(fig_y, use_container_width=True)

        # PDF Download Button
        pdf_y_summary = [
            ["Company Name", "Pankaj Solars"],
            ["Plant Location", "Noida, UP"],
            ["System Capacity", f"{capacity_kwp} kWp"],
            ["Total Annual Generation", f"{y_total:,.2f} kWh"],
            ["Total Cost Savings", f"Rs. {y_savings:,.2f}"],
            ["Carbon Offset", f"{y_co2:,.2f} Metric Tons CO2"]
        ]
        
        pdf_y_bytes = create_pdf_report(f"Annual Solar Generation Report ({sel_year_y})", pdf_y_summary, y_grouped[["Month", "Generation_kWh"]])

        st.download_button(
            label="📄 Download Official Yearly PDF Report",
            data=pdf_y_bytes,
            file_name=f"Pankaj_Solars_Annual_Report_{sel_year_y}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("No data available to generate yearly report.")
