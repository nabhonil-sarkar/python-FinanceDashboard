import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

def analyze_portfolio():
    # 1. Create a hidden main window
    root = tk.Tk()
    root.withdraw() # Hide the main empty box

    # 2. Pop up a file selector
    messagebox.showinfo("Step 1", "Please select your CSV or Excel file.")
    file_path = filedialog.askopenfilename(title="Select Portfolio File", 
                                           filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")])

    if not file_path:
        messagebox.showwarning("Cancelled", "No file selected. Exiting.")
        return

    try:
        # 3. Read the file (Handle both CSV and Excel)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # 4. Run the Analysis
        # Clean data
        df['Last_Clean'] = df['Last'].astype(str).str.extract(r'(\d+\.\d+)').astype(float)
        df['Spread'] = df['Ask'] - df['Bid']
        df['Spread_Pct'] = (df['Spread'] / df['Ask']) * 100

        # Gather Insights
        total_positions = len(df)
        call_count = len(df[(df['Type'] == 'OPT') & (df['P/C'] == 'C')])
        put_count = len(df[(df['Type'] == 'OPT') & (df['P/C'] == 'P')])
        
        # Identify expensive trades
        expensive_trades = df.sort_values('Spread_Pct', ascending=False).head(3)
        expensive_text = ""
        for index, row in expensive_trades.iterrows():
            expensive_text += f"{row['Symbol']} ({row['Spread_Pct']:.1f}% Spread)\n"

        # 5. Format the Output Message
        result_msg = (
            f"--- PORTFOLIO REPORT ---\n\n"
            f"Total Positions: {total_positions}\n"
            f"Puts: {put_count} | Calls: {call_count}\n\n"
            f"⚠️ HIGH COST TRADES (Wide Spreads):\n"
            f"{expensive_text}\n"
            f"--- END OF REPORT ---"
        )

        # 6. Show the result in a popup window
        messagebox.showinfo("Analysis Results", result_msg)

    except Exception as e:
        # If anything breaks, show the error in a window
        messagebox.showerror("Error", f"Something went wrong:\n{str(e)}")

if __name__ == "__main__":
    analyze_portfolio()