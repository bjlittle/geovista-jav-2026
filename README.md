<p align="center">
  <a href="https://geovista.readthedocs.io/en/latest/">
    <img src="https://raw.githubusercontent.com/bjlittle/geovista-media/2026.02.4/media/branding/logo/logomark/geovistalogoicon.svg"
         alt="GeoVista Logo"
         width="250"></a>
</p>

<p align="center">
  <a href="https://geovista.readthedocs.io/en/latest/">
    <img src="https://raw.githubusercontent.com/bjlittle/geovista-media/2026.02.0/media/branding/title/geovista-title.svg"
         alt="GeoVista"
         width="300"></a>
</p>

<h3 align="center">
  Cartographic rendering and mesh analytics powered by <a href="https://docs.pyvista.org/index.html">PyVista</a>
</h3>


----

<p align="center">🚧 Under construction 🚧</p>

|              |   |
|--------------|---|
| ⚙️ CI         | [![ci-locks](https://github.com/bjlittle/geovista-jav-2026/actions/workflows/ci-locks.yml/badge.svg)](https://github.com/bjlittle/geovista-jav-2026/actions/workflows/ci-locks.yml) [![ci-manifest](https://github.com/bjlittle/geovista-jav-2026/actions/workflows/ci-manifest.yml/badge.svg)](https://github.com/bjlittle/geovista-jav-2026/actions/workflows/ci-manifest.yml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bjlittle/geovista-jav-2026/main.svg)](https://results.pre-commit.ci/latest/github/bjlittle/geovista-jav-2026/main)  |
| 💬 Community  | [![Contributor Covenant](https://img.shields.io/badge/contributor%20covenant-2.1-4baaaa.svg)](https://github.com/bjlittle/geovista-jav-2026/blob/main/CODE_OF_CONDUCT.md) [![GH Discussions](https://img.shields.io/badge/github-discussions%20%F0%9F%92%AC-yellow?logo=github&logoColor=lightgrey)](https://github.com/bjlittle/geovista-jav-2026/discussions) |
| ✨ Meta       | [![GeoVista Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/bjlittle/geovista/main/docs/assets/badge/v0.json)](https://geovista.readthedocs.io/en/latest/) [![Pixi Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.prefix.dev) [![license - bsd-3-clause](https://img.shields.io/github/license/bjlittle/geovista-jav-2026)](https://github.com/bjlittle/geovista-jav-2026/blob/main/LICENSE) |
| 🧰 Repo       | [![commits-since](https://img.shields.io/github/commits-since/bjlittle/geovista-jav-2026/latest.svg)](https://github.com/bjlittle/geovista-jav-2026/commits/main) [![contributors](https://img.shields.io/github/contributors/bjlittle/geovista-jav-2026)](https://github.com/bjlittle/geovista-jav-2026/graphs/contributors) [![release](https://img.shields.io/github/v/release/bjlittle/geovista-jav-2026)](https://github.com/bjlittle/geovista-jav-2026/releases) |
|              |   |

[🎥 Reykjanes Time-Series](https://github.com/user-attachments/assets/7df2ee95-11db-4479-9cfe-a1a524aefa37)

Submission to the [Data Visualization and Effective Communication in Volcanology: Cross-disciplinary Lessons from Research and Practice](https://link.springer.com/collections/cgaadbacjg) collection in the [Journal of Applied Volcanology](https://link.springer.com/journal/13617).


# Install

 Please follow these steps to install the `geojav` package.

## Clone the Repository

Make a local clone of the `geovista-jav-2026` repository:

```bash
> git clone https://github.com/bjlittle/geovista-jav-2026
> cd geovista-jav-2026
```

## Create the Environment

Create an environment to install `geojav` and all its required dependencies.

### `pixi`

We recommend using [pixi](https://github.com/prefix-dev/pixi) for package management.

Simply:

```bash
> pixi shell --environment geojav
```

Alternatively, install [direnv](https://direnv.net/) to *activate*/*deactivate*
the `geojav` environment *automatically* whenever you enter/leave the `geovista-jav-2026`
directory:

```bash
> pixi global install direnv
> direnv allow
```

> [!TIP]
> For information about the system, workspace and available `pixi` environments:
>
> ```bash
> > pixi info
> ```


### `conda`

Simply:

```bash
> conda env create --file requirements/geojav.yml
> conda activate geojav
```

> [!TIP]
> Alternatively, for `linux` users only, install the fully resolved `geojav` environment:
>
> ```bash
> > conda env create --file requirements/locks/geojav_linux-64_conda_spec.yml
> > conda activate geojav


### `pip`

Simply:

```bash
> pip install .
> pip install git+https://github.com/bjlittle/geovista.git@main
```

> [!WARNING]
> The PyPI package [scitools-iris](https://pypi.org/project/scitools-iris/) has a dependency on
> [cf-units](https://pypi.org/project/cf-units/) which in turn requires the Unidata
> [UDUNITS-2](https://docs.unidata.ucar.edu/udunits/current/) package (C based library) for units
> of physical quantities to be available.
>
> The `UDUNITS-2` package is not `pip` installable.
>


# Explore

If you wish to interactvely explore either of the **Raikoke** and **Reykjanes** datasets, then please click either of the images below for further instructions.


## Raikoke (Russia)

<p align="center">
  <a href="https://github.com/bjlittle/geovista-jav-2026/blob/main/src/geojav/raikoke/README.md">
    <img src="https://raw.githubusercontent.com/bjlittle/geovista-data-jav-2026/2026.03.3/assets/media/raikoke.png"
         alt="Raikoke Plume"
         style="width: 75%; height: 75%"></a>
</p>


## Reykjanes (Iceland)

<p align="center">
  <a href="https://github.com/bjlittle/geovista-jav-2026/blob/main/src/geojav/reykjanes/README.md">
    <img src="https://raw.githubusercontent.com/bjlittle/geovista-data-jav-2026/2026.03.3/assets/media/reykjanes.png"
         alt="Reykjanes Plume Isosurface"
         style="width: 75%; height: 75%"></a>
</p>


# [#ShowYourStripes](https://showyourstripes.info/s/globe)

<h4 align="center">
  <a href="https://showyourstripes.info/s/globe">
    <img src="https://raw.githubusercontent.com/ed-hawkins/show-your-stripes/master/2022/GLOBE---1850-2022-MO.png"
         height="50" width="800"
         alt="#showyourstripes Global 1850-2022"></a>
</h4>

**Graphics and Lead Scientist**: [Ed Hawkins](http://www.met.reading.ac.uk/~ed/home/index.php), National Centre for Atmospheric Science, University of Reading.

**Data**: Berkeley Earth, NOAA, UK Met Office, MeteoSwiss, DWD, SMHI, UoR, Meteo France & ZAMG.

<p>
<a href="https://showyourstripes.info/s/globe">#ShowYourStripes</a> is distributed under a
<a href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>
<a href="https://creativecommons.org/licenses/by/4.0/">
  <img src="https://i.creativecommons.org/l/by/4.0/80x15.png"
       alt="creative-commons-by" style="border-width:0">
</a>
</p>
