"""Execute script with 'python -i <script>'."""
from pathlib import Path

from cf_units import Unit
import geovista
from geovista.common import to_cartesian
from geovista.pantry.data import capitalise
from geovista.crs import to_wkt, WGS84
from geovista.qt import GeoBackgroundPlotter
from geovista.geodesic import line
import iris
import netCDF4 as nc
import numpy as np
import pyvista as pv
from geopy.geocoders import Nominatim
from matplotlib.colors import ListedColormap

#
# callback state
#
reset_clip = False
show_clip = False
show_edges = True
show_isosurfaces = False
show_smooth = False
threshold = 0.2
isosurfaces = 200
isosurfaces_range = (0, 6)


def rgb(r, g, b):
    return (r / 256, g / 256, b / 256, 1.0)


def rgba(r, g, b):
    return np.array([r / 256, g / 256, b / 256, 1.0])


def qva(vmin=0, vmax=13):
    N = 2560
    mapping = np.linspace(vmin, vmax, N, dtype=int)
    colors = np.empty((N, 4))

    c01 = rgba(160, 210, 255)   # 0.2-2.0 mg/m3 (low)
    c02 = rgba(255, 153, 0)     # 2.0-5.0 (medium)
    c03 = rgba(255, 40, 0)      # 5.0-10.0 (high)
    c04 = rgba(170, 0, 170)     # >=10.0 (very high)

    colors[mapping >= 10] = c04
    colors[mapping < 10] = c03
    colors[mapping < 5] = c02
    colors[mapping < 2] = c01

    return ListedColormap(colors, N=N)


def cache(mesh, data, tstep) -> pv.UnstructuredGrid:
    tdir = Path("vtk")
    tdir.mkdir(exist_ok=True)
    fname = tdir / f"raikoke_{tstep}.vtk"
    if not fname.exists():
        tdata = np.ma.masked_less_equal(data[tstep][:], 0).filled(np.nan).flatten()
        mesh["data"] = tdata
        to_wkt(mesh, WGS84)
        mesh.active_scalars_name = "data"
        tmp = mesh.threshold()
        tmp.save(fname)
        result = tmp
    else:
        result = pv.read(fname)
    return result


def callback_clip(flag: bool) -> None:
    global show_clip
    global actor_checkbox_isosurface
    global actor_isosurfaces
    global actor_threshold
    global actor_min
    global actor_max

    show_clip = bool(flag)

    if show_clip:
        actor_isosurfaces.GetRepresentation().SetVisibility(False)
        actor_min.GetRepresentation().SetVisibility(False)
        actor_max.GetRepresentation().SetVisibility(False)
        actor_threshold.GetRepresentation().SetVisibility(False)
    else:
        state = bool(actor_checkbox_isosurface.GetRepresentation().GetState())
        actor_isosurfaces.GetRepresentation().SetVisibility(state)
        actor_min.GetRepresentation().SetVisibility(state)
        actor_max.GetRepresentation().SetVisibility(state)
        actor_threshold.GetRepresentation().SetVisibility(not state)

    callback_render(None)


def callback_edges(flag: bool) -> None:
    global show_edges

    show_edges = bool(flag)
    callback_render(None)


def callback_isosurfaces(value) -> None:
    global isosurfaces

    isosurfaces = int(f"{value:.0f}")
    callback_render(None)


def callback_max(max_value) -> None:
    global isosurfaces_range
    global actor_min

    min_value = isosurfaces_range[0]
    if max_value < min_value:
        # force the movement of the minimum value
        min_value = max_value
        actor_min.GetRepresentation().SetValue(min_value)

    isosurfaces_range = (min_value, max_value)
    callback_render(None)


def callback_min(min_value: float) -> None:
    global isosurfaces_range
    global actor_max

    max_value = isosurfaces_range[1]
    if min_value > max_value:
        # force the movement of the maximum value
        max_value = min_value
        actor_max.GetRepresentation().SetValue(max_value)

    isosurfaces_range = (min_value, max_value)
    callback_render(None)


def callback_smooth(flag: bool) -> None:
    global show_smooth

    show_smooth = bool(flag)
    callback_render(None)


def callback_threshold(value) -> None:
    global threshold

    threshold = value
    callback_render(None)


