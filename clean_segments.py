import os
import glob

files = glob.glob('./segments/*')
for f in files:
    os.remove(f)