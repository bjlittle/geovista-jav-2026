import geovista
import pyvista as pv
from geovista.qt import GeoBackgroundPlotter
from pathlib import Path

############################################################################
# Minimal example of using geojav to visualise a single precomputed time   #
# step of the Reykjanes Sulphur dioxide cloud created to illustrate the    #
# use of geovista in the geojav project. The mesh is loaded from a VTK     #
# file and visualised with a base layer, coastlines, and a point marker    #
# for the source location.                                                 #
#Run with "python -i sample.py" within the geojav pixi or conda environment#
############################################################################

BASE_DIR = Path(__file__).parent
fname = BASE_DIR/'reykjanes_043.vtk' #path to mesh for time step 159
frame = pv.read(fname) #load mesh

p = GeoBackgroundPlotter(toolbar=False, menu_bar=False,title="geojav-2026: Minimal Sample", border=False) #initialising plotter
p.set_background(color="black") #set background colour to black

actor_base = p.add_base_layer( #adding base layer
    texture=geovista.blue_marble(), #with earth texture
    zlevel=0)

p.add_coastlines(color="lightgray", #Adding grey coastlines
    zlevel=0 )

p.add_points( #Adding source location marker
    xs=-22.384, #longitude
    ys=63.882, #latitude
    render_points_as_spheres=True, #adds point as a sphere
    color="orange", #marker colour
    point_size=10 )

actor_plume = p.add_mesh( #Adds the mesh "frame" to the
    frame, #plotter
    name="plume",
    cmap="magma_r", #colour map used
    show_scalar_bar=False, #dont render colour bar
    show_edges=False, #don't render cell edges
    log_scale=True ) #use a log scale for colouring

p.view_poi()

sargs = {
    "color": "white",
    "title": f"Sulphur Dioxide Air Concentration" + r" $(\mu g \ m^{-3})$",
    "fmt": "%.1f",
}

actor_scalar_bar = p.add_scalar_bar(mapper=actor_plume.mapper, **sargs)

p.show() #launches a window and renders the plotter within it