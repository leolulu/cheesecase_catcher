import portion as P
from portion.interval import Interval


class ExplicitPortion:
    def __init__(self, coverage=2) -> None:
        self.p = P.empty()
        self.coverage = coverage

    def add_timestamp_portion(self, timestamp: str):
        self.p = self.p | self.timestamp_to_interval(timestamp)

    def add_portion(self, interval: Interval):
        self.p = self.p | interval

    def timestamp_to_interval(self, timestamp: str) -> Interval:
        hour, minute, second = timestamp.split("_")
        seconds = sum([
            int(hour)*3600,
            int(minute)*60,
            int(second)
        ])
        return P.closed(seconds-self.coverage, seconds+self.coverage)

    def get_p(self):
        return self.p & P.closed(0, P.inf)


def get_diffrent_intervals_at_once(timestamps, max_coverage):
    intervals = dict()
    for coverage_ in range(max_coverage):
        coverage = coverage_ + 1
        ep = ExplicitPortion(coverage)
        for timestamp in timestamps:
            ep.add_timestamp_portion(timestamp)
        intervals[coverage] = ep.get_p()
    return intervals


if __name__ == '__main__':
    ep = ExplicitPortion(coverage=8)
    with open(r"C:\Dpan\python-script\cheesecase_catcher\data\$RKSTDQB\porn_score_result.txt", 'r', encoding='utf-8') as f:
        data = f.read().strip().split('\n')
    for row in [i.split('\t') for i in data]:
        timestamp = row[0]
        score = float(row[1])
        if score >= 80:
            ep.add_timestamp_portion(timestamp)
    print(ep.get_p(),ep.p)
