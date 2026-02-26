# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

from __future__ import annotations

import tarfile

import iris


fname = "QVA_grid1.tar.gz"
iris.FUTURE.save_split_attrs = True

print("\nExtracting QVA files from tarball ...\n")

with tarfile.open(fname, "r:gz") as tar:
    tar.extractall(filter="data")

print("\nLoading QVA files ...\n")

# load the QVA timeseries data from the NAME model
cube = iris.load_cube("QVA_grid1_*.txt")
print(cube)

if cube.units == "g/m3":
    tunits = "mg/m3"
    print(f"\nConverting units {str(cube.units)} -> {tunits} ... ")
    cube.convert_units(tunits)

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

# serialize to a netcdf file (compressed)
print("\nSaving QVA to NetCDF ...\n")
fname = f"{cube.name().lower()}.nc"
iris.save(cube, fname, complevel=9, zlib=True)
print(f"\tCreated {fname!r}\n")
print("Done 👍")
