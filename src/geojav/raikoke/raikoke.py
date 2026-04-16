# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Execute script with 'python -i <script>'."""

from dataclasses import dataclass
from pathlib import Path

from cf_units import Unit
import geovista
from geovista.common import to_cartesian, to_lonlat, wrap
from geovista.pantry.data import capitalise
from geovista.crs import to_wkt, WGS84
from geovista.qt import GeoBackgroundPlotter
from geovista.geodesic import line
import iris
import netCDF4 as nc
import numpy as np
import pyvista as pv
from pyvista.plotting.picking import PICKED_REPRESENTATION_NAMES
from geopy.geocoders import Nominatim
from geopy.location import Location
from geopy.exc import GeocoderUnavailable
from matplotlib.colors import ListedColormap

BASE_DIR = Path(__file__).parent

Re = 6371 * 1000 * 3.281 # Earth radius in feet taking 1 m = 3.281 Ft

feet = Unit("feet")
meter = Unit("meter")

#
# callback state
#
reset_clip = False
show_clip = False
show_edges = True
show_flight = False
show_graticule = False
show_isosurfaces = False
show_opacity = False
show_picking = False
show_smooth = False
threshold = min_threshold = 0.2
isosurfaces = 200
isosurfaces_range = (min_threshold, 6.0)
iterations = 20
passband = 0.1
flight_level = 0


@dataclass
class Geocode:
    longitude: float
    latitude: float
    address: str | None = None


def latlon(latitude:float, longitude:float) -> str:
    yunit = "N" if latitude > 0 else "" if latitude == 0 else "S"

    xunit = ""
    longitude = wrap(longitude)[0]
    if longitude not in (0, -180):
        xunit = "W" if longitude < 0 else "E"

    return f"{abs(latitude):.2f}" + r'$\degree$' + f"{yunit} {abs(longitude):.2f}" + r'$\degree$' + f"{xunit}"


def rgba(r, g, b):
    return np.array([r / 256, g / 256, b / 256, 1.0])


def qva(vmin=0.2, vmax=13.0):
    step = 0.01
    mapping = np.arange(vmin, vmax + step, step)
    N = mapping.size

    colors = np.empty((N, 4), dtype=float)

    c01 = rgba(160, 210, 255)   # [vmin,  2.0) - low
    c02 = rgba(255, 153, 0)     # [2.0,   5.0) - medium
    c03 = rgba(255, 40, 0)      # [5.0,  10.0) - high
    c04 = rgba(170, 0, 170)     # [10.0, vmax] - very high

    colors[mapping >= 10] = c04
    colors[mapping < 10] = c03
    colors[mapping < 5] = c02
    colors[mapping < 2] = c01

    return ListedColormap(colors, name="qva", N=N)


def cache(mesh, data, tstep) -> pv.UnstructuredGrid:
    tdir = BASE_DIR / "vtk"
    tdir.mkdir(exist_ok=True)
    fname = tdir / f"raikoke_{tstep}.vtk"
    if not fname.exists():
        tdata = np.ma.masked_less_equal(data[tstep][:], 0).filled(np.nan).flatten()
        mesh["data"] = tdata
        mesh["idx"] = np.arange(mesh.n_cells)
        to_wkt(mesh, WGS84)
        mesh.active_scalars_name = "data"
        tmp = mesh.threshold()
        tmp.save(fname)
        result = tmp
    else:
        result = pv.read(fname)
    return result


def callback_isosurfaces(value) -> None:
    global isosurfaces

    isosurfaces = int(f"{value:.0f}")
    callback_render(None)


def callback_iterations(value) -> None:
    global iterations
    global p

    iterations = int(f"{value:.0f}")

    p.remove_actor(PICKED_REPRESENTATION_NAMES["element"])

    callback_render(None)


def callback_flight(value) -> None:
    global flight_level

    flight_level = int(f"{value:.0f}") // 50
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


def callback_passband(value) -> None:
    global passband
    global p

    passband = float(f"{value:.2f}")

    p.remove_actor(PICKED_REPRESENTATION_NAMES["element"])

    callback_render(None)


def callback_threshold(value) -> None:
    global threshold
    global p

    threshold = value

    p.remove_actor(PICKED_REPRESENTATION_NAMES["element"])

    callback_render(None)


