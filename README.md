# Location history generator

A simple script for generating LocationHistory.json formatted files from .gpx files.
It takes as input a .json file with list of .gpx files (containing track segments) and for every track segment
the beginning and the end of the segment (so any time points inside the .gpx files are ignored).
It generates the device's activity based on the average velocity it needs to cover the segment
in the provided time interval. Please note that each path has only one activity associated to it.

## Caution

Your .gpx data MUST be in this format:
```xml
    <trk>
        <trkseg>
            <trkpt lat="37.97395220376875" lon="24.00837198011452"></trkpt>
            <trkpt lat="37.97463885994126" lon="24.00835927867174"></trkpt>
            <trkpt lat="37.97463885994126" lon="24.00835927867174"></trkpt>
        <trkseg>
    </trk>
```
Please take a closer look at the samples folder before running.

## Installation of dependencies

Use the package manager [pip](https://pip.pypa.io/en/stable/).

```bash
    pip install -r /path/to/requirements.txt
```

## Recommended usage

The easiest way of using the tool is:
1. Draw a PATH on Google Earth.
2. Export it to .kml .
3. Convert it to .gpx with this online [tool](https://kml2gpx.com/). Make sure you check only the Tracks checkbox.
4. Repeat 1-3 multiple times if needed, for generating different PATHs.
5. Create your input.json file following the samples.
6. `python location_history_generator.py --input input.json`
7. Make sure your data were generated successfully using these tools [1](https://locationhistoryvisualizer.com/heatmap/), [2](http://theyhaveyour.info/).


## Usage

```bash
    python location_history_generator.py --input input.json
```

## Screenshots

![Alt text](/screenshots/screenshot1.png)
![Alt text](/screenshots/screenshot2.png)


## License
[MIT](https://choosealicense.com/licenses/mit/)