def checkbox_isosurfaces(flag: bool) -> None:
    global show_isosurfaces
    global actor_isosurfaces
    global actor_threshold
    global actor_min
    global actor_max

    show_isosurfaces = bool(flag)
    actor_isosurfaces.GetRepresentation().SetVisibility(show_isosurfaces)
    actor_min.GetRepresentation().SetVisibility(show_isosurfaces)
    actor_max.GetRepresentation().SetVisibility(show_isosurfaces)
    actor_threshold.GetRepresentation().SetVisibility(not show_isosurfaces)
    callback_render(None)


def callback_render(value) -> None:
    global tstep
    global n_tsteps
    global data
    global mesh
    global fmt
    global t
    global unit
    global actor
    global clim
    global p
    global cmap
    global sargs
    global show_edges
    global annotations
    global threshold
    global show_isosurfaces
    global isosurfaces
    global isosurfaces_range
    global show_smooth
    global show_clip
    global reset_clip
    global actor_scalar

    if value is None:
        value = tstep
    else:
        reset_clip = True

    value = int(f"{value:.0f}")
    tstep = value % n_tsteps

    frame = cache(mesh, data, tstep)

    if not show_isosurfaces and threshold:
        frame = frame.threshold(threshold)

    if frame.is_empty:
        p.remove_actor("plume")
    else:
        if reset_clip:
            if p.plane_widgets:
                p.plane_widgets.pop().Off()

        if show_clip:
            p.add_mesh_clip_plane(
                frame,
                widget_color=color,
                normal="z",
                outline_opacity=0,
                name="plume",
                render=False,
                reset_camera=False,
                show_edges=True,
                edge_color="gray",
                cmap=cmap,
                clim=clim,
                show_scalar_bar=False,
            )
        else:
            opacity = None
            tcmap = cmap
            smooth_shading = False
            tshow_edges = show_edges    

            if p.plane_widgets:
                p.plane_widgets.pop().Off()
                p.remove_actor("plume")

            if show_smooth:
                frame = frame.clean(tolerance=1e-5).triangulate().extract_surface().smooth_taubin(
                    n_iter=50,
                    pass_band=0.02,
                    normalize_coordinates=True,
                    feature_angle=30,
                    non_manifold_smoothing=True
                )
                smooth_shading = False

            if show_isosurfaces:
                opacity = "linear_r"
                tcmap = "fire_r"
                smooth_shading = True
                tshow_edges = False
                frame = frame.cell_data_to_point_data().contour(isosurfaces, rng=isosurfaces_range)

            p.add_mesh(
                frame,
                name="plume",
                cmap=tcmap,
                clim=clim,
                render=False,
                reset_camera=False,
                scalar_bar_args=sargs,
                show_edges=tshow_edges,
                edge_color="gray",
                annotations=annotations,
                opacity=opacity,
                smooth_shading=smooth_shading,
                show_scalar_bar=False,
            )

            p.add_actor(actor_scalar)
    
    reset_clip = False
    actor.SetText(3, unit.num2date(t.points[tstep]).strftime(fmt))


# sort the assets in date ascending date order
fname = "data/volcanic_ash_air_concentration.nc"
cube = iris.load_cube(fname)

ds = nc.Dataset(fname)
data = ds.variables["volcanic_ash_air_concentration"]

# bootstrap
t = cube.coord("time")
z = cube.coord("flight_level")
y = cube.coord("latitude")
x = cube.coord("longitude")

unit = Unit(t.units)
fmt = "%Y-%m-%d %H:%M"

n_tsteps = t.shape[0]
tstep = 0

y_cb = y.contiguous_bounds()
x_cb = x.contiguous_bounds()
z_cb = z.contiguous_bounds()
z_fix = np.arange(*z_cb.shape) * np.mean(np.diff(y_cb)) * 3

xx, yy, zz = np.meshgrid(x_cb, y_cb, z_fix, indexing="ij")
shape = xx.shape

dmin, dmax = 0.0, 13
clim = (dmin, dmax)

xyz = to_cartesian(xx, yy, zlevel=zz, zscale=0.005)
mesh = pv.StructuredGrid(xyz[:, 0].reshape(shape), xyz[:, 1].reshape(shape), xyz[:, 2].reshape(shape))

cmap = qva()
color = "white"

frame = cache(mesh, data, tstep)

