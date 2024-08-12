# General Libraries #
import pandas as pd 
from datetime import datetime

# Streamlit Libraries #
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_extras.metric_cards import style_metric_cards

# Visualization Libraries #
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

#################### Session State ####################

if 'gsheets' not in st.session_state:
    st.session_state.gsheets = False
    
if 'generate_report' not in st.session_state:
    st.session_state.generate_report = False
    
if 'show_dataframe' not in st.session_state:
    st.session_state.show_dataframe = False
    
if 'existing_data' not in st.session_state:
    st.session_state.existing_data = None
    
if 'expense_log' not in st.session_state:
    st.session_state.df = None
    
if 'current_expense_log' not in st.session_state:
    st.session_state.current_expense_log = None
    
if 'previous_expense_log' not in st.session_state:
    st.session_state.previous_expense_log = None
    
if 'budget_frame' not in st.session_state:
    st.session_state.budget_frame = None
    
#################### Expense Log Class ####################

class Expense_Log:
    def __init__(self):
        try:
            # Establish connection to Google Sheets
            self.conn = st.connection('gsheets', type=GSheetsConnection)
            st.session_state.gsheets = True
            
            # Read data from Google Sheets
            self.existing_data = self.conn.read(spreadsheet= 'your google sheet share link')
            st.session_state.existing_data = self.existing_data
            
            #Convert Existing Data to DataFrame
            self.df = pd.DataFrame(self.existing_data)
            st.session_state.df = self.df
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df['month'] = self.df['date'].dt.month
            self.df['year'] = self.df['date'].dt.year
            self.df['year'] = self.df['year'].astype(str)
            self.df['year'] = self.df['year'].str.replace(',', '')
            self.df['date'] = self.df['date'].dt.strftime('%Y-%m-%d')
            
        except Exception as e:
            st.error(f"Error: {e}")
            
