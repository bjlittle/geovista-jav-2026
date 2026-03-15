# Reykjanes (Iceland)

<p align="center">
  <a href="https://github.com/bjlittle/geovista-jav-2026/blob/main/src/geojav/reykjanes/README.md">
    <img src="https://raw.githubusercontent.com/bjlittle/geovista-data-jav-2026/2026.03.3/assets/media/reykjanes.png"
         alt="Reykjanes Plume Isosurface"
         style="width: 75%; height: 75%"></a>
</p>

> [!NOTE]
> Please ensure that the `geojav` environment is activated.

We require to download the `reykjanes` dataset for preprocessing prior to rendering.

From the `geovista-jav-2026` base directory change to the `reykjanes` directory:

```bash
> cd src/geojav/reykjanes
```


## Unpack: Combine NetCDF Time-Series

To streamline the rendering process, we download multiple `NetCDF` files
and then combine them into a single time-series `NetCDF` file. We also:

- ensure to convert SI Units to `μg/m3`
- calculate the data range
- discard non-populated time steps in the series

```bash
> cd data
> python unpack.py
> ls -l
> cd ..
```

This will create the `data/sulphur_dioxide_air_concentration.nc` file.


## Render: Explore Reykjanes Dataset

To interactively explore the `reykjanes` dataset simply:

```bash
> python -i reykjanes.py
```

> [!IMPORTANT]
> We require to execute `python` along with the `-i` flag (`inspect interactively`) as we are using [pyvistaqt](https://github.com/pyvista/pyvistaqt) to render the scene.


## Quick Start

Alternatively, to download, unpack, preprocess and render the Reykjanes dataset, simply:

```bash
> pixi run --frozen reykjanes
```