p = GeoBackgroundPlotter()
p.set_background(color="black")

sargs = {
    "color": color,
    "title": f"{capitalise(cube.name())} ({str(cube.units)})",
    "n_labels": 0,
    "position_x": 0.45,
    "width": 0.55,
}

annotations = {
    # 1.0: "Low",
    2.0: "2.0",
    # 3.5: "Medium",
    5.0: "5.0",
    # 7.5: "High",
    10.0: "10.0",
    # 12.5: "Very High",
}

actor_plume = p.add_mesh(
    frame,
    name="plume",
    cmap=cmap,
    clim=clim,
    show_scalar_bar=False,
    show_edges=show_edges,
    edge_color="gray",
    annotations=annotations
)
p.view_poi()
actor_scalar = p.add_scalar_bar(mapper=actor_plume.mapper, **sargs)

geolocator = Nominatim(user_agent="geovista")
location = geolocator.geocode("Raikoke", language="en")

p.add_points(xs=location.longitude, ys=location.latitude, render_points_as_spheres=True, color="red", point_size=10)
p.add_base_layer(texture=geovista.natural_earth_1(), zlevel=0, resolution="c192")
p.add_coastlines(color="lightgray")
p.add_mesh(line(-180, [90, 0, -90]), color="orange", line_width=3)
p.add_axes(color=color)

p.add_text(location.address, position="upper_left", font_size=15, color=color, shadow=False)

text = unit.num2date(t.points[tstep]).strftime(fmt)
actor = p.add_text(text, position="upper_right", font_size=10, color=color, shadow=False)

#
# sliders
#

p.add_slider_widget(
    callback_render,
    (0, n_tsteps-1),
    value=0,
    pointa=(0.55, 0.90),
    pointb=(0.95, 0.90),
    color=color,
    fmt="%.0f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title="Time Step",
    title_height=0.02,
)

actor_threshold = p.add_slider_widget(
    callback_threshold,
    (0.2, 5),
    value=threshold,
    pointa=(0.55, 0.80),
    pointb=(0.95, 0.80),
    color=color,
    fmt="%.2f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title=f"Threshold ({str(cube.units)})",
    title_height=0.02,
)

actor_isosurfaces = p.add_slider_widget(
    callback_isosurfaces,
    (10, 3000),
    value=isosurfaces,
    pointa=(0.05, 0.90),
    pointb=(0.45, 0.90),
    color=color,
    fmt="%.0f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title="Isosurfaces",
    title_height=0.02,
)
actor_isosurfaces.GetRepresentation().SetVisibility(False)

vmin, vmax = isosurfaces_range
actor_min = p.add_slider_widget(
    callback_min,
    isosurfaces_range,
    value=vmin,
    pointa=(0.05, 0.80),
    pointb=(0.45, 0.80),
    color=color,
    fmt="%.2f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title=f"Isosurface Thresholds ({str(cube.units)})",
    title_height=0.02,
)
actor_min.GetRepresentation().SetVisibility(False)

actor_max = p.add_slider_widget(
    callback_max,
    isosurfaces_range,
    value=vmax,
    pointa=(0.05, 0.80),
    pointb=(0.45, 0.80),
    color=color,
    fmt="%.2f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title_height=0.02,
)
actor_max.GetRepresentation().SetVisibility(False)

#
# checkboxes
#

size, pad = 25, 3
x, y = 10, 100
offset = size * 0.2
font_size = 10

p.add_checkbox_button_widget(
    callback_smooth,
    value=show_smooth,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Smooth",
    position=(x + size + offset, y),
    font_size=font_size,
    color=color,
)

y += size + pad

actor_checkbox_isosurface = p.add_checkbox_button_widget(
    checkbox_isosurfaces,
    value=show_isosurfaces,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Isosurfaces",
    position=(x + size + offset, y),
    font_size=font_size,
    color=color,
)

y += size + pad

p.add_checkbox_button_widget(
    callback_edges,
    value=show_edges,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Edges",
    position=(x + size + offset, y),
    font_size=font_size,
    color=color,
)

y += size + pad

p.add_checkbox_button_widget(
    callback_clip,
    value=show_clip,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Clip",
    position=(x + size + offset, y),
    font_size=font_size,
    color=color,
)

p.show()
