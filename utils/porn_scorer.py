import json
import os
from concurrent.futures import ThreadPoolExecutor, wait
import traceback
import time

import requests
from retrying import retry
from tqdm import tqdm


class PornScorer:
    def __init__(self, core_num=10) -> None:
        self.result_txt_path = None
        self.executor = ThreadPoolExecutor(core_num)
        self.futures = []
        self.b_time = time.time()

    def set_param(self, output_pic_dir, task_count):
        if self.result_txt_path is None:
            self.result_txt_path = os.path.join(output_pic_dir, 'porn_score_result.txt')
            self.pbar = tqdm(total=task_count, desc="打分")

    def submit_get_score_task(self, output_pic_path):
        def get_porn_score_with_txt(img_path):
            try:
                _, _, score = PornScorer.get_porn_score(img_path)
                with open(self.result_txt_path, 'a', encoding='utf-8') as f:  # type: ignore
                    f.write(f"{os.path.splitext(os.path.basename(img_path))[0]}\t{score}\n")
                self.pbar.update()
            except:
                print(traceback.format_exc())
        self.futures.append(self.executor.submit(get_porn_score_with_txt, output_pic_path))

    def wait_finish(self):
        wait(self.futures)
        self.pbar.close()
        print("打分处理完毕...")

    @staticmethod
    @retry(wait_fixed=2000, stop_max_delay=60000)
    def get_porn_score(img_path):
        try:
            url = 'https://ai.hn-ssc.com/api/v1/image/get_vision_porn/'
            img_path = os.path.abspath(img_path)
            img_name = os.path.basename(img_path)
            with open(img_path, 'rb') as f:
                data = f.read()
            files = {
                'image': (img_name, data),
                'system_id': (None, 1),
                'channel_id': (None, 3)
            }
            r = requests.post(url, files=files)
            result = json.loads(r.content)
            info = json.loads(r.content)['data']
            score = info['normal_hot_porn']
            return result, info, score
        except Exception as e:
            print("打分失败了！！！")
            print(e)
            print(r, r.content)  # type: ignore
            print("开始重试！！！")
            raise e


# if __name__ == '__main__':
#     os.chdir(r"C:\Dpan\python-script\cheesecase_catcher\data\More-Telegram@HTHUB_srted_ccd")
#     executor = ThreadPoolExecutor(10)

#     def score_file(i):
#         print(f'begin:{i}')
#         _, _, score = get_porn_score(i)
#         with open('result.txt', 'a', encoding='utf-8') as f:
#             f.write(f"{i}\t{score}\n")

#     executor.map(score_file, os.listdir('.'))
