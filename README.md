# UltimateLabeling

[![Build Status](https://travis-ci.com/alexandre01/UltimateLabeling.svg?branch=master)](https://travis-ci.com/alexandre01/UltimateLabeling)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/pyversions/ultimatelabeling.svg)](https://pypi.python.org/pypi/ultimatelabeling)
[![PyPI](https://img.shields.io/pypi/v/ultimatelabeling.svg)](https://pypi.python.org/pypi/ultimatelabeling) 

A multi-purpose Video Labeling GUI in Python with integrated SOTA detector and tracker. Developed using PyQt5.

**[Under development]**

The integrated object detectors and trackers are based on the following codes:
- [OpenPifPaf](https://github.com/vita-epfl/openpifpaf): for human pose estimation
- [YOLO darknet](https://github.com/AlexeyAB/darknet): for object detection
- [SiamMask](https://github.com/foolwood/SiamMask): for visual object tracking
- [Hungarian algorithm (scipy.optimize)](https://github.com/scipy/scipy): for optimal instance ID assignment

For remote server processing, follow the guide below in order to configure the [server files](https://github.com/alexandre01/UltimateLabeling_server).


## Demo 
![screenshot](docs/ultimatelabeling.jpg)

![uptown_funk](docs/uptown_funk.jpg)

![roundabout](docs/roundabout.jpg)


## Features
- SSH connection to the remote server (see below to configure the server)
- YOLO and OpenPifPaf integrated object & pose detectors (single frame and entire video mode)
- Hungarian instance ID assignment
- SiamMask Visual object tracking for missing or mislabeled objects
- Zoom on the video, resizable bounding boxes and skeletons
- Dark mode!


## Installation

Install the requirements using `pip` as follows:

```
pip install -r requirements
```

Put the videos (folder of images or video file, the frames will be extracted automatically) inside the `data` folder. Then, open the GUI using 

```sh
python -m ultimatelabeling.main
```

After closing the window, the annotations are available in the `output` folder.


## Remote server configuration
To configure the remote GPU server, follow the steps below:

```sh
git clone https://github.com/alexandre01/UltimateLabeling_server.git
cd UltimateLabeling_server
pip install -r requirements.txt
bash siamMask/setup.sh
bash detection/setup.sh
```

The data images and videos should be placed in the folder `data`, similarly to the client code.

To extract video files, use the following script:

```sh
bash extract.sh data/video_file.mp4
```


## Licence
Copyright (c) 2019 Alexandre Carlier, released under the MIT licence.
