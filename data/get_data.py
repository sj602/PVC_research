import os
import shutil

CURR_DIR = os.getcwd()

BASE_DIR = "/Users/seonjin/Desktop/동국대/4-1/개별연구2-딥러닝을 통한 신호데이터의 위치적 분석/patient data 2020.3.27"
folders = os.listdir(BASE_DIR)
i = 1

for big_folder in folders:
	if "LBBB" in big_folder or "RBBB" in big_folder:
		FOLD_DIR = os.path.join(BASE_DIR, big_folder)
		small_folders = os.listdir(FOLD_DIR)
		for small_folder in small_folders:
			if "LBBB" in small_folder or "RBBB" in small_folder:
				FILE_DIR = os.path.join(FOLD_DIR, small_folder)
				FILE_LST = os.listdir(FILE_DIR)
				for file in FILE_LST:
					file_path = os.path.join(FILE_DIR, file)
					if "V1" in file:
						end_name = ".jpg"
						shutil.copy2(file_path, f'{CURR_DIR}/{i}{end_name}')
					if "xml" in file:
						end_name = ".xml"
						shutil.copy2(file_path, f'{CURR_DIR}/{i}{end_name}')
				i+=1


