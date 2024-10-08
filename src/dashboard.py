import pandas as pd
from datetime import datetime, timedelta
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dash import dash_table
import plotly.express as px

# Load the pre-processed merged DataFrame
merged_df = pd.read_excel("merged_data.xlsx", sheet_name="merged_data")

# Normalize STATUS values
merged_df['STATUS'] = merged_df['STATUS'].str.strip().str.capitalize()

# Filter out the records where STATUS is 'Cancelled' or 'Canceled'
merged_df = merged_df[~merged_df['STATUS'].isin(['Cancelled', 'Canceled'])]

# Convert date columns to datetime
merged_df['AGREED_DATE'] = pd.to_datetime(merged_df['AGREED_DATE'], errors='coerce')
merged_df['CANCEL_DATE'] = pd.to_datetime(merged_df['CANCEL_DATE'], errors='coerce')


def filter_data(location, days):
    """
    Filter the DataFrame based on the selected location and date range.
    Exclude paused memberships from the total members count.
    :param location: Selected location
    :param days: Number of days for the date range filter
    :return: filtered_df, new_members, cancelled_members, net_movement, total_members
    """
    one_week_ago = datetime.now() - timedelta(days=days)
    if location == 'All':
        filtered_df = merged_df
    else:
        filtered_df = merged_df[merged_df['Location'] == location]
    old_members_df = filtered_df[filtered_df['AGREED_DATE'] < one_week_ago]  # Transactions from more than one week ago
    active_members_df = filtered_df[filtered_df['STATUS'] != 'Paused']  # Exclude paused memberships from the total members count
    total_members = active_members_df['CUSTOMER_NAME'].nunique()
    new_members = filtered_df[filtered_df['AGREED_DATE'] >= one_week_ago]['CUSTOMER_NAME'].nunique()  # Calculate unique new members
    cancelled_members = filtered_df[filtered_df['CANCEL_DATE'] >= one_week_ago]['CUSTOMER_NAME'].nunique()  # Calculate cancelled unique members
    net_movement = new_members - cancelled_members  # Calculate net movement
    return filtered_df, new_members, cancelled_members, net_movement, total_members


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("ZeroW Members Dashboard"),
    dcc.Dropdown(
        id='location-dropdown',
        options=[{'label': loc, 'value': loc} for loc in ['All'] + list(merged_df['Location'].unique())],
        value='All'
    ),
    dcc.Dropdown(
        id='date-range-dropdown',
        options=[
            {'label': '7 Days', 'value': 7},
            {'label': '14 Days', 'value': 14},
            {'label': '21 Days', 'value': 21},
            {'label': '28 Days', 'value': 28}
        ],
        value=7  # Default value
    ),
    html.Div([
        html.Div([
            html.H2("Number of Members"),
            dcc.Graph(id='number-of-members')
        ], style={'grid-area': 'top-left'}),

        html.Div([
            html.H2("Net Movement in the Last Week"),
            html.P(id='new-members', style={'cursor': 'pointer'}),
            html.P(id='cancelled-members', style={'cursor': 'pointer'}),
            html.P(id='net-movement', style={'cursor': 'pointer'}),
            html.P(id='total-members', style={'cursor': 'pointer'})
        ], style={'grid-area': 'top-right'}),

        html.Div([
            html.H2("Mix of Membership Types by Location"),
            dcc.Graph(id='membership-type-mix')
        ], style={'grid-area': 'bottom-left'}),

        html.Div([
            html.H2("Distribution of Membership Types by Location"),
            dcc.Graph(id='membership-type-distribution')
        ], style={'grid-area': 'bottom-right'})
    ], style={
        'display': 'grid',
        'grid-template-areas': '''
            'top-left top-right'
            'bottom-left bottom-right'
        ''',
        'grid-gap': '20px',
        'padding': '20px'
    }),
    html.Div([
        html.H2("Detailed Information"),
        dash_table.DataTable(id='details-table', columns=[])
    ], style={'marginTop': 50})
])


