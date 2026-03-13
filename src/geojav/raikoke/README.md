# Raikoke (Russia)

> [!NOTE]
> Please ensure that the `geojav` environment is activated.

We require to download the `raikoke` dataset for preprocessing prior to rendering.

From the `geovista-jav-2026` base directory change to the `raikoke` directory:

```bash
> cd src/geojav/raikoke
```

## Convert QVA to NetCDF

To streamline the rendering process, we download and unpack a tarball of multiple `QVA` files
and then combine them into a single `NetCDF` file. We also:

- ensure to convert SI Units to `mg/m3`
- calculate the data range
- discard non-populated time steps in the series

```bash
> cd data
> python unpack.py
> ls -l
> cd ..
```

This will create the `data/volcanic_ash_air_concentration.nc` file.

## Explore Raikoke Dataset

To interactively explore the `raikoke` dataset simply:

```bash
> python -i raikoke.py
```

> [!IMPORTANT]
> We require to execute `python` along with the `-i` flag (`inspect interactively`) as we are using [pyvistaqt](https://github.com/pyvista/pyvistaqt) to render the scene.

![Raikoke](images/raikoke.png)
