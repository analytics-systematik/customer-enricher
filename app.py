import streamlit as st
import pandas as pd
import io

# ==========================================
# TEXT CONFIGURATION
# ==========================================
APP_CONFIG = {
    "title": "Customer Demographics Enricher",
    
    "subtitle": """
<p style="font-size: 20px; line-height: 1.5; color: #1A1A1A; margin-bottom: 20px;">
Stop guessing who your customers are. 
Instantly enrich your customer list with Census-level income and demographic data to build better ad audiences and understand your buyer persona.
</p>
""",
    
    "privacy_notice": "🔒 **Your data is safe. The analysis runs entirely in this secure session — we never see, store, or save your files.**",
    
    # Sidebar Text
    "sidebar_header": "Settings",
    "filter_label": "Exclude low population areas",
    "filter_help": "If checked, the analysis will ignore Zip Codes with fewer than 100 residents to prevent statistical outliers.",
    
    "brand_header": "Powered by Systematik",
    "brand_info": "Full-stack data agency for ecommerce brands earning $5M-100M annually.",
    "brand_email": "info@systematikdata.com",
    
    "instructions_title": "Instructions & caveats",
    "video_link": "https://www.youtube.com", 
    "video_text": "Watch the video walkthrough",
    
    "instructions_intro": """
1. Export your customer list as a CSV or Excel file.
2. Ensure the file contains a `zip_code` column.
3. Include `customer_id` or `email` so you can map the data back to your system.
4. Drag and drop the file below.

### Important caveats
* **US customers only:** This tool uses US Census data. International zip codes will not match.
* **Match rates:** You can expect a ~90-95% match rate. Zip codes for PO Boxes or large office buildings often do not have residential Census data.
""",
    
    "success_msg": "Enrichment complete. Processed {n} rows with a {r}% match rate.",
    "error_msg": "Error: Could not detect a Zip Code column. Please rename your header to 'Zip' or 'Postal Code'."
}

# ==========================================
# APP LOGIC
# ==========================================

