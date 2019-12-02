import argparse
import json
import math
import random
from collections import namedtuple
from enum import Enum
from typing import *
from datetime import datetime

import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic

Pair = namedtuple("Pair", ["start", "end"])


class TrackSegment:
    def __init__(self, segment, activity_sampling_rate: int, start_of_tracking: int,
                 end_of_tracking: int):
        self.points: List[TrackPoint] = []

        for point in segment.points:
            self.points.append(TrackPoint(point))

        self.interval: Pair = Pair(start_of_tracking, end_of_tracking)
        self.mean_velocity: float = Helpers.mean_velocity(self.points, self.interval)
        self.activity: ActivityType = ActivityType.from_mean_velocity(self.mean_velocity)
        self.activity_sampling_rate: int = activity_sampling_rate

        self.generate_point_times()
        self.remove_duplicate_time_points()
        self.generate_activities()

    def generate_point_times(self):
        self.points[0].time = self.interval.start
        self.points[-1].time = self.interval.end

        for i in range(0, len(self.points) - 2):
            time_diff = Helpers.time_diff(
                self.points[i], self.points[i + 1], self.mean_velocity)
            self.points[i + 1].time = self.points[i].time + time_diff

    def remove_duplicate_time_points(self):
        unique_time_points = {}
        for point in self.points:
            unique_time_points[point.time] = point
        self.points = list(unique_time_points.values())

    def generate_activities(self):
        for i in range(0, len(self.points) - 2):
            time_diff = self.points[i + 1].time - self.points[i].time
            if time_diff > self.activity_sampling_rate:
                for j in range(0, math.floor(time_diff / self.activity_sampling_rate)):
                    self.points[i].activities.append(
                        Activity(self.activity, self.points[i].time + self.activity_sampling_rate * j))

    def to_json(self):
        return self.points


class TrackPoint:
    def __init__(self, point):
        self.lon: float = point.longitude
        self.lat: float = point.latitude
        self.ele: float = point.elevation
        # self.time = datetime.strptime(point.time[:-3], '%Y-%m-%d %H:%M:%S.%f')
        self.time: int = 0
        self.activities: List[Activity] = []

    def to_json(self):
        return {'timestampMs': Helpers.export_time(self.time), 'latitudeE7': int(self.lat * 10 ** 7),
                'longitudeE7': int(self.lon * 10 ** 7),
                'accuracy': 80,
                'activity': self.activities}


class ActivityType(Enum):
    IN_VEHICLE = 'IN_VEHICLE'  # The device is in a vehicle, such as a car.
    ON_BICYCLE = 'ON_BICYCLE'  # The device is on a bicycle.
    RUNNING = 'RUNNING'  # The device is on a user who is running.
    STILL = 'STILL'  # The device is still (not moving).
    WALKING = 'WALKING'  # The device is on a user who is walking.

    def __init__(self, activity: int):
        self.activity: int = activity

    @staticmethod
    def from_mean_velocity(mean_velocity: float):
        if mean_velocity < 0:
            raise Exception()
        elif mean_velocity == 0:
            return ActivityType.STILL
        elif 0 <= mean_velocity < 5000 / 3600:
            return ActivityType.WALKING
        elif 5000 / 3600 <= mean_velocity < 15000 / 3600:
            return ActivityType.RUNNING
        elif 15000 / 3600 <= mean_velocity < 25000 / 3600:
            return ActivityType.RUNNING
        else:
            return ActivityType.IN_VEHICLE

    def to_json(self):
        return {'type': self.activity, 'confidence': 50}


class Activity:
    def __init__(self, activity_type: ActivityType, time: int):
        self.time = time
        self.activity_type = activity_type

    def to_json(self):
        return {'timestampMs': Helpers.export_time(self.time), 'activity': [self.activity_type]}


class Helpers:
    @staticmethod
    def distance_sum(points: List[TrackPoint]) -> int:
        d = 0
        for i in range(0, len(points) - 2):
            d += Helpers.distance(points[i], points[i + 1])
        return d

    @staticmethod
    def distance(point1: TrackPoint, point2: TrackPoint) -> int:
        return geodesic((point1.lat, point1.lon), (point2.lat, point2.lon)).meters

    @staticmethod
    def time_diff(point1: TrackPoint, point2: TrackPoint, mean_velocity: float) -> int:
        return int(Helpers.distance(point1, point2) / mean_velocity)

    @staticmethod
    def mean_velocity(points: List[TrackPoint], interval: Pair) -> float:
        return Helpers.distance_sum(points) / (interval.end - interval.start)

    @staticmethod
    def overlap(interval1: Pair, interval2: Pair) -> bool:
        return interval1.start <= interval2.end and interval2.start <= interval1.end

    @staticmethod
    def segment_overlap(segments: List[TrackSegment]) -> bool:
        for s1 in segments:
            for s2 in segments:
                if s1 != s2 and Helpers.overlap(s1.interval, s2.interval):
                    return True
        return False

    @staticmethod
    def export_time(time: int) -> str:
        return "{}{}".format(time, random.randrange(999))

    @staticmethod
    def import_time(time: str) -> int:
        return int(datetime.strptime(time, '%Y-%m-%d %H:%M:%S').timestamp())


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_json'):
            return obj.to_json()
        else:
            return json.JSONEncoder.default(self, obj)


def load_data(filename: str) -> List[TrackSegment]:
    segments = []

    with open(filename, 'r') as fp:
        json_file = json.load(fp)
        for entry in json_file['input']:
            gpx_file = open(entry['filename'], 'r')
            gpx = gpxpy.parse(gpx_file)

            for track in gpx.tracks:
                for segment in track.segments:
                    segments.append(TrackSegment(
                        segment,
                        int(entry['activitySamplingRate']),
                        Helpers.import_time(entry['startOfTracking']),
                        Helpers.import_time(entry['endOfTracking']))
                    )

    return segments


def export_data(filename: str, points: List[TrackPoint]):
    exported_data = {'locations': points}
    with open(filename, 'w') as fp:
        json.dump(exported_data, fp, cls=ComplexEncoder)


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='Convert a GPX file to LocationHistory.json file.')
    parser.add_argument('--input', dest='inputfile', type=str,
                        required=True, help='Input GPX file')
    parser.add_argument('--output', dest='outputfile', type=str,
                        default='LocationHistory.json', help='Output JSON file')
    args = parser.parse_args()

    segments = load_data(args.inputfile)
    Helpers.segment_overlap(segments)
    merged_points = [p for s in segments for p in s.points]
    export_data(args.outputfile, merged_points)


if __name__ == '__main__':
    main()