def main():
    st.title('Expense Log')
    st.divider()
    expense_log = Expense_Log()
    st.session_state.expense_log = expense_log
    
    budget_frame = pd.DataFrame({
        'type': ['transportation_budget', 'food_budget'],
        'amount': [2400, 2500]
    })
    
    st.session_state.budget_frame = budget_frame
    
    selector_month_year_col = st.columns(2)

    with selector_month_year_col[1]:
        st.warning("Please Select Month and Year")
        selected_year = st.selectbox("Year", expense_log.df['year'].unique())
        
        if selected_year: 
            selected_month = st.selectbox("Month", expense_log.df['month'].unique())

    if hasattr(expense_log, 'df'):
        st.divider()
        if selected_month and selected_year:
        
            filtered_expense_log_df = expense_log.df[expense_log.df['month'] == selected_month]
            filtered_expense_log_df = filtered_expense_log_df.reset_index(drop=True)
            
            #Save to session state
            st.session_state.current_expense_log = filtered_expense_log_df
                
            #Create Previous Month DataFrame for Comparison
            previous_month = selected_month - 1
            filtered_previous_expense_log_df = expense_log.df[expense_log.df['month'] == previous_month]
            
            #Save to session state
            st.session_state.previous_expense_log = filtered_previous_expense_log_df
        
            if st.session_state.current_expense_log is not None:
                st.dataframe(st.session_state.current_expense_log, width=1000)
                st.session_state.show_dataframe = True
            

            if not st.session_state.generate_report:
                #Generate Report Button
                generate_report = st.button("Generate Report")
                if generate_report:
                    st.session_state.generate_report = True
                    st.session_state.show_dataframe = False
                    
            #After Generate Report Button is clicked
            if st.session_state.generate_report:
                if filtered_previous_expense_log_df.empty:
                    st.warning("No data available for comparison.")

                else:
                    current_total = filtered_expense_log_df['cost'].sum()
                    previous_total = filtered_previous_expense_log_df['cost'].sum()
                    
                    #add, to the cost column and no decimal places
                    formatted_current_total = "{:,.0f}".format(current_total)
                    
                    # formatted_current_total = int(current_total)
                    formatted_previous_total = "{:,.0f}".format(previous_total)
                    
                    delta_cost = int(previous_total - current_total)
                    
                    #Transaction count
                    current_transaction_count = filtered_expense_log_df.shape[0]
                    previous_transaction_count = filtered_previous_expense_log_df.shape[0]
                    
                    delta_transaction_count = int(current_transaction_count - previous_transaction_count)

                #Visualization Column Header
                st.write("# Visualization")
                st.divider()
                #Metric value column
                
                metric_col = st.columns(3)
                
                with metric_col[0]:
                    st.metric(label="Total Expense", value=formatted_current_total, delta=delta_cost)
                    st.info(f"Total Expense: {int(filtered_expense_log_df['cost'].sum())} Bath")
                    
                    #Logic statement to compare the total cost between current and previous month
                    if previous_total > current_total:
                        st.success(f"Total Expense Decreased by {abs(int(previous_total - current_total))} Bath")
                    elif previous_total < current_total:
                        st.error(f"Total Expense Increased by {abs(int(previous_total - current_total))} Bath") 
                    else:
                        st.success("Total Expense Remained the Same")
                
                with metric_col[1]:
                    st.metric(label="Number of Transactions", value=current_transaction_count, delta=delta_transaction_count)
                    st.info(f"Number of Transactions: {filtered_expense_log_df.shape[0]}")
                    
                    if previous_transaction_count > current_transaction_count:
                        st.success(f"Number of Transactions Decreased by {abs(int(previous_transaction_count - current_transaction_count))}")
                        
                    elif previous_transaction_count < current_transaction_count:
                        st.error(f"Number of Transactions Increased by {abs(int(previous_transaction_count - current_transaction_count))}")
                        
                    else:
                        st.success("Number of Transactions Remained the Same")
                        
                with metric_col[2]:
                    st.metric(label="Budget", value=budget_frame['amount'].sum(), delta=-int(current_total - budget_frame['amount'].sum()))
                    st.info(f"Budget: {budget_frame['amount'].sum()} Bath")
                    
                    if current_total > budget_frame['amount'].sum():
                        st.error(f"Budget Exceeded by {abs(int(current_total - budget_frame['amount'].sum()))} Bath")
                        
                    elif current_total < budget_frame['amount'].sum():
                        st.success(f"You save money: {abs(int(current_total - budget_frame['amount'].sum()))} Bath")
                        
                    else:
                        st.success("Budget Spent as Planned")
                    
                style_metric_cards(border_left_color="#672E6D")
                
                st.divider()
                
                #Visualization column
                visualzation_col = st.columns([5, 0.5])
                
                with visualzation_col[0]:
                    pie_source = filtered_expense_log_df[filtered_expense_log_df['cost'].notnull()]
                    pie_source = pie_source.groupby(['type'])['cost'].sum().reset_index()
                    fig_pie = go.Figure(data=[go.Pie(labels=pie_source['type'], values=pie_source['cost'], hole=0.3)])
                    
                    # Update the layout to format numbers consistently
                    fig_pie.update_traces(
                        textinfo='label+percent+value', 
                        texttemplate='%{value:,.0f}',   
                    )
                    
                    fig_pie.update_layout(
                        title='Expense Distribution by Type',
                        
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True, theme='streamlit')
                    
                with visualzation_col[1]:
                    bar_source_current = filtered_expense_log_df[filtered_expense_log_df['cost'].notnull()].groupby(['month'])['cost'].sum().reset_index()
                    bar_source_current['cost'] = bar_source_current['cost'].apply(lambda x: int(x))
                    
                    bar_source_previous = filtered_previous_expense_log_df[filtered_previous_expense_log_df['cost'].notnull()].groupby(['month'])['cost'].sum().reset_index()
                    bar_source_previous['cost'] = bar_source_previous['cost'].apply(lambda x: int(x))
                    
                    delta_cost = abs(int(bar_source_current['cost'].iloc[-1] - bar_source_previous['cost'].iloc[-1]))
                    formatted_delta_cost = f'{int(abs(delta_cost)):,}'

                    # Coordinate of the line to connect the cost between current and previous month
                    x_coords = [bar_source_current['month'].iloc[-1], bar_source_previous['month'].iloc[-1]]
                    y_coords = [bar_source_current['cost'].iloc[-1], bar_source_previous['cost'].iloc[-1]]
                    mid_x = (x_coords[0] + x_coords[1]) / 2
                    mid_y = (y_coords[0] + y_coords[1]) / 2

                    
                    fig_bar = go.Figure()
                    # Add current costs bar trace
                    fig_bar.add_trace(go.Bar(
                        x=bar_source_current['month'],
                        y=bar_source_current['cost'],
                        text=bar_source_current['cost'].apply(lambda x: f'{x:,}'),
                        name='Current Cost',
                        marker_color='blue'
                    ))
                    # Add previous costs bar trace
                    fig_bar.add_trace(go.Bar(
                        x=bar_source_previous['month'],
                        y=bar_source_previous['cost'].apply(lambda x: round(x, 2)),
                        text=bar_source_previous['cost'].apply(lambda x: f'{x:,}'),
                        name='Previous Cost',
                        marker_color='red'
                    ))
                    
                    #Add line to connect the cost between current and previous month, and add the text to show the difference cost between the month
                    fig_bar.add_trace(go.Scatter(
                        x= [x_coords[0], mid_x, x_coords[1]],
                        y= [y_coords[0], mid_y, y_coords[1]],
                        mode='lines',
                        name='Difference',
                        textposition='top center',
                        line=dict(color='green', width=2, dash='dash')
                    ))
                    
                    # Add annotation for the delta cost at the midpoint of the line
                    fig_bar.add_annotation(
                        x=mid_x,
                        y=mid_y,
                        text=formatted_delta_cost,
                        showarrow=False,
                        arrowhead=4,
                        ax=20,
                        ay=-80,
                        font=dict(
                            size = 16,
                            color = 'red'
                        ))
                    
                    # Update the layout
                    fig_bar.update_layout(
                        title='Expense Distribution by Month',
                        xaxis_title='Month',
                        yaxis_title='Cost',
                        barmode='group',
                        showlegend=True,
                        legend=dict(
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        width=700,
                        height=500
                    )
                    
                    
                    st.plotly_chart(fig_bar)
                
                ### Histogram ###
                fig = px.histogram(
                    filtered_expense_log_df,
                    x='date',  
                    nbins=30,  
                    title='Expense Frequency by Date', 
                    color_discrete_sequence=['skyblue']
                )

                fig.update_layout(
                    title_text='Expense Frequency by Date', 
                    title_x=0.5,  
                    xaxis_title='Date',
                    yaxis_title='Frequency',
                    template='plotly_white',  
                    autosize=True,
                    width=1200,
                    height=500,
                    margin=dict(l=50, r=50, t=50, b=50) 
                )

                fig.update_traces(marker_color='#0077B6') 
                
                st.plotly_chart(fig)                

        else:
            st.error("Failed to load data.")

if __name__ == "__main__":
    main()
