import sys
from utils.porn_scorer import PornScorer
from utils.extracti_video_frames import extract_frame


class CheesecaseCatcher:
    def __init__(self, video_path, interval=1) -> None:
        self.video_path = video_path
        self.interval = interval
        self.porn_scorer = PornScorer()

    def extract_frame_and_get_score(self):
        for (output_pic_dir, output_pic_path) in extract_frame(self.video_path, self.interval):
            self.porn_scorer.set_result_txt_path(output_pic_dir)
            self.porn_scorer.submit_get_score_task(output_pic_path)
        self.porn_scorer.wait_finish()
        self.result_txt_path = self.porn_scorer.result_txt_path

    def run(self):
        self.extract_frame_and_get_score()


if __name__ == '__main__':
    video_path = sys.argv[1]
    c = CheesecaseCatcher(video_path)
    c.run()
