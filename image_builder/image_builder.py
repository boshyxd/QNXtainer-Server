#!/usr/bin/python3
import os
import shlex
import shutil
import subprocess
import tarfile
import tempfile
from typing import Any
from pathlib import Path

import yaml
import typer
from faker import Faker

app = typer.Typer()
gen = Faker()


def copy_files(context_dir: Path, image_build_dir: Path):
    shutil.copytree(context_dir, image_build_dir, dirs_exist_ok=True)


def build_program(build_command: str):
    cleaned_command = shlex.split(build_command)
    result = subprocess.run(cleaned_command)
    result.check_returncode()


def make_runner(image_build_dir: Path, run_command: str):
    env_file_path = image_build_dir / ".env"
    with (
        open(image_build_dir / "run.sh", "w+") as runner_file,
        open(env_file_path) as env_file,
    ):
        env_file_data = " \\\n\t".join([*env_file.readlines(), run_command])
        runner_file.write(env_file_data)


def make_env(image_build_dir: Path, env: dict[str, str]):
    # This just makes KEY=VALUE strings
    env_output = "\n".join(
        map(lambda pair: "=".join([pair[0], str(pair[1])]), env.items())
    )
    with open(image_build_dir / ".env", "w+") as env_file:
        env_file.write(env_output)


def mount_files(image_build_dir: Path, mounted_files: list[str]):
    for mounted_file in mounted_files:
        [src, dest] = mounted_file.split(":")
        src_path = Path(src).absolute().resolve()
        dest_path = image_build_dir / dest
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if src_path.is_dir():
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        elif src_path.is_file():
            shutil.copy2(src_path, dest_path)


@app.command(name="build")
def build_image(context_dir: Path):
    context_dir = context_dir.absolute().resolve()
    image_dir = Path.home() / ".qnxtainer" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    print(f"I'm gonna be working out of: {context_dir}")
    with (
        tempfile.TemporaryDirectory() as image_build_dir,
        open(context_dir / "qnxtainer.yml") as manifest_file,
    ):
        os.chdir(context_dir)
        image_build_dir_path = Path(image_build_dir)
        manifest: dict[str, Any] = yaml.safe_load(manifest_file)
        name: str = manifest.get("name", f"qnxtainer-{gen.slug()}")
        run_command: str = manifest.get("cmd", None)
        build_command: str = manifest.get("build", None)
        env: dict[str, str] = manifest.get("env", {})
        mounted_files: list[str] = manifest.get("mounts", [])
        copy_files(context_dir, image_build_dir_path)
        mount_files(image_build_dir_path, mounted_files)
        os.chdir(image_build_dir_path)
        build_program(build_command)
        make_env(image_build_dir_path, env)
        make_runner(image_build_dir_path, run_command)

        # In case someone does docker-style tagging
        output_name = "/".join(name.split(":"))
        output_filename = image_dir / output_name
        output_filename = output_filename.with_suffix(".tar.gz")

        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(image_build_dir_path, arcname="image")


if __name__ == "__main__":
    app()
