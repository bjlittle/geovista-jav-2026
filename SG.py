import pyvista as pv
import numpy as np

x = np.sort(np.random.rand(20) * 30)
y = np.sort(np.random.rand(30) * 30)
z = np.sort(np.random.rand(10) * 30)
xx, yy, zz = np.meshgrid(x, y, z, indexing = "ij")
mesh = pv.StructuredGrid(xx, yy, zz)
mesh.plot(show_edges=True)
