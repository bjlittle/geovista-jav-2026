# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

from __future__ import annotations

from pathlib import Path

import iris

from geojav import CACHE


def main() -> None:
    iris.FUTURE.save_split_attrs = True
    iris.FUTURE.date_microseconds = True

    if Path("sulphur_dioxide_air_concentration.nc").exists():
        print("\nReykjanes time-series NetCDF file already exists, skipping ...\n")
        return

    print("\nFetching assets ...\n")

    # fetch all the reykjanes assets in the registry
    for asset in CACHE.registry_files:
        if asset.startswith("reykjanes"):
            CACHE.fetch(asset)

    # load the so2 dataset
    name = "SULPHUR_DIOXIDE_AIR_CONCENTRATION"

    print(f"\nLoading {' '.join(part.capitalize() for part in name.split('_'))} ...\n")
    cube = iris.load_cube(CACHE.abspath / "reykjanes" / "*.nc", name)
    print(cube)

    if cube.units != (target := "μg/m^3"):
        print(f"\nConverting units {str(cube.units)!r} -> {target!r} ...")
        cube.convert_units(target)

    # calculate the data range for each time step
    print("\nCalculating data range for each time step ...\n")
    dmin, dmax = None, None
    tsteps = []
    for i, scube in enumerate(cube.slices_over("time")):
        data = scube.data
        min, max = data.min(), data.max()
        if dmin is None or min < dmin:
            dmin = min
        if dmax is None or max > dmax:
            dmax = max
        if data.sum():
            tsteps.append(i)

    dmin, dmax = float(dmin), float(dmax)
    print(f"\t{dmin=}, {dmax=}")

    # discard time steps with no data
    print("\nDiscarding time steps with no data ...\n")
    slicer = [slice(None)] * cube.ndim
    slicer[cube.coord_dims("time")[0]] = tsteps
    cube = cube[tuple(slicer)]
    print(cube)

    # serialize to a netcdf file
    print(f'\nSaving to NetCDF ...\n')
    fname = f"{cube.name().lower()}.nc"
    iris.save(cube, fname)
    print(f"\tCreated {fname!r}\n")
    print("Done 👍")


if __name__ == "__main__":
    main()
