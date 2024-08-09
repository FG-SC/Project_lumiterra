import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


df = pd.read_csv('lumiterra_trades.csv', index_col=0)

df['count'] = df['quantity'].astype(int)
df['price']  = df['price'].astype(float)
#df['unitaryPrice'] = df['price (ZBIT)'] / df [ 'count']
df['time'] = pd.to_datetime(df.index)
df = df.sort_values(by='time').reset_index(drop=True)


st.set_page_config(
    page_title='Selection',
    page_icon="👀",
    layout='wide'
)

st.title("Lumiterra Project: Marketplace Analytics")


st.markdown("""

Intro: This is a Data Science project that consists of displaying data in a friendly manner from the [Lumiterra Marketplace](https://marketplace.skymavis.com/collections/lumiterra?tab=activities).
Data is collected at least weekly for the moment as I'm doing this in my freetime. More data will be added in the future, so stay tuned!

OBS: 
- There maybe some bugs in some plots as I'm still web scrapping data.
- Just in case, this app was done using streamlit, a python framework for dashboards. I've used selenium to scrape the data online,
pandas to manipulate it and plotly.express to plot. :D             
            
If you find this __useful__ and want to support me, please, consider __donating__:
            
    BTC Wallet: bc1qk6glseyj4wyqrr05jemqhdz0l24he5u6555ll6 
    Metamask: 0x1382A41F37689858eD16771487e76Afa969eE148""")



with st.form(key='my_form'):
    # First question: type of property
    #types = list(sorted(df['category'].value_counts().index))
    #selected_types = st.selectbox('Select item category', options=types)

    # Filter DataFrame based on selected types
    df_type = df.copy()#[df['category'] == selected_types]
    # Second question: neighborhood (item)
    neighborhoods = list(sorted(df['item'].value_counts().index))
    selected_neighborhoods = st.multiselect('Select item', options=neighborhoods)

    # Filter DataFrame based on selected neighborhoods
    df_neighborhood = df_type[df_type['item'].isin(selected_neighborhoods)]
    submit_button = st.form_submit_button(label='Submit')

if submit_button:

    df = df_neighborhood.copy()
    # Assuming you have the dataframe 'df' with the relevant data
    price_rolling_window = 1
    items = df['item'].value_counts().index
        
    for item in items:
        # Filter data for the specific item
        df[(df['item'] == item) & (df['activityType'] == 'Sale')][::-1].reset_index().reset_index()
        data = df[(df['item'] == item) & (df['activityType'] == 'Sale')][::-1].reset_index().reset_index()
        #data = data.reset_index()
        data.rename(columns={'index': 'total_trades', 'timestamp':'time'},inplace=True)
        data['cumulative_count'] = data['quantity'].cumsum()

        # Custom aggregation function
        def weighted_avg(df, value, weight):
            return np.sum(df[value] * df[weight]) / np.sum(df[weight])

        # Group by 'time' and aggregate
        aggregated_df = data.groupby('time').agg({
            #'category': 'first',
            'item': 'first',
            'seller': lambda x: ', '.join(x),
            'buyer': lambda x: ', '.join(x),
            'price': 'sum',
            'quantity': 'sum',
            'unitary_price': lambda x: weighted_avg(data.loc[x.index], 'unitary_price', 'quantity'),
            'total_trades': 'size'
        }).reset_index()

        # Sort by 'time' if needed
        aggregated_df = aggregated_df.sort_values(by='time').reset_index(drop=True)
        # Create cumulative count column
        aggregated_df['cumulative_count'] = aggregated_df['quantity'].cumsum()
        # Create cumulative trades column
        aggregated_df['cumulative_trades'] = aggregated_df['total_trades'].cumsum()
        
        aggregated_df['Amount/Trade'] = aggregated_df['cumulative_count']/aggregated_df['cumulative_trades']

        # Create the plot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add the cumulative count line plot
        fig.add_trace(go.Scatter(
            x=aggregated_df['time'],
            y=aggregated_df['cumulative_count'],
            mode='lines',
            name='Cumulative Count (CC)',
            line=dict(color='blue', dash='dash')
        ), secondary_y=False)

        # Add the total number of trades line plot
        fig.add_trace(go.Scatter(
            x=aggregated_df['time'],
            y=aggregated_df['cumulative_trades'],
            mode='lines',
            name='Total Trades (TT)',
            line=dict(color='green')
        ), secondary_y=False)

        # Add the total number of trades line plot
        fig.add_trace(go.Scatter(
            x=aggregated_df['time'],
            y=aggregated_df['Amount/Trade'],
            mode='lines',
            name='Amounts per Trade (AT)',
            line=dict(color='purple')
        ), secondary_y=False)
        
        # Add the unitary price line plot
        fig.add_trace(go.Scatter(
            x=aggregated_df['time'],
            y=aggregated_df['unitary_price'].rolling(price_rolling_window).mean(),
            mode='lines+markers',
            name='Unitary Price',
            line=dict(color='red')
        ), secondary_y=True)

        # Update layout
        fig.update_layout(
            title=f'{item}\'s Data Over Time',
            xaxis_title='Time',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(255,255,255,1)',
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="RebeccaPurple"
            )
        )

        # Set y-axes titles
        fig.update_yaxes(title_text="CC/TT/AT", secondary_y=False, type="log")
        fig.update_yaxes(title_text="Unitary Price", secondary_y=True)

        # Show the plot
        #fig.show()

        # Show the plot
        st.write(fig)
