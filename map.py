import pandas as pd
import plotly.express as px


def plot_shelters(df):
    fig = px.scatter_map(df,
                            lat="lat",  # Latitude column
                            lon="long",  # Longitude column
                            hover_name="region",  # Region (Shelter name) for the hover info
                            hover_data=["address", "tel", "email", "website"],  # Additional metadata for hover
                            #color="region",  # Use region to color code points (optional)
                            title=f"Shelters ({len(df)})",
                            zoom=5,
                            labels={"lat": "Latitude", "long": "Longitude"})

    fig.update_layout(mapbox_style="open-street-map",
                      mapbox_center={"lat": 51.5074, "lon": -0.1278})  # Center the map (default to London)

    fig.write_html("cat_shelters_map.html")


def main():
    df = pd.read_csv("shelters.csv")
    plot_shelters(df)


if __name__ == "__main__":
    main()
