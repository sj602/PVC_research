import os, subprocess

CURR_DIR = os.getcwd()
CURR_FILES = os.listdir(CURR_DIR)
file_path = "/Users/seonjin/Documents/projects/muse/musexmlex.py"
for file in CURR_FILES:
	if "xml" in file:
		arg_path = os.path.join(CURR_DIR, file)
		print(file_path)
		# print(arg_path)
		subprocess.call(["python2", file_path, arg_path])