st.set_page_config(
    page_title=APP_CONFIG["title"],
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD EXTERNAL CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("style.css")
except FileNotFoundError:
    st.warning("Note: style.css not found. UI might look unstyled.")

# --- LOAD CENSUS DATA (Cached) ---
@st.cache_data
def load_census_data():
    try:
        df = pd.read_csv("census_reference.csv")
        df['zip_code'] = df['zip_code'].astype(str).str.zfill(5)
        return df
    except FileNotFoundError:
        return None

census_df = load_census_data()

if census_df is None:
    st.error("CRITICAL ERROR: 'census_reference.csv' not found. Please ensure the reference file is in the repository.")
    st.stop()

# --- HELPER: ROBUST ZIP FINDER ---
def find_zip_column(df):
    # Extensive list of potential headers for Zip Code
    candidates = [
        'zip', 'zipcode', 'zip code', 'zip_code', 
        'postal', 'postal code', 'postal_code', 'postcode', 'post_code',
        'billing zip', 'billing_zip', 'billing postal', 'billing_postal_code',
        'shipping zip', 'shipping_zip', 'shipping postal', 'shipping_postal_code'
    ]
    
    # 1. Exact match (case insensitive)
    for col in df.columns:
        if str(col).lower().strip() in candidates:
            return col
            
    # 2. Fuzzy match (contains keyword)
    for col in df.columns:
        col_lower = str(col).lower()
        for c in candidates:
            if c in col_lower:
                return col
    return None

def clean_zip_codes(series):
    s = series.astype(str).str.split('.').str[0]  
    s = s.str.split('-').str[0]                   
    s = s.str.strip().str.zfill(5)                
    return s

# --- EXCEL GENERATOR ---
def convert_to_excel(df, report_type):
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, startrow=0, sheet_name='Report')
        
        workbook = writer.book
        worksheet = writer.sheets['Report']
        
        from openpyxl.styles import Font, Alignment
        
        bold_font = Font(bold=True, name='Arial', size=11)
        regular_font = Font(name='Arial', size=10)
        purple_link_font = Font(name='Arial', size=10, color="7030A0", underline="single")
        header_font = Font(bold=True, name='Arial', size=14)
        text_align = Alignment(wrap_text=True, vertical='top')
        
        def write_side_block(row, title, text, link=None):
            cell_title = worksheet[f'J{row}']
            cell_title.value = title
            cell_title.font = bold_font
            
            cell_text = worksheet[f'J{row+1}']
            cell_text.value = text
            cell_text.font = regular_font if not link else purple_link_font
            cell_text.alignment = text_align
            if link: cell_text.hyperlink = link

        worksheet['J1'] = "Systematik data — Customer enrichment report"
        worksheet['J1'].font = header_font
        
        worksheet['J2'] = f"Report: {report_type} | Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}"
        worksheet['J2'].font = regular_font

        write_side_block(4, "1. What this report shows", 
                         "We have matched your customer Zip Codes against the US Census Bureau database. You now have the Median Household Income, Median Age, and Total Population for the area where each customer lives.")
        
        write_side_block(8, "2. Actionable strategies", 
                         "• Build 'High earner' segments: Filter this list for Income > $100k. Upload this segment to Meta/Google as a Custom Audience for your premium products.\n"
                         "• Adjust creative strategy: If your Median Age is higher than expected (e.g., 45+), test creative that resonates with an older demographic rather than Gen Z trends.\n"
                         "• Geographic targeting: Identify which specific Zip codes yield your highest value customers and bid more aggressively in those locations.")
        
        write_side_block(16, "3. Important caveats", 
                         "• Geographic Enrichment: This describes the neighborhood profile, not individual credit data.\n"
                         "• Match Rates: Zip codes for PO Boxes or large commercial buildings may not have Census data (showing as N/A).")
        
        write_side_block(21, "4. Need deeper analysis?", 
                         "This is just the start. We can help you calculate Customer Lifetime Value (LTV) by demographic segment to see exactly how much 'High Income' customers are actually worth to your brand.")
        
        write_side_block(25, "Powered by Systematik", 
                         "Full-stack data agency for ecommerce brands ($5M-$100M).")
        
        write_side_block(28, "Visit our website", "systematikdata.com", link="https://go.systematikdata.com/ZA4N87")

        worksheet.column_dimensions['J'].width = 70
        for col in ['F', 'G', 'H', 'I']: worksheet.column_dimensions[col].width = 5
        
        # Auto-fit Data columns
        for i, col in enumerate(df.columns):
             col_letter = chr(65 + i) if i < 26 else 'A' 
             worksheet.column_dimensions[col_letter].width = 18

    return output.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.header(APP_CONFIG["sidebar_header"])
    
    exclude_low_pop = st.checkbox(
        APP_CONFIG["filter_label"],
        value=True,
        help=APP_CONFIG["filter_help"]
    )
    
    st.divider()

    st.markdown(f"""
<div>
<h3 style="color: #7030A0; font-family: 'Outfit', sans-serif;">{APP_CONFIG['brand_header']}</h3>
<div style="background-color: #F2E6FF; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
<p style="margin: 0; color: #1A1A1A; font-weight: 600;">{APP_CONFIG['brand_info']}</p>
</div>
<p style="margin-bottom: 5px; color: #1A1A1A; font-weight: 700;">Free resources:</p>
<ul style="margin-top: 0;">
<li><a href="https://go.systematikdata.com/y4GdSj">Product Mix Analyzer</a></li>
<li><a href="https://go.systematikdata.com/rvisGJ">Data Strategy Guide</a></li>
<li><a href="https://systematikdata.com">Looker Studio Templates</a></li>
<li><a href="https://go.systematikdata.com/IyBNYV">See all..</a></li>
</ul>
<p style="margin-bottom: 5px; color: #1A1A1A; font-weight: 700;">Need a custom build?</p>
<a href="mailto:{APP_CONFIG['brand_email']}">{APP_CONFIG['brand_email']}</a>
</div>
""", unsafe_allow_html=True)

# --- MAIN PAGE ---
st.title(APP_CONFIG["title"])
st.markdown(APP_CONFIG["subtitle"], unsafe_allow_html=True)
st.markdown(APP_CONFIG["privacy_notice"])

with st.expander(APP_CONFIG["instructions_title"], expanded=False):
    st.markdown("### How it works")
    
    st.markdown(f"""
    <a href="{APP_CONFIG['video_link']}" style="color: #7030A0; font-weight: bold; font-size: 1.1em; display: inline-block; margin-bottom: 15px; text-decoration: none;">
        {APP_CONFIG['video_text']}
    </a>
    """, unsafe_allow_html=True)
    
    st.markdown(APP_CONFIG["instructions_intro"])

