from geopy.geocoders import Nominatim
import geovista
from geovista.geodesic import line
import geovista.theme


geolocator = Nominatim(user_agent="geovista")
location = geolocator.geocode("reykjanes", language="en")

p = geovista.GeoPlotter(off_screen=True, window_size=(1024, 1024))
p.add_base_layer(texture=geovista.natural_earth_1())
p.add_points(xs=location.longitude, ys=location.latitude, render_points_as_spheres=True, point_size=100, color="orange", lighting=False)
p.view_poi()
p.enable_anti_aliasing(aa_type="ssaa")
p.camera.zoom(1.7)
p.screenshot("reykjanes_inset.png", transparent_background=True)
