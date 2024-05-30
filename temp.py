import plotly.express as px
import pandas as pd
from astro_script import angle_influence  # Ensure this is correctly imported

# Generate values
x = list(range(-11, 11, 100))  # This includes values from -11 to 10
y = [angle_influence(i) for i in x]

# Create a DataFrame for Plotly Express
df = pd.DataFrame({'Angle': x, 'Influence': y})

# Create the plot using Plotly Express
fig = px.line(df, x='Angle', y='Influence', title='Plot of angle_influence function')

# Show the plot
fig.show()
