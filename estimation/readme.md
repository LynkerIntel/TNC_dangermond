# Setup ngen
This step can be skipped if ngen is already setup and the python virtual environment used by ngen is active.

## Setup a python virtual environment

```sh
python3 -m venv venv
source venv/bin/activate
```

## Setup t-route

```sh
git clone https://github.com/noaa-owp/t-route
cd t-route
pip install "numpy<2.0"
pip install -r requirements.txt
NETCDF=$(brew --prefix netcdf-fortran)/include \
LIBRARY_PATH=$(brew --prefix gcc)/lib/gcc/current/:$(brew --prefix)/lib:$LIBRARY_PATH \
./compiler.sh no-e
cd ..
```

## Build ngen
 May need to change relevant features enabled in the cmake configuration
```sh

git clone https://github.com/noaa-owp/ngen
cd ngen
```

Build submodules and formulation modules

```sh
git submodule update --init --recursive -- test/googletest
git submodule update --init --recursive -- extern/pybind11
git submodule update --init --recursive -- extern/cfe
sed -i '' 's/CFE_DEBUG 1/CFE_DEBUG 0/g' extern/cfe/cfe/src/bmi_cfe.c
git submodule update --init --recursive -- extern/noah-owp-modular/noah-owp-modular
git submodule update --init --recursive -- extern/bmi-cxx
git submodule update --init --recursive -- extern/sloth
git submodule update --init --recursive -- extern/evapotranspiration/
cmake -B extern/cfe/cmake_build -S extern/cfe/cfe/ -DNGEN=ON
make -C extern/cfe/cmake_build 
cmake -B extern/noah-owp-modular/cmake_build -S extern/noah-owp-modular -DNGEN_IS_MAIN_PROJECT=ON
make -C extern/noah-owp-modular/cmake_build
cmake -B extern/sloth/cmake_build -S extern/sloth
make -C extern/sloth/cmake_build
cmake -B extern/evapotranspiration/cmake_build -S extern/evapotranspiration/evapotranspiration/
make -C extern/evapotranspiration/cmake_build
```

## Build ngen with features needed

```sh
cd ../ngen
cmake -B cmake_build -S . \
-DNGEN_WITH_PYTHON:BOOL=ON \
-DNGEN_WITH_BMI_C:=ON \
-DNGEN_WITH_BMI_FORTRAN:BOOL=ON \
-DUDUNITS_QUIET:BOOL=ON \
-DNGEN_WITH_NETCDF:=ON \
-DNGEN_WITH_SQLITE:=ON \
-DNGEN_WITH_ROUTING:=ON \
-DNGEN_UPDATE_GIT_SUBMODULES:=OFF \
-DNGEN_WITH_EXTERN_TOPMODEL:=OFF \
-DNGEN_WITH_MPI:=OFF

make -j 8 -C cmake_build
cd ..
```

# Generating forcing data for Dangermond Hydrofabric

Create a new venv or use the ngen venv.

## Get hydrofabric

```sh
unzip tnc_hf.zip
```

## Get the AORC forcing processing code

```sh
git clone https://github.com/jmframe/CIROH_DL_NextGen
pip install -r CIROH_DL_NextGen/forcing_prep/requirements.txt
```

Note: needs PR#9 to use local geopackage and to produce netcdf outputs

## Run the processor

```sh
python CIROH_DL_NextGen/forcing_prep/generate.py forcing.yaml
```

# Generating init configs

```sh
pip install 'git+https://github.com/noaa-owp/ngen-cal@master#egg=ngen_config_gen&subdirectory=python/ngen_config_gen'
```

Quick fix of attribute names...

```sh
python fix_attribute_names.py
```

Then generate the init configs

```sh
python gen_init_config.py
```

Turn off PET verbose setting

```sh
sed -i '' 's/verbose=1/verbose=0/g' config/PET*
```

# Setting up calibration

These directions will evolve and will probably point to a custom fork/branch as certain features for this specific application are developed...

```sh
git clone https://github.com/noaa-owp/ngen-cal
pip install -e ngen-cal/python/ngen_cal/
```

# Notes

Streamflow is compared/optmized using natrualized stream flows at a montly time scale (found in `tnc_hf/model_flows.parquet`).  These flow values are in units of ft^3/sec (CFS).