import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Pro Financial Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM DARK THEME ---
st.markdown("""
<style>
    /* Dark Background */
    [data-testid="stAppViewContainer"] { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #262730; }
    
    /* Metrics Styling */
    div[data-testid="metric-container"] {
        background-color: #1E2127;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #FF4B4B;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Headers */
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 300; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
@st.cache_data
def load_and_process_data(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
            
        # 1. Clean Prices (Remove 'C' and convert)
        cols_to_clean = ['Last', 'Bid', 'Ask']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('C', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 2. Expiry & DTE
        df['Expiry_Str'] = df['Expiry'].fillna(0).astype(int).astype(str)
        df['Expiry_Date'] = pd.to_datetime(df['Expiry_Str'], format='%Y%m', errors='coerce')
        df['Days_To_Expiry'] = (df['Expiry_Date'] - datetime.now()).dt.days
        
        # 3. Filter Options
        df_opt = df[df['Type'] == 'OPT'].copy()
        
        # 4. Financial Calculations
        df_opt['Position_Value'] = df_opt['Last'] * 100 # Assuming 100 multiplier
        df_opt['Spread'] = df_opt['Ask'] - df_opt['Bid']
        
        # Logic: Puts -> Assignment Price | Calls -> Break Even
        df_opt['Key_Level'] = df_opt.apply(
            lambda x: x['Strike'] if x['P/C'] == 'P' else (x['Strike'] + x['Last']), axis=1
        )
        df_opt['Level_Type'] = df_opt['P/C'].map({'P': 'Assignment Price', 'C': 'Break-Even Price'})
        
        # Labels
        df_opt['Label'] = df_opt['Symbol'] + " " + df_opt['Strike'].astype(str) + df_opt['P/C']
        
        return df_opt
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame()

# --- MAIN APP ---
def main():
    st.title("🚀 Professional Options Dashboard")
    st.markdown("### Advanced Portfolio Analytics")
    
    # Sidebar
    st.sidebar.header("📂 Data & Filters")
    # FIX: Added unique key to prevent DuplicateElementId error
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv", "xlsx"], key="portfolio_uploader_v2")
    
    if uploaded_file:
        df = load_and_process_data(uploaded_file)
        
        if not df.empty:
            # Filters
            symbols = st.sidebar.multiselect("Filter by Symbol", options=df['Symbol'].unique(), default=df['Symbol'].unique())
            types = st.sidebar.multiselect("Filter by Type", options=['P', 'C'], default=['P', 'C'])
            
            # Apply Filter
            dff = df[(df['Symbol'].isin(symbols)) & (df['P/C'].isin(types))]
            
            # --- TOP ROW METRICS ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Exposure", f"${dff['Position_Value'].sum():,.0f}")
            col2.metric("Positions Count", len(dff))
            col3.metric("Avg Days to Expiry", f"{dff['Days_To_Expiry'].mean():.0f} Days")
            col4.metric("Avg Bid/Ask Spread", f"${dff['Spread'].mean():.2f}")
            
            st.divider()

            # --- TABS FOR DIFFERENT VIEWS ---
            tab1, tab2, tab3 = st.tabs(["📊 Portfolio Overview", "⏳ Time & Risk", "🧮 Payoff Simulator"])
            
            with tab1:
                # Row 1: Charts
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Allocation by Symbol")
                    fig_pie = px.pie(dff, values='Position_Value', names='Symbol', hole=0.4, template='plotly_dark')
                    fig_pie.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with c2:
                    st.subheader("Strategy Breakdown")
                    fig_bar = px.bar(
                        dff.groupby(['Symbol', 'P/C'])['Position_Value'].sum().reset_index(),
                        x='Symbol', y='Position_Value', color='P/C',
                        title="Value Distribution",
                        template='plotly_dark', barmode='group',
                        color_discrete_map={'C': '#00CC96', 'P': '#EF553B'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                # Row 2: Table
                st.subheader("Position Details")
                st.dataframe(
                    dff[['Label', 'Expiry_Date', 'Last', 'Position_Value', 'Level_Type', 'Key_Level']]
                    .sort_values('Position_Value', ascending=False)
                    .style.format({'Last': '${:.2f}', 'Position_Value': '${:,.0f}', 'Key_Level': '${:.2f}', 'Expiry_Date': '{:%Y-%m-%d}'}),
                    use_container_width=True
                )

            with tab2:
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.subheader("📅 Expiry Timeline")
                    fig_timeline = px.scatter(
                        dff, x='Expiry_Date', y='Symbol', size='Position_Value', color='P/C',
                        title="Positions by Expiry Date (Bubble Size = Value)",
                        template='plotly_dark',
                        hover_data=['Strike', 'Key_Level']
                    )
                    fig_timeline.update_layout(xaxis_title="Expiry Date", yaxis_title="Symbol")
                    st.plotly_chart(fig_timeline, use_container_width=True)
                
                with col_b:
                    st.subheader("⚠️ Liquidity Risk")
                    st.markdown("Positions with wide Bid-Ask spreads.")
                    # FIX: Removed background_gradient to avoid Matplotlib dependency
                    st.dataframe(
                        dff[['Symbol', 'Strike', 'Spread']].sort_values('Spread', ascending=False)
                        .style.format({'Spread': '${:.2f}'}),
                        use_container_width=True, height=400
                    )

            with tab3:
                st.subheader("Interactive Payoff Simulator")
                st.info("Select a position to see its intrinsic value at different stock prices on expiry day.")
                
                # Selector
                selected_label = st.selectbox("Select Position", dff['Label'].unique())
                if selected_label:
                    pos = dff[dff['Label'] == selected_label].iloc[0]
                    strike = pos['Strike']
                    pc = pos['P/C']
                    
                    # Slider for Price Scenario
                    min_price = float(strike * 0.5)
                    max_price = float(strike * 1.5)
                    spot_price = st.slider("Hypothetical Stock Price at Expiry", min_price, max_price, float(strike))
                    
                    # Calculate Intrinsic Value
                    if pc == 'C':
                        intrinsic_val = max(0, spot_price - strike)
                    else:
                        intrinsic_val = max(0, strike - spot_price)
                    
                    contract_val = intrinsic_val * 100
                    
                    # Display Result
                    c_sim1, c_sim2 = st.columns(2)
                    c_sim1.metric(f"Projected Option Value (Per Share)", f"${intrinsic_val:.2f}")
                    c_sim2.metric(f"Total Contract Value", f"${contract_val:,.2f}")
                    
                    # Graph Payoff
                    prices = list(range(int(min_price), int(max_price)))
                    values = [max(0, p - strike) if pc == 'C' else max(0, strike - p) for p in prices]
                    
                    fig_payoff = px.line(x=prices, y=values, title=f"Payoff Diagram at Expiry ({pos['Label']})", template='plotly_dark')
                    fig_payoff.add_vline(x=spot_price, line_dash="dash", line_color="yellow", annotation_text="Selected Price")
                    fig_payoff.update_layout(xaxis_title="Stock Price", yaxis_title="Option Intrinsic Value")
                    st.plotly_chart(fig_payoff, use_container_width=True)

    else:
        st.info("👋 Upload your CSV to unlock the dashboard.")

if __name__ == "__main__":
    import sys
    from streamlit.web import cli as stcli
    from streamlit import runtime
    
    # Check if we are running inside Streamlit already
    if runtime.exists():
        main()
    else:
        # If not, relaunch the script via Streamlit CLI
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())

    except Exception as e:
        # If anything breaks, show the error in a window
        messagebox.showerror("Error", f"Something went wrong:\n{str(e)}")

if __name__ == "__main__":

    analyze_portfolio()
