# Sample

> [!NOTE]
> Please ensure that the `geojav` environment is activated.

This minimal example visualises a single precomputed time step of the Reykjanes sulphur dioxide cloud using `geovista`.
The mesh is loaded from a VTK file and rendered with a base layer, coastlines, and a point marker for the source location.

From the `geovista-jav-2026` base directory change to the `sample` directory:

```bash
> cd src/geojav/sample
```

## Render:

To run the sample script:

```bash
> python -i sample.py
```

> [!IMPORTANT]
> We require to execute `python` along with the `-i` flag (`inspect interactively`) as we are using [pyvistaqt](https://github.com/pyvista/pyvistaqt) to render the scene.

The example loads the `reykjanes_043.vtk` mesh, adds a base layer and coastlines, and highlights the source location with an orange marker.