def checkbox_clip(flag: bool) -> None:
    global show_clip
    global show_isosurfaces
    global show_smooth
    global show_edges
    global show_flight
    global actor_checkbox_isosurface
    global actor_isosurfaces
    global actor_threshold
    global actor_min
    global actor_max
    global actor_checkbox_smooth
    global actor_iterations
    global actor_passband
    global actor_checkbox_edges
    global actor_checkbox_flight
    global actor_flight
    global actor_checkbox_picking
    global p

    show_clip = bool(flag)

    if show_clip:
        actor_checkbox_isosurface.GetRepresentation().SetState(0)
        actor_checkbox_smooth.GetRepresentation().SetState(0)
        actor_checkbox_edges.GetRepresentation().SetState(1)
        actor_checkbox_flight.GetRepresentation().SetState(0)
        actor_checkbox_picking.GetRepresentation().SetState(0)

        show_isosurfaces = False
        show_smooth = False
        show_edges = True
        show_flight = False

        actor_isosurfaces.GetRepresentation().SetVisibility(False)
        actor_min.GetRepresentation().SetVisibility(False)
        actor_max.GetRepresentation().SetVisibility(False)
        actor_threshold.GetRepresentation().SetVisibility(False)
        actor_iterations.GetRepresentation().SetVisibility(False)
        actor_passband.GetRepresentation().SetVisibility(False)
        actor_flight.GetRepresentation().SetVisibility(False)
    else:
        actor_threshold.GetRepresentation().SetVisibility(True)

    checkbox_picking(False)

    callback_render(None)


def checkbox_edges(flag: bool) -> None:
    global show_edges
    global show_clip
    global actor_checkbox_edges

    if show_clip:
        show_edges = True
        actor_checkbox_edges.GetRepresentation().SetState(1)
    else:
        show_edges = bool(flag)

    if not show_clip:
        callback_render(None)


def checkbox_flight(flag: bool) -> None:
    global show_flight
    global show_clip
    global show_isosurfaces
    global actor_checkbox_flight
    global actor_flight
    global actor_threshold

    if show_clip or show_isosurfaces:
        show_flight = False
        actor_checkbox_flight.GetRepresentation().SetState(0)
        actor_threshold.GetRepresentation().SetVisibility(False)
    else:
        show_flight = bool(flag)

    actor_flight.GetRepresentation().SetVisibility(show_flight)

    if not (show_clip or show_isosurfaces):
        state = not show_flight
        if state and show_isosurfaces:
            state = False
        actor_threshold.GetRepresentation().SetVisibility(state)
        callback_render(None)


def checkbox_graticule(flag: bool) -> None:
    global p

    actors = [name for name in p.actors.keys() if name.startswith("meridian") or name.startswith("parallel")]
    flag = bool(flag)

    if flag and not actors:
        p.add_graticule(lat_step=15, lon_step=30, mesh_args={"zlevel": 0, "reset_camera": False})

    for actor in actors:
        p.actors[actor].SetVisibility(flag)


def checkbox_isosurfaces(flag: bool) -> None:
    global show_isosurfaces
    global show_clip
    global show_smooth
    global show_flight
    global show_picking
    global actor_isosurfaces
    global actor_threshold
    global actor_min
    global actor_max
    global actor_checkbox_isosurface
    global actor_checkbox_flight
    global actor_checkbox_picking

    if show_clip:
        show_isosurfaces = False
        actor_checkbox_isosurface.GetRepresentation().SetState(0)
        actor_threshold.GetRepresentation().SetVisibility(False)
    else:
        show_isosurfaces = bool(flag)

    actor_isosurfaces.GetRepresentation().SetVisibility(show_isosurfaces)
    actor_min.GetRepresentation().SetVisibility(show_isosurfaces)
    actor_max.GetRepresentation().SetVisibility(show_isosurfaces)

    if not show_clip:
        state = not show_isosurfaces
        if state and show_smooth:
            state = False
        actor_threshold.GetRepresentation().SetVisibility(state)
        if show_isosurfaces:
            show_flight = False
            actor_checkbox_flight.GetRepresentation().SetState(0)
            actor_flight.GetRepresentation().SetVisibility(False)
            actor_checkbox_picking.GetRepresentation().SetState(0)
            checkbox_picking(False)
        callback_render(None)


def checkbox_opacity(flag: bool) -> None:
    global show_opacity
    global actor_base
    global p

    show_opacity = bool(flag)

    if show_opacity:
        p.enable_depth_peeling()
        actor_base.GetProperty().SetOpacity(0.5)
    else:
        p.disable_depth_peeling()
        actor_base.GetProperty().SetOpacity(1.0)