st.divider()
st.subheader("Upload customer list")
uploaded_file = st.file_uploader("Drag & drop CSV or Excel file here", type=['csv', 'xlsx'], label_visibility="collapsed")

if uploaded_file:
    # 1. PROCESSING PHASE
    # We use a placeholder for variables we need to pass out of the try block
    final_df = None
    match_rate = 0
    total_rows = 0
    avg_income = 0
    avg_age = 0
    
    try:
        with st.spinner("Matching with Census database..."):
            # 1. Load User Data
            if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
            else: df = pd.read_excel(uploaded_file)
            
            # 2. Find Zip Column (Robust Search)
            zip_col = find_zip_column(df)
            
            if not zip_col:
                st.error(APP_CONFIG["error_msg"])
                st.stop()
                
            # 3. Clean User Zips
            df['__join_zip'] = clean_zip_codes(df[zip_col])
            
            # 4. Prepare Census Data
            ref_df = census_df.copy()
            if exclude_low_pop:
                ref_df = ref_df[ref_df['population'] >= 100]
                
            # 5. Perform the Join
            merged = pd.merge(df, ref_df, left_on='__join_zip', right_on='zip_code', how='left')
            
            # 6. Cleanup & Renaming
            merged = merged.rename(columns={
                'median_income': 'Estimated household income',
                'median_age': 'Median age',
                'population': 'Zip population'
            })
            
            cols_to_drop = ['__join_zip', 'zip_code']
            final_df = merged.drop(columns=[c for c in cols_to_drop if c in merged.columns])
            
            # 7. Calculate Metrics
            total_rows = len(final_df)
            matched_rows = final_df['Estimated household income'].notna().sum()
            match_rate = (matched_rows / total_rows) if total_rows > 0 else 0
            
            avg_income = final_df['Estimated household income'].mean()
            avg_age = final_df['Median age'].mean()

    except Exception as e:
        st.error(f"Something went wrong during processing: {e}")
        st.stop()

    # 2. DISPLAY PHASE (Spinner is gone now)
    if final_df is not None:
        st.success(APP_CONFIG["success_msg"].format(n=total_rows, r=round(match_rate * 100, 1)))
        
        # 8. Scorecards
        c1, c2, c3 = st.columns(3)
        c1.metric("Match rate", f"{match_rate:.1%}")
        
        income_display = f"${avg_income:,.0f}" if pd.notna(avg_income) else "N/A"
        c2.metric("Avg. household income", income_display)
        
        age_display = f"{avg_age:.1f} years" if pd.notna(avg_age) else "N/A"
        c3.metric("Avg. customer age", age_display)
        
        st.divider()
        st.subheader("Enriched data preview")
        
        # 9. Smart Column Reordering
        metric_cols = ['Estimated household income', 'Median age', 'Zip population']
        # Ensure Zip is first, then metrics, then rest
        cols = list(final_df.columns)
        for c in metric_cols + [zip_col]:
            if c in cols: cols.remove(c)
            
        display_order = [zip_col] + metric_cols + cols
        final_df = final_df[display_order]
        
        # Table Header Styling
        header_styles = [
            {'selector': 'th', 'props': [
                ('background-color', '#1A1A1A'), 
                ('color', '#F3F3F3'), 
                ('font-weight', 'bold')
            ]}
        ]
        
        st.dataframe(
            final_df.head(100).style.set_table_styles(header_styles).format({
                'Estimated household income': '${:,.0f}', 
                'Median age': '{:.1f}', 
                'Zip population': '{:,.0f}'
            }), 
            use_container_width=True, 
            hide_index=True
        )
        
        # 3. EXCEL GENERATION PHASE (New Spinner)
        # This tells the user: "We are done calculating, now we are just building the file."
        excel_data = None
        with st.spinner("Generating Excel file... (This may take a moment for large files)"):
            try:
                excel_data = convert_to_excel(final_df, "Customer demographics")
            except Exception as e:
                st.error(f"Error generating Excel file: {e}")
        
        if excel_data:
            st.download_button(
                "Download Enriched Excel", 
                excel_data, 
                "customer_demographics_enriched.xlsx", 
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            )
