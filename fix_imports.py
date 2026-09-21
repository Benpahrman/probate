import os
import glob

def replace_in_files(directory, old_str, new_str):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if old_str in content:
                    content = content.replace(old_str, new_str)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    count += 1
    print(f"Replaced {old_str} with {new_str} in {count} files in {directory}.")

if __name__ == '__main__':
    src_dir = r"c:\Users\ben\probate\src"
    tests_dir = r"c:\Users\ben\probate\tests"
    
    replace_in_files(src_dir, 'from src.gieni_os', 'from gieni_os')
    replace_in_files(src_dir, 'import src.gieni_os', 'import gieni_os')
    
    replace_in_files(tests_dir, 'from src.gieni_os', 'from gieni_os')
    replace_in_files(tests_dir, 'import src.gieni_os', 'import gieni_os')