def checkbox_picking(flag: bool) -> None:
    global show_clip
    global show_isosurfaces
    global show_picking
    global p
    global actor_hud
    global feet
    global meter
    global n_hcells

    def picking_callback(pick) -> None:
        global p
        global actor_hud
        global n_hcells

        # for name in p.actors.keys():
        #     if name.startswith("vtkOpenGLActor"):
        #         p.remove_actor(name)
        #         break

        xyz = pick.cell_centers().points[0]
        radius = np.linalg.norm(xyz)
        lon, lat = to_lonlat(xyz, radius=radius)
        location = latlon(lat, lon)

        sample = pick["data"][0]

        flight_level = pick["idx"][0] // n_hcells
        lower = int(feet.convert(flight_level*50*100, meter))
        upper = int(feet.convert((flight_level+1)*50*100, meter))

        hud = f"{location}, {lower:,}-{upper:,}m [FL: {flight_level*50:,}-{(flight_level+1)*50:,}], " + f"{sample:.2f}" + r"mg m$^{\text{-3}}$"
        actor_hud.SetText(0, f"{hud}")

    if show_clip or show_isosurfaces:
        show_picking = False
        actor_checkbox_picking.GetRepresentation().SetState(0)
    else:
        show_picking = bool(flag)

    if show_picking:
        p.enable_element_picking(
            callback=picking_callback,
            left_clicking=False,
            show_message=False,
            line_width=10,
            render_lines_as_tubes=True,
        )
    else:
        # TODO: remove the picking actor
        p.disable_picking()
        p.remove_actor(PICKED_REPRESENTATION_NAMES["element"])
        actor_hud.SetText(0, "")


def checkbox_smooth(flag: bool) -> None:
    global show_smooth
    global show_clip
    global show_isosurfaces
    global actor_iterations
    global actor_passband
    global actor_threshold
    global actor_checkbox_smooth
    global p

    p.remove_actor(PICKED_REPRESENTATION_NAMES["element"])

    if show_clip:
        show_smooth = False
        actor_checkbox_smooth.GetRepresentation().SetState(0)
        actor_threshold.GetRepresentation().SetVisibility(False)
    else:
        show_smooth = bool(flag)

    actor_iterations.GetRepresentation().SetVisibility(show_smooth)
    actor_passband.GetRepresentation().SetVisibility(show_smooth)

    if not show_clip:
        state = not show_smooth
        if state and show_isosurfaces:
            state = False
        actor_threshold.GetRepresentation().SetVisibility(state)
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
    global iterations
    global passband
    global min_threshold
    global flight_level
    global n_hcells
    global title
    global actor_title
    global feet
    global meter


    if value is None:
        value = tstep
    else:
        reset_clip = True
        p.remove_actor(PICKED_REPRESENTATION_NAMES["element"])

    value = int(f"{value:.0f}")
    tstep = value % n_tsteps

    frame = cache(mesh, data, tstep)

    if show_isosurfaces:
        if min_threshold:
            frame = frame.threshold(min_threshold)
    elif threshold:
        frame = frame.threshold(threshold)

    if frame.is_empty:
        p.remove_actor("plume")
    else:
        if reset_clip:
            if p.plane_widgets:
                p.plane_widgets.pop().Off()

        if show_clip:
            xyz = np.asarray(frame.center)
            norm = np.linalg.norm(xyz)

            p.remove_actor("flight")
            actor_title.SetInput(title)

            p.add_mesh_clip_plane(
                frame,
                widget_color=color,
                normal=-xyz / norm,
                implicit=False,
                outline_translation=True,
                name="plume",
                render=False,
                reset_camera=False,
                show_edges=True,
                edge_color="gray",
                cmap=cmap,
                clim=clim,
                show_scalar_bar=False,
                pickable=False,
            )
        else:
            opacity = None
            tcmap = cmap
            smooth_shading = False
            tshow_edges = show_edges
            show_scalar_bar = False

            if p.plane_widgets:
                p.plane_widgets.pop().Off()
                p.remove_actor("plume")

            if show_smooth:
                frame = frame.clean(tolerance=1e-5).triangulate().extract_surface(algorithm=None).smooth_taubin(
                    n_iter=iterations,
                    pass_band=passband,
                    normalize_coordinates=True,
                    feature_angle=30,
                    non_manifold_smoothing=True
                )

            if show_isosurfaces:
                opacity = "linear_r"
                tcmap = "fire_r"
                smooth_shading = True
                tshow_edges = False
                frame = frame.cell_data_to_point_data().contour(isosurfaces, rng=isosurfaces_range)
                p.remove_actor(actor_scalar)
                show_scalar_bar = True

            if show_flight:
                idx = frame["idx"]
                mask = np.where((idx >= n_hcells*flight_level) & (idx < n_hcells*(flight_level+1)))[0]
                if mask.size > 0:
                    flight = frame.extract_cells(mask)
                    p.add_mesh(
                        flight,
                        name="flight",
                        color="white" if flight_level % 2 else "black",
                        line_width=4,
                        style="wireframe",
                        render=False,
                        reset_camera=False,
                        render_lines_as_tubes=True,
                        pickable=False,
                    )
                    lower = int(feet.convert(flight_level*50*100, meter))
                    upper = int(feet.convert((flight_level+1)*50*100, meter))
                    text = f"{title}\tAlt: {lower:,}-{upper:,}m (AMSL)\t\tFL: {flight_level*50:,}-{(flight_level+1)*50:,}"
                    actor_title.SetInput(text)
                else:
                    p.remove_actor("flight")
                    actor_title.SetInput(title)
            else:
                p.remove_actor("flight")
                actor_title.SetInput(title)

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
                show_scalar_bar=show_scalar_bar,
                pickable=True,
            )

            if not show_isosurfaces:
                p.add_actor(actor_scalar)

    reset_clip = False
    actor.SetText(3, unit.num2date(t.points[tstep]).strftime(fmt))


