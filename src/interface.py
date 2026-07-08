import pandas as pd

def get_user_demand_selection(df) -> tuple:
    """Displays the available electricity demand types found in the dataset
    and prompts the user to select which ones to analyze using numbers.

    Args:
        df (pd.DataFrame): The validated dataset.

    Returns:
        tuple: A tuple containing (selected_demands, all_available_demands).
    """
    # Extract unique demand categories dynamically from the 'name' column
    available_demands = list(pd.unique(df["name"]))

    print("\n📊 --- DEMAND SELECTION MENU ---")
    print("Select which demand types you want to include in the report and chart:")

    # Print options dynamically with an associated index number
    for i, demand in enumerate(available_demands, start=1):
        print(f"  [{i}] {demand}")

    # The last option is always dynamically mapped to "Analyze All"
    all_options_idx = len(available_demands) + 1
    print(f"  [{all_options_idx}] ANALYZE ALL DEMANDS")

    while True:
        try:
            # Capture user input and clean trailing whitespaces
            user_input = input(f"\nEnter numbers separated by commas (e.g., 1,3) or press Enter for ALL: ").strip()

            # If the user presses Enter or selects the "All" option, return the full list
            if user_input == "" or user_input == str(all_options_idx):
                print("🔄 Analyzing all available demand types...")
                return available_demands, available_demands
            
            # Parse input string into a list of integers (e.g., "1, 3" -> [1, 3])
            selected_indices = [int(x.strip()) for x in user_input.split(",")]

            # Validate that all selected numbers fall within the valid menu range
            if all(1 <= idx <= len(available_demands) for idx in selected_indices):
                # Map integers back to the actual string names from the dataset
                selected_demands = [available_demands[idx - 1] for idx in selected_indices]
                print(f"✅ Selected categories: {', '.join(selected_demands)}")
                return selected_demands, available_demands
            else:
                print(f"❌ Invalid selection. Please enter numbers between 1 and {all_options_idx}.")

        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2).")

def ask_comparison_targets(all_demands: list, selected_demands: list) -> tuple:
    """Prompts the user to select exactly two demand types for the advanced 
    comparison out of the previously selected options.

    Args:
        all_demands (list): A list of all unique demand types available.
        selected_demands (list): A list of strings containing the names of the 
        demands previously selected by the user.

    Returns:
        tuple: A tuple containing two strings (model_a, model_b) with the names 
        of the two distinct demand types chosen for comparison.
    """
    print("\n🔍 --- ADVANCED COMPARISON SELECTION ---")
    print("You selected multiple demands. Which two would you like to cross-analyze?")

    # Create a map to link the global index (1-based) to each selected demand
    indexed_selection = {}
    for demand in selected_demands:
        global_idx = all_demands.index(demand) + 1
        indexed_selection[global_idx] = demand
        print(f"  [{global_idx}] {demand}")

    while True:
        try:
            user_input = input("\nSelect exactly two numbers separated by a comma (e.g., 1,2): ").strip()
            indices = [int(x.strip()) for x in user_input.split(",")]

            # Validate we got exactly two numbers and both are inside our allowed selection map
            if len(indices) == 2 and all(idx in indexed_selection for idx in indices):
                # Ensure they didn't pick the exact same number twice (e.g., 1,1)
                if indices[0] == indices[1]:
                    print("❌ You cannot compare a demand type against itself. Please pick two different ones.")
                    continue

                model_a = indexed_selection[indices[0]]
                model_b = indexed_selection[indices[1]]
                return model_a, model_b
            else:
                valid_options = ", ".join(map(str, indexed_selection.keys()))
                print(f"❌ Invalid choice. Please enter exactly two numbers from your active options: [{valid_options}].")
        except ValueError:
            print("❌ Input format error. Please use numbers separated by commas only (e.g., 1,2).")