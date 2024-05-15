import json

def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data, file_path):
    """Save JSON data to a file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def merge_json_files(file1_path, file2_path, output_path):
    """Merge two JSON files with nested objects and save the result to a new file."""
    # Load data from the JSON files
    data1 = load_json(file1_path)
    data2 = load_json(file2_path)
    
    # Check if the data is in the expected format (dictionaries)
    if not isinstance(data1, dict) or not isinstance(data2, dict):
        raise ValueError("Both JSON files should contain dictionaries")
    
    # Merge the dictionaries
    merged_data = {**data1, **data2}
    
    # Save the merged data to the output file
    save_json(merged_data, output_path)

if __name__ == "__main__":
    # Example usage
    file1 = 'file1.json'
    file2 = 'file2.json'
    output_file = 'merged.json'
    
    merge_json_files(file1, file2, output_file)
    print(f"Merged JSON saved to {output_file}")