# sort the assets in date ascending date order
fname = BASE_DIR / "data" / "volcanic_ash_air_concentration.nc"
cube = iris.load_cube(fname)

ds = nc.Dataset(fname)
data = ds.variables["volcanic_ash_air_concentration"]

# bootstrap
t = cube.coord("time")
z = cube.coord("flight_level")
y = cube.coord("latitude")
x = cube.coord("longitude")

unit = Unit(t.units)
fmt = "%Y-%m-%d %H:%M UTC"

n_tsteps = t.shape[0]
tstep = 0

y_cb = y.contiguous_bounds()
x_cb = x.contiguous_bounds()
z_cb = z.contiguous_bounds()

n_hcells = (x_cb.size - 1) * (y_cb.size - 1)

zscale = np.mean(np.diff(y_cb))*(np.pi/180)/(np.mean(np.diff(z_cb))*100/Re) #mean latitude step (radians)/mean altitude step (feet) over Earth Radius
z_h =(z_cb*100)/Re*zscale

xx, yy, zz = np.meshgrid(x_cb, y_cb, z_h, indexing="ij")
shape = xx.shape

dmin, dmax = 0.2, 13.0
clim = (dmin, dmax)

xyz = to_cartesian(xx, yy, zlevel=zz, zscale=1)
mesh = pv.StructuredGrid(xyz[:, 0].reshape(shape), xyz[:, 1].reshape(shape), xyz[:, 2].reshape(shape))

cmap = qva(*clim)
color = "white"

frame = cache(mesh, data, tstep)

p = GeoBackgroundPlotter()
p.set_background(color="black")

sargs = {
    "color": color,
    "title": f"{capitalise(cube.name())}" + r" (mg m$^{\text{-3}}$)",
    "n_labels": 0,
    "position_x": 0.45,
    "width": 0.55,
}

annotations = {
    0.2: "0.2",
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
    annotations=annotations,
    pickable=True,
)
p.view_poi()
actor_scalar = p.add_scalar_bar(mapper=actor_plume.mapper, **sargs)

try:
    geolocator = Nominatim(user_agent="geovista")
    raikoke = geolocator.geocode("Raikoke", language="en")
except GeocoderUnavailable:
    raikoke = Geocode(longitude=153.25, latitude=48.292)

p.add_points(
    xs=raikoke.longitude,
    ys=raikoke.latitude,
    render_points_as_spheres=True,
    color="yellow",
    point_size=10,
    pickable=False,
)
actor_base = p.add_base_layer(
    texture=geovista.blue_marble(),
    zlevel=0,
    resolution="c192",
    pickable=False
)
p.add_coastlines(color="lightgray", pickable=False)
p.add_axes(color=color)

# Defining Raikoke Legend
fname = BASE_DIR / "images" / "raikoke_inset.png"
p.add_logo_widget(fname, position=(0.00, 0.91), size=(0.08, 0.08))

