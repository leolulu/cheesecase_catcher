import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime

from tqdm import tqdm

from data_structure.result_row import ResultRow
from utils.concat_video import concat_video
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
            self.output_pic_dir = output_pic_dir
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
            self.output_pic_dir = output_pic_dir
            self.porn_scorer.set_param(output_pic_dir, int(video_duration/self.interval))
            fs.append(executor.submit(process_pics, output_pic_dir))
        wait(fs)
        self.porn_scorer.wait_finish()
        self.result_txt_path = self.porn_scorer.result_txt_path

    def sort_score_result(self):
        print("重新排列结果顺序，重写文件...")
        with open(self.result_txt_path, 'r', encoding='utf-8') as f:
            data = f.read().strip()
        with open(self.result_txt_path, 'w', encoding='utf-8') as f:
            f.write("")

        def cut_row(row):
            img_path = row[0]
            timestamp = os.path.splitext(os.path.basename(img_path))[0]
            score = row[1]
            score_80_filterd = score if float(score) >= 80 else 0
            return ResultRow(img_path, timestamp, score, score_80_filterd)

        sorted_data = sorted([cut_row(i.split('\t')) for i in data.split('\n')], key=lambda x: x.timestamp)

        for rr in sorted_data:
            with open(self.result_txt_path, 'a', encoding='utf-8') as f:
                f.write(f"{rr.timestamp}\t{rr.score}\t{rr.score_80_filterd}\n")
        self.sorted_data = sorted_data

    def form_explicit_material(self):
        print("开始后处理结果图片和视频文件...")
        self.explicit_material_dir = os.path.join(self.output_pic_dir, 'explicit_material')
        self.explicit_material_pic_dir = os.path.join(self.explicit_material_dir, 'pic')
        self.explicit_material_video_dir = os.path.join(self.explicit_material_dir, 'video')
        if not os.path.exists(self.explicit_material_dir):
            os.mkdir(self.explicit_material_dir)
        if not os.path.exists(self.explicit_material_pic_dir):
            os.mkdir(self.explicit_material_pic_dir)
        if not os.path.exists(self.explicit_material_video_dir):
            os.mkdir(self.explicit_material_video_dir)
        for e_row in tqdm([i for i in self.sorted_data if i.score >= 80], desc="explicit后处理"):
            shutil.copy(e_row.img_path, self.explicit_material_pic_dir)
            output_vid_path = os.path.join(self.explicit_material_video_dir, f"{e_row.timestamp}.mp4")
            log_path = os.path.abspath(os.path.join(self.explicit_material_video_dir, "one_clip_explicit_video.log"))
            command = f'ffmpeg -y -ss {e_row.ffmpeg_timestamp} -t {self.interval} -i "{self.video_path}" "{output_vid_path}" 2>>"{log_path}"'
            subprocess.call(command, shell=True)
        concat_video(self.explicit_material_video_dir)
        print("后处理完毕...")

    def run(self):
        print(f"\n[{datetime.now().strftime('%F %X')}] 开始处理：{self.video_path}")
        self.extract_frame_and_get_score()
        self.sort_score_result()
        self.form_explicit_material()


if __name__ == '__main__':
    data_dir = 'data'
    for (dir_, _, file_) in os.walk(os.path.abspath(data_dir)):
        for v_path in [os.path.join(dir_, f) for f in file_]:
            if (os.path.splitext(v_path)[-1] in ['.mp4', '.mkv', '.avi']) and ('explicit_material' not in v_path):
                try:
                    os.rename(v_path, v_path)
                except:
                    continue
                c = CheesecaseCatcher(v_path, extractor_type=CheesecaseCatcher.TYPE_FFMPEG, scorer_type=PornScorer.TYPE_OFFLINE)
                c.run()
