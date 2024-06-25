import os
import json
import subprocess
import shutil

class Mount:

    def __init__(self, logger, download_dir):
        self.files = None
        self.logger = logger
        self.download_dir = download_dir

    def get_files(self, dir):
        return [f"{dir}/{file}" for file in os.listdir(self.download_dir) if not file.startswith('.')]

    def get_video_type(self, filename) -> float:
        filename = filename.lstrip(f"{self.download_dir}/")
        return filename.split("_")[-1].split(".")[0]

    def get_start_time(self, filename) -> float:
        return self.get_start_time_path(filename, self.download_dir)

    def get_start_time_path(self, filename, path) -> float:
        filename = filename.lstrip(f"{path}/")
        return float(filename.split("_")[0])

    def get_type_video(self, filename) -> str:
        filename = filename.lstrip(f"{self.download_dir}/")
        return filename.split("_")[1].split(".")[0]

    def get_filename(self, filename) -> str:
        filename = filename.lstrip(f"{self.download_dir}/")
        return filename

    def get_filename_path(self, filename, path) -> str:
        filename = filename.lstrip(f"{path}/")
        return filename

    def get_end_time(self, filename) -> float:
        out = subprocess.check_output(
            ["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", filename])

        ffprobe_data = json.loads(out)
        return float(ffprobe_data["format"]["duration"])

    def merge_share_and_conf_chunks(self, screen_sharing_file, conference_file, result_file):
        self.logger.info(f"Начало обьединения {screen_sharing_file} и {conference_file} (параллельно)")

        time_video_sharing = self.get_start_time(screen_sharing_file)
        time_video_conf = self.get_start_time(conference_file)

        end_time_share = self.get_end_time(screen_sharing_file)
        end_time_conf = self.get_end_time(conference_file)

        end_time = max(end_time_share, end_time_conf)

        diff_video = time_video_sharing - time_video_conf

        subcommand = f"[0:v]tpad=start_duration={diff_video},scale=1024:576[v0]; \
                                        [1:v]scale=150:150,fifo[v1];" \
                                        if diff_video > 0 else \
                                        f"[0:v]scale=1024:576[v0]; \
                                        [1:v]tpad=start_duration={abs(diff_video)},scale=150:150,fifo[v1];"

        # 1 - screensharing, 2 - conf(вебка)

        # монтирование вебки и видео
        command = (f"ffmpeg -y -i {screen_sharing_file} -i {conference_file} \
                    -f lavfi -i color=black:s=1024x576:d={end_time} \
                    -f lavfi -t 7 -i anullsrc -filter_complex \" \
                    {subcommand} \
                    [1:a]amix=inputs=1:duration=longest[amixed]; \
                    [2][v0]overlay=eof_action=pass[over1]; \
                    [over1][v1]overlay=eof_action=pass[over2]\" \
                    -vcodec libx264 \
                    -map [over2] \
                    -map [amixed] \
                    {result_file}")

        try:
            subprocess.call(command, shell=True)
            # check exists file
            self.logger.info(f"Файл {result_file} был успешно создан с продолжительностью {end_time}.")
        except subprocess.CalledProcessError as e:
            self.logger.error("An error occurred while running ffmpeg:")
            print(e)

    def count_video_on_type(self):
        result = {}
        for file in self.files:
            type_video = self.get_type_video(file)
            if type_video in result:
                result[type_video] += 1
            else:
                result[type_video] = 1

        return result

    def get_min_type(self, types) -> str:
        t = list(types.keys())[0]
        min = types[t]
        for type in types.keys():
            if types[type] < min:
                t = type
                min = types[type]

        return t

    def get_index_for_group(self, file):
        time_target_file = self.get_start_time(file)

        min_time = -1
        min_index = -1

        for index in range(len(self.files_min_types)):
            value = self.files_min_types[index]
            start_time = self.get_start_time(value)

            diff_time = max(start_time, time_target_file) - min(start_time, time_target_file)

            if min_time < 0 or diff_time < min_time:
                min_time = diff_time
                min_index = index

        return min_index

    def find_near_video_other_type(self, target_file, find_type):
        time_target_file = self.get_start_time(target_file)

        min_time = -1
        result_file = ''

        for file in self.files:
            type_video = self.get_type_video(file)
            if type_video == find_type:
                start_time = self.get_start_time(file)

                diff_time = max(start_time, time_target_file) - min(start_time, time_target_file)

                if min_time < 0 or diff_time < min_time:
                    min_time = diff_time
                    result_file = file

        return result_file

    def count_files_of_min_type(self, min_type):
        return sum(1 for file in self.files if self.get_type_video(file) == min_type)

    def group_video(self, min_type):
        min_type_count = self.count_files_of_min_type(min_type)
        result = [[] for _ in range(min_type_count)]

        # screensharing
        for file in self.files:
            type_video = self.get_type_video(file)
            if type_video == min_type:
                continue

            index = self.get_index_for_group(file)
            result[index].append(file)

        return result

    def concat_video(self):
        self.logger.info('Concatenating video ...')

        count_videos_on_type = self.count_video_on_type()

        type_min = self.get_min_type(count_videos_on_type)
        self.files_min_types = [file for file in self.files if self.get_type_video(file) == type_min]
        groups_video = self.group_video(type_min)

        new_path = self.download_dir+'/.tmp/'

        if not os.path.exists(new_path):
            os.makedirs(new_path)

        for group_video in groups_video:
            if len(group_video) > 1:
                new_path_grp = []
                for video in group_video:
                    shutil.move(video, new_path+self.get_filename(video))
                    new_path_grp.append(new_path+self.get_filename(video))

                # Сортируем файлы по времени начала
                sorted_new_path_grp = sorted(new_path_grp, key=lambda g: self.get_start_time_path(g, new_path))
                # Путь к выходному файлу
                output_file = self.download_dir + '/' + self.get_filename_path(sorted_new_path_grp[0], new_path)
                self.merge_group_video_to_one(sorted_new_path_grp, output_file)

        self.files = self.get_files(self.download_dir)

        # fixme hardcode под формат screenshare и conference
        result_compare_videos = []

        count_part = 0
        for screenshare_file in self.files:
            # объединяем попарно в одно видео
            type_video = self.get_type_video(screenshare_file)
            if type_video == 'conference':
                continue

            # check several files
            conference_file = self.find_near_video_other_type(screenshare_file, 'conference')

            count_part += 1

            # add check...
            self.merge_share_and_conf_chunks(screenshare_file,
                                    conference_file, self.download_dir+'/'+f'part_{count_part}.mp4')
            result_compare_videos.append(self.download_dir+'/'+f'part_{count_part}.mp4')

        if count_part > 1:
            # группу видео собираем в одно итоговое -> profit
            self.merge_group_video_to_one(result_compare_videos, self.download_dir+'/result.mp4')

    def merge_group_video_to_one(self, group_video, output_file):
        self.logger.info(f"Начало обьединения {' '.join(group_video)} (последовательно)")

        # cоздаем временную папку для промежуточных файлов
        temp_folder = "."
        os.makedirs(temp_folder, exist_ok=True)

        # Создаем файлы для списков файлов
        group_video_list_file = f"{temp_folder}/group_video_list_file.txt"

        # Записываем пути к файлам в соответствующие списки
        with open(group_video_list_file, "w") as file:
            file.write("\n".join(f"file '{path}'" for path in group_video))

        # todo add support mount use gpu (nvidea)

        # Команда FFmpeg для объединения видео с использованием GPU
        ffmpeg_command = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            group_video_list_file,
            "-c:v",
            "libx264",
            "-preset",
            "fast",  # Быстрый пресет для кодирования
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            output_file,
        ]

        try:
            subprocess.run(ffmpeg_command, check=True)
            self.logger.info(f"Файл {output_file} был успешно создан.")
        except subprocess.CalledProcessError as e:
            self.logger.error("An error occurred while running ffmpeg:")
            print(e)

        os.remove(group_video_list_file)

    def check_bad_files(self):
        for file in self.get_files(self.download_dir):
            st = os.stat(file)
            if st.st_size < 1:
                self.logger.info(f"find bad file "+file)
                os.remove(file)


    def run(self):
        self.check_bad_files()
        self.files = self.get_files(self.download_dir)
        self.concat_video()