title = f"Raikoke: {latlon(raikoke.latitude, raikoke.longitude)}"
actor_title = p.add_text(
    title,
    position=(0.08, 0.96),
    viewport=True,
    font_size=15,
    color=color,
)

address = f'{", ".join([word.strip() for word in raikoke.address.split(",")[1:]])}\n' if raikoke.address else ""
p.add_text(
    f"{address}Vertical Scale Factor: x{zscale:.2f}",
    position=(0.08, 0.91),
    viewport=True,
    font_size=10,
    color=color,
)

text = unit.num2date(t.points[tstep]).strftime(fmt)
actor = p.add_text(text, position="upper_right", font_size=15, color=color, shadow=False)

actor_hud = p.add_text(
    "",
    position="lower_left",
    font_size=8,
    color="white",
)

#
# sliders
#

p.add_slider_widget(
    callback_render,
    (0, n_tsteps-1),
    value=0,
    pointa=(0.55, 0.85),
    pointb=(0.90, 0.85),
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
    (0.2, 6.0),
    value=threshold,
    pointa=(0.55, 0.75),
    pointb=(0.90, 0.75),
    color=color,
    fmt="%.2f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title=r"Threshold (mg m$^{\text{-3}}$)",
    title_height=0.02,
)

actor_isosurfaces = p.add_slider_widget(
    callback_isosurfaces,
    (10, 3000),
    value=isosurfaces,
    pointa=(0.10, 0.85),
    pointb=(0.45, 0.85),
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
    pointa=(0.10, 0.75),
    pointb=(0.45, 0.75),
    color=color,
    fmt="%.2f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title=r"Isosurface Thresholds (mg m$^{\text{-3}}$)",
    title_height=0.02,
)
actor_min.GetRepresentation().SetVisibility(False)

actor_max = p.add_slider_widget(
    callback_max,
    isosurfaces_range,
    value=vmax,
    pointa=(0.10, 0.75),
    pointb=(0.45, 0.75),
    color=color,
    fmt="%.2f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title_height=0.02,
)
actor_max.GetRepresentation().SetVisibility(False)

actor_iterations = p.add_slider_widget(
    callback_iterations,
    (5, 100),
    value=iterations,
    pointa=(0.55, 0.75),
    pointb=(0.90, 0.75),
    color=color,
    fmt="%.0f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title="Iterations",
    title_height=0.02,
)
actor_iterations.GetRepresentation().SetVisibility(False)

actor_passband = p.add_slider_widget(
    callback_passband,
    (0.01, 2),
    value=passband,
    pointa=(0.55, 0.65),
    pointb=(0.90, 0.65),
    color=color,
    fmt="%.2f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title="Passband",
    title_height=0.02,
)
actor_passband.GetRepresentation().SetVisibility(False)

actor_flight = p.add_slider_widget(
    callback_flight,
    (z_cb[0], z_cb[-1]),
    value=flight_level,
    pointa=(0.10, 0.85),
    pointb=(0.45, 0.85),
    color=color,
    fmt="%.0f",
    style="modern",
    slider_width=0.02,
    tube_width=0.001,
    title=r"Flight Level",
    title_height=0.02,
)
actor_flight.GetRepresentation().SetVisibility(False)

#
# checkboxes
#

size, pad = 25, 3
x, y = 10, 95
offset = size * 0.2
font_size = 10

actor_checkbox_smooth = p.add_checkbox_button_widget(
    checkbox_smooth,
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

actor_checkbox_picking = p.add_checkbox_button_widget(
    checkbox_picking,
    value=show_picking,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Picking",
    position=(x + size + offset, y),
    font_size=font_size,
    color=color,
)

y += size + pad

actor_checkbox_opacity = p.add_checkbox_button_widget(
    checkbox_opacity,
    value=show_opacity,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Opacity",
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

actor_checkbox_edges = p.add_checkbox_button_widget(
    checkbox_graticule,
    value=show_graticule,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Graticule",
    position=(x + size + offset, y),
    font_size=font_size,
    color=color,
)

y += size + pad

actor_checkbox_flight = p.add_checkbox_button_widget(
    checkbox_flight,
    value=show_flight,
    color_on="green",
    color_off="red",
    size=size,
    position=(x, y),
)
p.add_text(
    "Flight Level",
    position=(x + size + offset, y),
    font_size=font_size,
    color=color,
)

y += size + pad

actor_checkbox_edges = p.add_checkbox_button_widget(
    checkbox_edges,
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
    checkbox_clip,
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
