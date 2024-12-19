import pandas as pd
import streamlit as st
import plotly.graph_objs as go
import json

# Load the dataset for offline servers
df_offline = pd.read_csv('./offline servers all.csv')

# Convert 'Installation Date' to datetime and extract the year as string
df_offline['Installation Date'] = pd.to_datetime(df_offline['Installation Date'], errors='coerce')
df_offline['Installation Year'] = df_offline['Installation Date'].dt.year.astype(str)  # Convert to string

# Load the simplified GeoJSON for Nepal's districts
with open('./nepal-districts-new-reduced.json') as geo:
    nepal_districts = json.load(geo)

# Extract province code and add it to the dataframe
province_mapping = {feature['properties']['DIST_PCODE']: feature['properties']['ADM1_PCODE']
                    for feature in nepal_districts['features']}
df_offline['Province Code'] = df_offline['DIST_PCODE'].map(province_mapping)

# Convert 'DIST_PCODE' to string and handle NaN values
df_offline['DIST_PCODE'] = df_offline['DIST_PCODE'].fillna('Unknown').astype(str)

# Province names mapped to their codes
province_names = {
    'NP01': 'Koshi', 'NP02': 'Madhesh', 'NP03': 'Bagmati', 'NP04': 'Gandaki',
    'NP05': 'Lumbini', 'NP06': 'Karnali', 'NP07': 'Sudurpashchim'
}

# Prepare province options with names
province_options = ['All'] + [province_names.get(province, 'Unknown') for province in sorted(df_offline['Province Code'].dropna().unique())]

# Prepare year options
year_options = ['All'] + sorted(df_offline['Installation Year'].dropna().unique())

# Function to generate the map figure
def generate_map(df, nepal_districts):
    # Merge the district names into the aggregated data
    df = df.merge(df_offline[['DIST_PCODE', 'DIST_EN']].drop_duplicates(), on='DIST_PCODE', how='left')

    # Define a color scale
    color_scale = "YlGnBu"

    # Adjust the map figure
    fig = go.Figure(go.Choroplethmapbox(geojson=nepal_districts,
                                        locations=df['DIST_PCODE'],
                                        z=df['Installations'],
                                        featureidkey="properties.DIST_PCODE",
                                        colorscale=color_scale,
                                        marker_opacity=0.5,
                                        marker_line_width=1,
                                        marker_line_color='black',
                                        coloraxis='coloraxis',
                                        text=df['DIST_EN'],
                                        hoverinfo='text+z',
                                        hovertemplate="<b>%{text}</b><br>%{z} servers<extra></extra>"))

    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=5.5,
                      mapbox_center={"lat": 28.3949, "lon": 84.1240},
                      margin={"r": 0, "t": 0, "l": 0, "b": 50},
                      coloraxis=dict(colorscale=color_scale))

    # Update color bar to be horizontal and positioned below the map
    fig.update_layout(coloraxis_colorbar=dict(
        title="Offline Server Installations",
        orientation='h',
        x=0.5,
        xanchor='center',
        y=-0.1,
        titleside='bottom',
        tickvals=[0, 50, 100],
        lenmode='fraction',
        len=0.5,
    ))

    return fig


# Streamlit App Layout
st.title("Offline Server Installations in Nepal")

# Year dropdown
selected_year = st.selectbox("Select Installation Year", year_options)

# Province dropdown
selected_province = st.selectbox("Select Province", province_options)

# District dropdown
district_options = ['All'] + [row['DIST_EN'] for _, row in df_offline.drop_duplicates(subset=['DIST_PCODE']).iterrows()]
selected_district = st.selectbox("Select District", district_options)

# Reset button
if st.button('Reset Filters'):
    selected_year = 'All'
    selected_province = 'All'
    selected_district = 'All'
    st.experimental_rerun()

# Filter data based on selections
filtered_df = df_offline.copy()

if selected_year != 'All':
    filtered_df = filtered_df[filtered_df['Installation Year'] == selected_year]  # No type conversion

if selected_province != 'All':
    province_code = [key for key, value in province_names.items() if value == selected_province]
    if province_code:
        filtered_df = filtered_df[filtered_df['Province Code'] == province_code[0]]

if selected_district != 'All':
    filtered_df = filtered_df[filtered_df['DIST_EN'] == selected_district]

# Aggregate the filtered data
aggregated_data = filtered_df.groupby('DIST_PCODE').size().reset_index(name='Installations')

# Generate the map visualization
fig = generate_map(aggregated_data, nepal_districts)
st.plotly_chart(fig)

# Show the filtered data (optional)
if st.checkbox("Show Filtered Data"):
    st.write(filtered_df)
