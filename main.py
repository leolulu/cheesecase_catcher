import os
import sys
from datetime import datetime

from utils.extracti_video_frames import extract_frame
from utils.porn_scorer import PornScorer


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
        print(f"[{datetime.now().strftime('%F %X')}] 开始处理：{self.video_path}")
        self.extract_frame_and_get_score()


if __name__ == '__main__':
    data_dir = 'data'
    for i in os.listdir(data_dir):
        c = CheesecaseCatcher(os.path.join(os.path.abspath(data_dir), i))
        c.run()
