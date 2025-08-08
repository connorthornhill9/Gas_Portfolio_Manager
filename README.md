Natural Gas Portfolio Manager
**Author:** Connor Thornhill  
**GitHub:** [connorthornhill9](https://github.com/connorthornhill9)  

An interactive Streamlit app designed to help Portfolio Managers track and visualize positions in their natural gas books.
This tool was built with procurement teams in mind — giving them a simple, intuitive interface to guide daily nomination decisions.

🚀 Features
Track Daily Forecasts — enter or upload forecasted natural gas consumption.

Manage Executed Deals — log fixed or index deals with supplier, price, and delivery point.

Visualize Coverage — interactive charts to compare forecast vs. executed positions.

Weekly Action Plan — automated buy/sell guidance for each day in a gas week.

Inline Help — built-in, collapsible guidance for every section.


📂 Project Structure
bash
Copy
Edit
Gas_Portfolio_Manager/
│
├── app/
│   ├── app.py                # Main Streamlit app
│   ├── helpers.py             # Helper functions (load/save data, styling, etc.)
│   ├── data/
│   │   ├── deals.csv          # Sample deals data
│   │   └── forecast.csv       # Sample forecast data
│
├── README.md                  # Project overview (this file)
├── requirements.txt           # Python dependencies
└── .gitignore
🧠 Quick Start
1️⃣ Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
2️⃣ Run the app
bash
Copy
Edit
streamlit run app/app.py
📖 How to Use
1. Enter or Upload Forecast
Manually input daily forecast consumption, or upload a CSV.

Re-uploading the same date overwrites existing values.

2. Enter Executed Deal
Log fixed or index volumes for a date range.

Warnings appear if total deals exceed the forecast.

3. Visualize & Plan
Interactive chart shows coverage vs. forecast.

Weekly Action Plan tab suggests Buy/Sell amounts.

📊 Sample Data
The /app/data/ folder contains:

forecast.csv — sample forecast data.

deals.csv — sample executed deal data.
You can modify or replace these with your own.

🌐 Deployment
This app is Streamlit Cloud-ready.
Make sure:

requirements.txt is in the root folder.

Any local file paths are wrapped in try/except if deploying without write permissions.

🛠 Tech Stack
Python (pandas, plotly, datetime)

Streamlit for UI and deployment

📄 License
This project is licensed under the MIT License — feel free to modify and share.