import os
import subprocess
import sys

import click

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["EMBEDDINGS_URL"] = "https://qembeddings-ih27b7zwaa-tl.a.run.app/embeddings"

PYTHON_EXE = sys.executable
HOST = "0.0.0.0"
PORT = "5454"
ENTRYPOINT = "main:app"


@click.group()
def main():
    """Quipubase CLI."""
    pass


@main.command()
def clean():
    """Clear the __pycache__ directory."""
    file_count = 0
    dir_count = 0
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            if name.endswith(".pyc"):
                os.remove(os.path.join(root, name))
                file_count += 1
        for name in dirs:
            if name == "__pycache__":
                os.rmdir(os.path.join(root, name))
                dir_count += 1
    print(f"Removed {file_count} .pyc files and {dir_count} __pycache__ directories.")


@main.command()
@click.option("--tag", default="latest", help="The tag to use for the Docker image.")
@click.option(
    "--name", default="quipubase", help="The name to use for the Docker image."
)
def build(tag: str, name: str):
    """Build the Quipubase Docker image."""
    print("Building Quipubase...")
    subprocess.run(
        ["cd", "quipubase", "&&", PYTHON_EXE, "setup.py", "build-ext", "--inplace"],
        check=True,
    )
    print("Quipubase build successful!")
    subprocess.run(
        ["docker", "build", "--tag", f"{name}:{tag}", "."],
        check=True,
    )
    print(f"Quipubase Docker image built with tag {tag}.")
    print(f"Pushing to Dockerhub... {name}:{tag}")
    subprocess.run(["docker", "push", f"{name}:{tag}"], check=True)
    print(f"Quipubase Docker image pushed to Dockerhub.")
    print(f"https://hub.docker.com/repository/docker/{name}")


@main.command()
@click.option("--host", default=HOST, help="The host to run the server on.")
@click.option("--port", default=PORT, help="The port to run the server on.")
def run(host: str, port: str):
    """Run the Quipubase server."""
    print("Building Quipubase...")
    subprocess.run([PYTHON_EXE, "setup.py", "build-ext", "--inplace"], check=True)
    print("Quipubase build successful!")
    subprocess.run(
        [PYTHON_EXE, "-m", "uvicorn", ENTRYPOINT, "host", host, "port", port],
        check=True,
    )
    print(f"Quipubase is running on http://{host}:{port}/")


@main.command()
def test():
    """Run the Quipubase tests."""
    subprocess.run([PYTHON_EXE, "-m", "pytest", "tests"], check=True)
