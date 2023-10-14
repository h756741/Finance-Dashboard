import streamlit as st
import pandas as pd
import yfinance as yf
import cufflinks as cf
import datetime
import pandas_datareader as pdr
import wikipedia as wp
import finnhub
import plotly.graph_objects as go
import os

api_key = os.getenv('FINNHUB_API_KEY')
finnhub_client = finnhub.Client(api_key=api_key)

@st.cache_data
def fetch_company_profile(ticker):
    return finnhub_client.company_profile2(symbol=ticker)

@st.cache_data
def fetch_earnings(ticker):
    return finnhub_client.company_earnings(ticker)

@st.cache_data
def fetch_news(ticker, start_date, end_date):
    return finnhub_client.company_news(ticker, _from=start_date, to=end_date)

st.title("Finance Dashboard")

st.subheader("Stocks 📈")

st.write('---')

# Sidebar
st.sidebar.subheader('Query parameters')
start_date = st.sidebar.date_input("Start date", datetime.date(2009,1 ,1))
end_date = st.sidebar.date_input("End date", datetime.date(2023, 10, 1))

# Company list from Wikipedia
html = wp.page("List of S&P 500 companies").html().encode("UTF-8")
df = pd.read_html(html)[0]  # This line may vary - inspect your data to locate the table
ticker_list = df['Symbol'].tolist()  # Extract the 'Symbol' column

tickerSymbol = st.sidebar.selectbox('Stock ticker', ticker_list)

# Ticker Information
tickerData = yf.Ticker(tickerSymbol)
tickerDf = tickerData.history(period='1d', start=start_date, end=end_date)

string_name = tickerData.info['longName']
st.header('**%s**' % string_name)

# Plotting the query parameters
st.subheader('Historical Stock Prices')
fig = go.Figure(data=[go.Candlestick(x=tickerDf.index,
                open = tickerDf['Open'],
                high = tickerDf['High'],
                low=tickerDf['Low'],
                close=tickerDf['Close'])])

fig.update_layout(xaxis_rangeslider_visible=False, xaxis_title='Date',
                yaxis_title='Price (in USD)', title=f'{string_name} Stock Price Data')
st.plotly_chart(fig)

# Company Data
st.subheader('Company Profile')

try:
    company_profile = fetch_company_profile(tickerSymbol)
except finnhub.FinnhubAPIException as e:
    st.error("Error fetching company profile: " + str(e))
    company_profile = None

if company_profile:
    profile_md= f"""
    - **Country**: {company_profile['country']}
    - **Currency**: {company_profile['currency']}
    - **Exchange**: {company_profile['exchange']}
    - **Industry**: {company_profile['finnhubIndustry']}
    - **IPO Date**: {company_profile['ipo']}
    - **Market Capitalization (millions)**: {company_profile['marketCapitalization']}
    - **Name**: {company_profile['name']}
    - **Phone**: {company_profile['phone']}
    - **Shares Outstanding**: {company_profile['shareOutstanding']}
    - **Ticker**: {company_profile['ticker']}
    - **Website**: [Link]({company_profile['weburl']})
    """
    st.markdown(profile_md)
    st.image(company_profile['logo'], use_column_width=False)
else:
    st.warning("No company profile information available.")

st.subheader('Earnings')
earnings_data = fetch_earnings(tickerSymbol)
earnings_df = pd.DataFrame(earnings_data)
earnings_df = earnings_df[['period', 'quarter', 'actual', 'estimate', 'surprise', 'surprisePercent', 'year']]
st.table(earnings_df)

today = datetime.datetime.now()
month_ago = today - datetime.timedelta(days=30)

news = fetch_news(tickerSymbol, month_ago.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

st.subheader('News')
if news: 
    for article in news:
        st.subheader(article['headline'])
        st.write(article['summary'])
        st.write(article['url'])
        if article['image']:
            st.image(article['image'])
        st.write("---")
else:
    st.write("no company-specific news available during the specified date range")

