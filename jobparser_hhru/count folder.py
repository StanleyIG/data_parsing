import os

directory = 'img'
count = sum(os.path.isdir(os.path.join(directory, name)) for name in os.listdir(directory))
print(f"Количество папок в папке '{directory}': {count}")