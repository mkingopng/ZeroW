import pandas as pd
import math


def read_merged_data(file_path):
	"""
	Read the merged data from the CSV file.
	:param file_path: Path to the merged CSV file.
	:return: DataFrame containing the merged data.
	"""
	return pd.read_csv(file_path)


def get_current_members(data, location, membership_type="Standard"):
	"""
	Get the current number of active members for a specific location and
	membership type.
	:param data: DataFrame containing the merged data.
	:param location: Location to filter the data by.
	:param membership_type: Membership type to filter the data by.
	:return: Number of active members for the location and membership type.
	"""
	filtered_data = data[
		(data['Location'] == location) &
		(data['MEMBERSHIP_TYPE'].str.lower() == membership_type.lower())
		]
	active_members = filtered_data[
		filtered_data['STATUS'].str.lower() == 'active']
	return len(active_members)


def calculate_current_revenue_base(data, location):
	"""
	Calculate the current revenue base for a specific location.
	:param data: DataFrame containing the merged data.
	:param location: Location to filter the data by.
	:return: Current revenue base.
	"""
	filtered_data = data[
		(data['Location'] == location) &
		(data['STATUS'].str.lower() == 'active')
		]
	revenue_base = filtered_data['PRICE'].sum() * 4
	return revenue_base


def calculate_new_members_needed(current_rev, bep, membership_fee):
	"""
	Calculate the number of new members needed to reach the break-even point.
	:param current_rev: Current monthly revenue.
	:param bep: Monthly break-even point.
	:param membership_fee: Membership fee per member.
	:return: Number of new members needed to reach the break-even point.
	"""
	return math.ceil((bep - current_rev) / membership_fee)


def main():
	file_path = "merged_data.csv"
	data = read_merged_data(file_path)
	location = "Sunshine Coast"  # Hardcoded values for testing
	membership_fee = 35 * 4  # Standard membership fee per month
	monthly_costs = float(input("Enter the monthly costs: "))
	current_revenue_base = calculate_current_revenue_base(data, location)
	if current_revenue_base >= monthly_costs:
		print("You have already achieved the break-even point.")
	else:
		new_members_needed = calculate_new_members_needed(
			current_revenue_base,
			monthly_costs,
			membership_fee
		)
		print(
			f"Number of new standard members needed to reach the break-even point: {new_members_needed}")
	print(f"Current revenue base in {location}: ${current_revenue_base:.2f}")


if __name__ == "__main__":
	main()
