import argparse
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
from queue import Empty, Queue

from tqdm import tqdm

from constants.score_threshold import SCORE_THRESHOLD
from data_structure.result_row import ResultRow
from utils.concat_video import concat_video
from utils.extract_video_frames import extract_frame_opencv, extract_frame_ffmpeg, time_format
from utils.porn_scorer import PornScorer
from utils.process_portion import get_different_intervals_at_once
from utils.score_visualization import prepare_score_for_visualization, save_bar_visualization


class CheesecaseCatcher:
    TYPE_OPENCV = 'type_opencv'
    TYPE_FFMPEG = 'type_ffmpeg'

    def __init__(
        self,
        video_path,
        extractor_type,
        scorer_type,
        interval,
        video_regeneration_with_copy,
        video_regeneration_coverage
    ) -> None:
        self.video_path = os.path.abspath(video_path)
        self.interval = interval
        self.video_regeneration_with_copy = video_regeneration_with_copy
        self.video_regeneration_coverage = video_regeneration_coverage
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
        def process_pics(output_pic_dir, queue: Queue):
            is_ffmpeg_processing = True
            while is_ffmpeg_processing:
                try:
                    queue.get(block=False)
                    is_ffmpeg_processing = False
                    print("结束图像监控...")
                except Empty:
                    pass
                time.sleep(1)
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

        executor = ThreadPoolExecutor(1)
        fs = []
        queue = Queue()
        for (output_pic_dir, video_duration) in extract_frame_ffmpeg(self.video_path, 1/self.interval):
            print(f"获得图像输出目录：{output_pic_dir}")
            self.output_pic_dir = output_pic_dir
            self.porn_scorer.set_param(output_pic_dir, int(video_duration/self.interval))
            fs.append(executor.submit(process_pics, output_pic_dir, queue))
        queue.put(False, block=False)
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
            score_filtered = score if float(score) >= SCORE_THRESHOLD else 0
            return ResultRow(img_path, timestamp, score, score_filtered)

        sorted_data = sorted([cut_row(i.split('\t')) for i in data.split('\n')], key=lambda x: x.timestamp)

        for rr in sorted_data:
            with open(self.result_txt_path, 'a', encoding='utf-8') as f:
                f.write(f"{rr.timestamp}\t{rr.score}\t{rr.score_filtered}\n")
        self.sorted_data = sorted_data

    def form_explicit_material(self):
        print("开始后处理结果图片和视频文件...")
        explicit_datas = [i for i in self.sorted_data if i.score >= SCORE_THRESHOLD]
        if len(explicit_datas) > 0:
            self.explicit_material_dir = os.path.join(self.output_pic_dir, 'explicit_material')
            self.explicit_material_pic_dir = os.path.join(self.explicit_material_dir, 'pic')
            if not os.path.exists(self.explicit_material_dir):
                os.mkdir(self.explicit_material_dir)
            if not os.path.exists(self.explicit_material_pic_dir):
                os.mkdir(self.explicit_material_pic_dir)
            for e_row in explicit_datas:
                shutil.copy(e_row.img_path, self.explicit_material_pic_dir)

            self.explicit_material_video_dirs = dict()
            for (coverage, intervals) in get_different_intervals_at_once([i.timestamp for i in explicit_datas], self.video_regeneration_coverage).items():
                self.explicit_material_video_dirs[coverage] = os.path.join(self.explicit_material_dir, f'video_coverage-{coverage}')
                if not os.path.exists(self.explicit_material_video_dirs[coverage]):
                    os.mkdir(self.explicit_material_video_dirs[coverage])
                for interval in tqdm(intervals, desc=f"抽取特定视频片段，当前coverage[{coverage}]"):
                    begin_second = interval.lower
                    end_second = interval.upper
                    output_vid_path = os.path.join(
                        self.explicit_material_video_dirs[coverage],
                        "{}-{}.mp4".format(time_format(begin_second), time_format(end_second))
                    )
                    log_path = os.path.abspath(os.path.join(self.explicit_material_video_dirs[coverage], "one_clip_explicit_video.log"))
                    if self.video_regeneration_with_copy:
                        command = f'ffmpeg -y -ss {begin_second} -to {end_second} -accurate_seek -i "{self.video_path}" -codec copy -map_chapters -1 -avoid_negative_ts 1 "{output_vid_path}" 2>>"{log_path}"'
                    else:
                        command = rf'ffmpeg -y -ss {begin_second} -to {end_second} -i "{self.video_path}" -vf "scale=w=min(1920\, iw):h=min(1080\, ih):force_original_aspect_ratio=decrease" -map_chapters -1 "{output_vid_path}" 2>>"{log_path}"'
                    subprocess.call(command, shell=True)
                concat_video(self.explicit_material_video_dirs[coverage])
        else:
            print("没有explicit的data，跳过后处理...")
        print("开始移动原始抽帧图像文件...")
        self.moved_frames_dir = os.path.join(self.output_pic_dir, 'org_frames')
        if not os.path.exists(self.moved_frames_dir):
            os.mkdir(self.moved_frames_dir)
        for row in self.sorted_data:
            shutil.move(row.img_path, self.moved_frames_dir)
            img_path_moved = os.path.join(self.moved_frames_dir, os.path.basename(row.img_path))
            row.img_path_moved = img_path_moved
        print("后处理完毕...")

    def gen_score_image_or_pdf(self):
        print("开始将打分结果生成可视化文件...")
        data = prepare_score_for_visualization(self.result_txt_path)
        save_bar_visualization(
            data,
            os.path.splitext(self.result_txt_path)[0]
        )

    def run(self):
        print(f"\n[{datetime.now().strftime('%F %X')}] 开始处理：{self.video_path}")
        self.extract_frame_and_get_score()
        self.sort_score_result()
        self.gen_score_image_or_pdf()
        self.form_explicit_material()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--data_dir', help='视频文件目录的路径，可以使用相对路径，默认为当前目录的data文件夹', default='data')
    parser.add_argument('-i', '--interval', help='抽帧间隔，即每几秒抽一帧，默认1秒一帧', default=1, type=int)
    parser.add_argument('-c', '--video_regeneration_with_copy', help='使用复制音视频流的方式进行视频片段的再生成，默认为False，需要进行再编码', action='store_true')
    parser.add_argument('-l', '--video_regeneration_coverage', help='进行视频片段划分的黏性阈值，默认为5秒', default=5, type=int)
    args = parser.parse_args()
    import tensorflow.compat.v1  # type: ignore
    for (dir_, _, file_) in os.walk(os.path.abspath(args.data_dir)):
        for v_path in [os.path.join(dir_, f) for f in file_]:
            if (os.path.splitext(v_path)[-1] in ['.mp4', '.mkv', '.avi', '.flv']) and ('explicit_material' not in v_path):
                try:
                    os.rename(v_path, v_path)
                except:
                    continue
                c = CheesecaseCatcher(
                    v_path,
                    extractor_type=CheesecaseCatcher.TYPE_FFMPEG,
                    scorer_type=PornScorer.TYPE_OFFLINE,
                    interval=args.interval,
                    video_regeneration_with_copy=args.video_regeneration_with_copy,
                    video_regeneration_coverage=args.video_regeneration_coverage
                )
                c.run()
