import pandas as pd
from datetime import datetime, timedelta
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash import dash_table
from dash.dash_table.Format import Group

# Define the file paths and their corresponding locations
files_with_locations = {
	'./../data/paypa_plane/ZeroW_Sunshine_Coast_Agreements_2024-07-21.csv': 'Sunshine Coast',
	'./../data/paypa_plane/Cairns_Agreements-2024-06-21.csv': 'Cairns',
	'./../data/paypa_plane/ZeroW_Arundel members 2024-07-01.csv': 'Gold Coast',
	'./../data/paypa_plane/ZeroW_Brisbane-Agreements-2024-06-21.csv': 'Brisbane',
	'./../data/paypa_plane/ZeroW_Gold_Coast_Agreements-2024-07-01.csv': 'Gold Coast',
	'./../data/paypa_plane/ZeroW_SouthSide_Agreements-2024-06-21.csv': 'South Side'
}

# Load and combine the CSV files, adding the location column
combined_dfs = []
for file, location in files_with_locations.items():
	df = pd.read_csv(file)
	df['Location'] = location
	combined_dfs.append(df)

combined_df = pd.concat(combined_dfs)

# Filter out the records where STATUS is 'Cancelled'
combined_df = combined_df[combined_df['STATUS'] != 'Cancelled']

# Convert date columns to datetime
combined_df['AGREED_DATE'] = pd.to_datetime(combined_df['AGREED_DATE'],
											errors='coerce')
combined_df['CANCEL_DATE'] = pd.to_datetime(combined_df['CANCEL_DATE'],
											errors='coerce')

# Calculate net movement in the last week
one_week_ago = datetime.now() - timedelta(weeks=1)


def filter_data(location):
	if location == 'All':
		filtered_df = combined_df
	else:
		filtered_df = combined_df[combined_df['Location'] == location]
	new_members = \
	filtered_df[(filtered_df['AGREED_DATE'] >= one_week_ago)].shape[0]
	cancelled_members = \
	filtered_df[(filtered_df['CANCEL_DATE'] >= one_week_ago)].shape[0]
	net_movement = new_members - cancelled_members
	return filtered_df, new_members, cancelled_members, net_movement


app = dash.Dash(__name__)

app.layout = html.Div([
	html.H1("ZeroW Members Dashboard"),
	dcc.Dropdown(
		id='location-dropdown',
		options=[{'label': loc, 'value': loc} for loc in
				 ['All'] + list(combined_df['Location'].unique())],
		value='All'
	),
	html.Div([
		html.H2("Number of Members"),
		dcc.Graph(id='number-of-members')
	]),
	html.Div([
		html.H2("Net Movement in the Last Week"),
		html.P(id='new-members'),
		html.P(id='cancelled-members'),
		html.P(id='net-movement')
	]),
	html.Div([
		html.H2("Member Details"),
		dash_table.DataTable(
			id='member-details',
			columns=[{"name": i, "id": i} for i in combined_df.columns],
			page_size=10
		)
	])
])


@app.callback(
	[Output('number-of-members', 'figure'),
	 Output('new-members', 'children'),
	 Output('cancelled-members', 'children'),
	 Output('net-movement', 'children'),
	 Output('member-details', 'data')],
	[Input('location-dropdown', 'value'),
	 Input('number-of-members', 'clickData')]
)
def update_dashboard(selected_location, clickData):
	filtered_df, new_members, cancelled_members, net_movement = filter_data(
		selected_location)

	figure = {
		'data': [{'x': filtered_df['STATUS'].value_counts().index,
				  'y': filtered_df['STATUS'].value_counts().values,
				  'type': 'bar'}],
		'layout': {'title': 'Current Status of Members'}
	}

	new_members_text = f"New members: {new_members}"
	cancelled_members_text = f"Cancelled members: {cancelled_members}"
	net_movement_text = f"Net movement: {net_movement}"

	if clickData:
		selected_status = clickData['points'][0]['x']
		detailed_records = filtered_df[
			filtered_df['STATUS'] == selected_status].to_dict('records')
	else:
		detailed_records = []

	return figure, new_members_text, cancelled_members_text, net_movement_text, detailed_records


if __name__ == '__main__':
	app.run_server(debug=True)
