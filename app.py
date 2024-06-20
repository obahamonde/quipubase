import os


def process_python_files(root_dir: str, output_file: str) -> None:
    with open(output_file, "w") as md_file:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, root_dir)
                    md_file.write(f"# {relative_path}\n\n")
                    md_file.write("```python\n")
                    with open(full_path, "r") as py_file:
                        md_file.write(py_file.read())
                    md_file.write("\n```\n")
                    md_file.write("---\n")


if __name__ == "__main__":
    current_directory = os.getcwd()
    output_markdown_file = "python_files.md"
    process_python_files(current_directory, output_markdown_file)
    print(f"Markdown file {output_markdown_file} has been created.")