@app.callback(
    [Output('number-of-members', 'figure'),
     Output('new-members', 'children'),
     Output('cancelled-members', 'children'),
     Output('net-movement', 'children'),
     Output('total-members', 'children'),
     Output('membership-type-mix', 'figure'),
     Output('membership-type-distribution', 'figure')],
    [Input('location-dropdown', 'value'),
     Input('date-range-dropdown', 'value')]
)
def update_dashboard(selected_location, selected_days):
    """
    Update the dashboard based on the selected location and date range.
    :param selected_location: Selected location
    :param selected_days: Number of days for the date range filter
    :return: number_of_members_figure, new_members_text, cancelled_members_text,
    net_movement_text, total_members_text, membership_type_mix_figure, membership_type_distribution_figure
    """
    filtered_df, new_unique_members, cancelled_unique_members, net_movement, total_members = filter_data(selected_location, selected_days)

    # Number of members figure
    status_count = filtered_df['STATUS'].value_counts()
    number_of_members_figure = {
        'data': [{'x': status_count.index,
                  'y': status_count.values,
                  'type': 'bar'}],
        'layout': {'title': 'Current Status of Members'}
    }
    new_members_text = f"New members: {new_unique_members}"
    cancelled_members_text = f"Cancelled members: {cancelled_unique_members}"
    net_movement_text = f"Net members movement: {net_movement}"
    total_members_text = f"Total members: {total_members}"

    # Mix of membership types by location
    membership_type_mix = filtered_df.groupby('Location')['MEMBERSHIP_TYPE'].value_counts().unstack().fillna(0)
    membership_type_mix_figure = px.bar(
        membership_type_mix,
        title='Mix of Membership Types by Location',
        labels={'value': 'Count', 'MEMBERSHIP_TYPE': 'Membership Type'},
        barmode='stack'
    )

    # Distribution of membership types by location
    membership_type_distribution = filtered_df['MEMBERSHIP_TYPE'].value_counts(normalize=True).reset_index()
    membership_type_distribution.columns = ['MEMBERSHIP_TYPE', 'Percentage']
    membership_type_distribution['Count'] = filtered_df['MEMBERSHIP_TYPE'].value_counts().values
    membership_type_distribution_figure = px.pie(
        membership_type_distribution,
        values='Percentage',
        names='MEMBERSHIP_TYPE',
        title='Distribution of Membership Types by Location',
        hover_data=['Count'],
        labels={'Percentage': 'Percentage', 'Count': 'Count'}
    )
    membership_type_distribution_figure.update_traces(
        textinfo='none', hoverinfo='label+percent+value'
    )
    membership_type_distribution_figure.update_layout(
        margin=dict(t=50, b=50, l=50, r=50)
    )
    return (number_of_members_figure,
            new_members_text,
            cancelled_members_text,
            net_movement_text,
            total_members_text,
            membership_type_mix_figure,
            membership_type_distribution_figure)


@app.callback(
    Output('details-table', 'columns'),
    Output('details-table', 'data'),
    [Input('new-members', 'n_clicks'),
     Input('cancelled-members', 'n_clicks'),
     Input('net-movement', 'n_clicks'),
     Input('total-members', 'n_clicks')],
    [Input('location-dropdown', 'value'),
     Input('date-range-dropdown', 'value')]
)
def display_detailed_info(new_clicks, cancelled_clicks, net_movement_clicks, total_clicks, selected_location, selected_days):
    """
    Display detailed information based on clicks on the summary statistics.
    :param new_clicks: Clicks on new members count
    :param cancelled_clicks: Clicks on cancelled members count
    :param net_movement_clicks: Clicks on net movement count
    :param total_clicks: Clicks on total members count
    :param selected_location: Selected location
    :param selected_days: Selected date range
    :return: columns, data for the DataTable
    """
    filtered_df, new_unique_members, cancelled_unique_members, net_movement, total_members = filter_data(selected_location, selected_days)

    ctx = dash.callback_context
    columns = [{"name": i, "id": i} for i in filtered_df.columns]
    data = []

    if not ctx.triggered:
        return columns, data

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'new-members':
        data = filtered_df[filtered_df['AGREED_DATE'] >= datetime.now() - timedelta(days=selected_days)].to_dict('records')

    elif triggered_id == 'cancelled-members':
        data = filtered_df[filtered_df['CANCEL_DATE'] >= datetime.now() - timedelta(days=selected_days)].to_dict('records')

    elif triggered_id == 'net-movement':
        # Optionally, you could add logic here to show net movement data
        pass

    elif triggered_id == 'total-members':
        data = filtered_df[filtered_df['STATUS'] != 'Paused'].to_dict('records')

    return columns, data


if __name__ == '__main__':
    app.run_server(debug=True)



# todo: dict of locations and colours, dict of contractors
