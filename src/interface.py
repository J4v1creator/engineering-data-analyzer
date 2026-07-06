import pandas as pd

def get_user_demand_selection(df) -> list:
    """
    Displays the available electricity demand types found in the dataset
    and prompts the user to select which ones to analyze using numbers.

    Args:
        df (pd.DataFrame): The validated dataset.

    Returns:
        list: A list of strings containing the selected demand types.
    """

    # 1. Extract unique demand categories dynamically from the 'name' column
    available_demands = list(pd.unique(df["name"]))

    print("\n📊 --- DEMAND SELECTION MENU ---")
    print("Select which demand types you want to include in the report and chart:")

    # 2. Print options dynamically with an associated index number
    for i, demand in enumerate(available_demands, start=1):
        print(f"  [{i}] {demand}")

    # The last option is always dynamically mapped to "Analyze All"
    all_options_idx = len(available_demands) + 1
    print(f"  [{all_options_idx}] ANALYZE ALL DEMANDS")

    while True:
        try:
            # 3. Capture user input and clean trailing whitespaces
            user_input = input(f"\nEnter numbers separated by commas (e.g., 1,3) or press Enter for ALL: ").strip()

            # If the user presses Enter or selects the "All" option, return the full list
            if user_input == "" or user_input == str(all_options_idx):
                print("🔄 Analyzing all available demand types...")
                return available_demands
            
            # 4. Parse input string into a list of integers (e.g., "1, 3" -> [1, 3])
            selected_indices = [int(x.strip()) for x in user_input.split(",")]

            # 5. Validate that all selected numbers fall within the valid menu range
            if all(1 <= idx <= len(available_demands) for idx in selected_indices):
                # Map integers back to the actual string names from the dataset
                selected_demands = [available_demands[idx - 1] for idx in selected_indices]
                print(f"✅ Selected categories: {', '.join(selected_demands)}")
                return selected_demands
            else:
                print(f"❌ Invalid selection. Please enter numbers between 1 and {all_options_idx}.")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2).")