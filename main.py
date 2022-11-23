import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
from utils.bookmark_gen import get_duration

from utils.extracti_video_frames import extract_frame_opencv, extract_frame_opencv_ffmpeg, time_format
from utils.porn_scorer import PornScorer


class CheesecaseCatcher:
    TYPE_OPENCV = 'type_opencv'
    TYPE_FFMPEG = 'type_ffmpeg'

    def __init__(self, video_path, extractor_type, scorer_type, interval=1) -> None:
        self.video_path = os.path.abspath(video_path)
        self.interval = interval
        self.extractor_type = extractor_type
        self.porn_scorer = PornScorer(scorer_type=scorer_type)

    def extract_frame_and_get_score(self):
        if self.extractor_type == CheesecaseCatcher.TYPE_OPENCV:
            self.extract_frame_and_get_score_opencv()
        elif self.extractor_type == CheesecaseCatcher.TYPE_FFMPEG:
            self.extract_frame_and_get_score_ffmpeg()
        else:
            raise UserWarning("extractor_type只能为[TYPE_OPENCV]或[TYPE_FFMPEG]其中之一！")

    def extract_frame_and_get_score_opencv(self):
        for (output_pic_dir, output_pic_path, task_count) in extract_frame_opencv(self.video_path, self.interval):
            self.porn_scorer.set_param(output_pic_dir, task_count)
            self.porn_scorer.submit_get_score_task(output_pic_path)
        self.porn_scorer.wait_finish()
        self.result_txt_path = self.porn_scorer.result_txt_path

    def extract_frame_and_get_score_ffmpeg(self):
        def process_pics(output_pic_dir):
            scan_left_times = 10
            while scan_left_times > 0:
                pic_names = [i for i in os.listdir(output_pic_dir) if re.match(r"^\d+$", os.path.splitext(i)[0])]
                for pic_name in pic_names:
                    (pic_id, pic_ext) = os.path.splitext(pic_name)
                    pic_path = os.path.join(output_pic_dir, pic_name)
                    try:
                        os.rename(pic_path, pic_path)
                    except:
                        continue
                    if pic_name == '00000001.jpg':
                        os.remove(pic_path)
                        continue
                    pic_renamed_path = os.path.join(output_pic_dir, f"{time_format(int(pic_id)-2)}{pic_ext}")
                    os.rename(pic_path, pic_renamed_path)
                    self.porn_scorer.submit_get_score_task(pic_renamed_path)
                    scan_left_times = 10
                scan_left_times -= 1
                time.sleep(1)
            print("结束图像监控...")

        executor = ThreadPoolExecutor(1)
        fs = []
        for (output_pic_dir, video_duration) in extract_frame_opencv_ffmpeg(self.video_path, 1/self.interval):
            print(f"获得图像输出目录：{output_pic_dir}")
            self.porn_scorer.set_param(output_pic_dir, int(video_duration/self.interval))
            fs.append(executor.submit(process_pics, output_pic_dir))
        wait(fs)
        self.porn_scorer.wait_finish()
        self.result_txt_path = self.porn_scorer.result_txt_path

    def sort_score_result(self):
        with open(self.result_txt_path, 'r', encoding='utf-8') as f:
            data = f.read().strip()
        with open(self.result_txt_path, 'w', encoding='utf-8') as f:
            f.write("")
        for row in sorted([i.split('\t') for i in data.split('\n')], key=lambda x: x[0]):
            with open(self.result_txt_path, 'a', encoding='utf-8') as f:
                f.write(f"{row[0]}\t{row[1]}\n")

    def run(self):
        print(f"[{datetime.now().strftime('%F %X')}] 开始处理：{self.video_path}")
        self.extract_frame_and_get_score()
        self.sort_score_result()


if __name__ == '__main__':
    data_dir = 'data'
    for i in os.listdir(data_dir):
        if os.path.splitext(i)[-1] == '.mp4':
            i_abs = os.path.join(os.path.abspath(data_dir), i)
            c = CheesecaseCatcher(i_abs, extractor_type=CheesecaseCatcher.TYPE_FFMPEG, scorer_type=PornScorer.TYPE_OFFLINE)
            c.run()
