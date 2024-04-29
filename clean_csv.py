import pandas as pd

# Import CSV file into a DataFrame
df = pd.read_csv('./ephe/star_names_and_magnitudes.csv', header=1)

# Drop rows with NaN values
df = df.dropna()

# Replace all 999.99 values with the mean of the column (excluding 999.99)
df = df.replace(999.99, df[df != 999.99].mean())

# Save the cleaned DataFrame to a new CSV file
df.to_csv('./ephe/cleaned_star_data.csv', index=False)