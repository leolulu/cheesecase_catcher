import os
import sys
from utils.porn_scorer import PornScorer
from utils.extracti_video_frames import extract_frame


class CheesecaseCatcher:
    def __init__(self, video_path, interval=1) -> None:
        self.video_path = os.path.abspath(video_path)
        self.interval = interval
        self.porn_scorer = PornScorer()

    def extract_frame_and_get_score(self):
        for (output_pic_dir, output_pic_path, task_count) in extract_frame(self.video_path, self.interval):
            self.porn_scorer.set_param(output_pic_dir, task_count)
            self.porn_scorer.submit_get_score_task(output_pic_path)
        self.porn_scorer.wait_finish()
        self.result_txt_path = self.porn_scorer.result_txt_path

    def run(self):
        print(f"开始处理：{self.video_path}")
        self.extract_frame_and_get_score()


if __name__ == '__main__':
    for i in os.listdir('data'):
        c = CheesecaseCatcher(i)
        c.run()
