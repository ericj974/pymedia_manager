# Media Manager

This is the main source code repository for my picture manager.

## Environment Installation

### Main Packages installation

1. Clone the repo (with submodules)
   ```bash
   git clone --recursive https://github.com/ericj974/media_manager.git
   ```
2. Setup the conda environment
   ```bash
   conda env create -f environment_3.yml
   ```

### pyheif lib

   ```bash
    sudo apt-get install -y libffi-dev libheif-dev libde265-dev
    conda activate media
    pip install pyheif
   ```
### Dlib lib for deepface

**Clone / compile / install dlib dependency**

***Install build tools***

```bash
   sudo apt-get install build-essential
   sudo snap install cmake --classic
```

***Build and setup dlib***

Steps coming from [this link](https://gist.github.com/ageitgey/629d75c1baac34dfa5ca2a1928a7aeaf?permalink_comment_id=3552228)

   ```bash
   git clone https://github.com/davisking/dlib.git
   cd dlib
   mkdir build; cd build; cmake ..; cmake --build .
   conda activate media
   cd ..
   python3 setup.py install 
   ```

## Setup the configuration File

The app will look first for `config.json` to run, and use by default `config_default.json` if not found.
You may wish to 
- create a config.json as a copy of `config_default.json`, and
- Specify an existing or a new location for the face_detection dataset (see DB_FOLDER in `config_default.json`)

## Run the app 

   ```bash
   conda activate media
   python main_app.py
   ```

## Usage

TBC

## License

This code is provided under a 3-clause BSD license that can be found in the
LICENSE file. By using, distributing, or contributing to this project, you agree
to the terms and conditions of this license.



