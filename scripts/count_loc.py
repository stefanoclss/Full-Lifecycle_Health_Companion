
import os

def count_lines(directory):
    py_lines = 0
    js_lines = 0
    py_files = 0
    js_files = 0
    
    ignore_dirs = {'.git', 'venv', '.venv', 'node_modules', '__pycache__', '.idea', '.vscode', 'ml_models', '.ipynb_checkpoints'}

    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        py_lines += lines
                        py_files += 1
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
            elif ext == '.js':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        js_lines += lines
                        js_files += 1
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    print(f"Python: {py_lines} lines in {py_files} files")
    print(f"JavaScript: {js_lines} lines in {js_files} files")

if __name__ == "__main__":
    count_lines('.')
