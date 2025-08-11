import nbformat
import os
import sys

def clean_notebook(nb_path):
    """Clean output and metadata from a notebook"""
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    # Clear outputs and execution counts
    for cell in nb.cells:
        if cell.cell_type == 'code':
            cell.outputs = []
            cell.execution_count = None
            if 'metadata' in cell:
                cell.metadata = {}
    
    # Clean notebook metadata
    nb.metadata = {
        "kernelspec": nb.metadata.get("kernelspec", {}),
        "language_info": nb.metadata.get("language_info", {})
    }
    
    # Write back
    with open(nb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
    print(f"Cleaned {nb_path}")

def main():
    """Clean all notebooks in the current directory and subdirectories"""
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.ipynb') and '.ipynb_checkpoints' not in root:
                notebook_path = os.path.join(root, file)
                try:
                    clean_notebook(notebook_path)
                except Exception as e:
                    print(f"Error processing {notebook_path}: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
