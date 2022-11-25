class ResultRow:
    def __init__(self, img_path, timestamp, score, score_80_filterd) -> None:
        self.img_path = img_path
        self.timestamp = timestamp
        self.score = float(score)
        self.score_80_filterd = float(score_80_filterd)
        self.timestamp2ffmpeg()
        self.img_path_moved = ''

    def timestamp2ffmpeg(self):
        self.ffmpeg_timestamp = str(self.timestamp).replace("_", ":")
