# `pipm` - Proof of Concept for Julia-Like Package Management in Python

## Quick Start

1. Install project with poetry
2. Enter poetry shell
3. Go to another poetry-based project directory, a lock file must exist
4. Run `pipm` - this will **edit sitecustomize.py** for your current environment to add a custom python import finder, download wheels for that project and install them
5. While in this directory the version of a package which is specified in the lock file will be used
6. Go into another directory with a different poetry lock file, run `pipm`, and now the version of packages in that lock file will be available

Note:

- This is a very basic proof of concept that will only work in equally basic scenarios
- `pipm` installs wheels via `pip download .`, this means that only dependencies under `tool.poetry.dependencies` will be installed, not `dev-dependencies` or others
- Packages without wheels won't work
- Packages with headers/executable entry points probably won't work

## Context

The following is taken from the original post from the Python forums, the post can be found here: <https://discuss.python.org/t/environments-with-a-shared-package-installation-directory-julia-like-packaging/21576>

This is a proof of concept implementation of a Julia-like approach to packaging in Python. For those not familiar, here is a summarised version of the [background to the Julia package manager](https://pkgdocs.julialang.org/v1/#Background-and-Design) (I recommend reading the page fully for those interested):

- Pkg is designed around “environments”: independent sets of packages that can be local to an individual project or shared and selected by name
- The exact set of packages and versions in an environment is captured in a manifest (lock) file
- Since environments are managed and updated independently from each other, “dependency hell” is significantly alleviated in Pkg
- The location of each package version is canonical
- When environments use the same versions of packages, they can share installations, avoiding unnecessary duplication of the package

To illustrate this better, here are some comparisons between current behaviour and a theoretical Julia-like implementation:

Installing a package **without** an environment (e.g. `pip install --user`):

- Currently for python:
  - `pip install` command without a virtual environment activated
  - the package is installed under  `~/.local/lib/python3.10/site-packages/{package_name}`
  - python looks through that path for imports
- For Julia-like package system:
  - install command adds the package to a pyproject file, creates/updates a lock file
  - `pip install --user` equivalent command would add the package to a 'user level' `pyproject` file and update the `lock` file (e.g. Poetry, Pipenv, etc...), these files are stored in a user-level directory, e.g. under `~/.local/state/python3.10/envs/default/{pyproject,lockfile}`
  - package(s) installed under `~/.local/lib/python3.10/multi-site-packages/{package_name}/{package_version}`
  - python **reads the pyproject/lock files** and uses that information to decide which package versions to import

Now, when installing a package **with** an environment:

- Currently for python:
  - `python3 -m venv .venv` to create a new virtual environment
  - `source .venv/bin/activate` to activate it
  - `pip install` to install packages into the environment
  - the venv is (ignoring `--system-site-packages`) completely isolated and all packages are installed in it independently of whatever else is on the system
- For the Julia-like approach:
  - environments are only defined by a `pyproject` file and `lock` file existing in a directory or parent directory, so 'creating' one just means having those files there
    [details="details on local/global environments"]
    In Julia you have the concept of local environments which are what I describe above, where the project/lock files are in a directory, but you can also have environments stored in a central location which make activating environments anywhere you want possible, in a similar way to how conda works
    [/details]
  - `pip install` equivalent command would add the package to the `pyproject` file and update the `lock` file (e.g. Poetry, Pipenv, etc...)
  - package(s) installed under `~/.local/lib/python3.10/multi-site-packages/{package_name}/{package_version}`
  - python **reads the pyproject/lock files** and uses that information to decide which package versions to import

In both cases the key difference is that packages **would continue to get installed under** `~/.local/lib/` instead of into a virtual environment directory, with which package to use being specified in the `pyproject.toml` file.

There are a lot of benefits to this approach, but IMO the main ones are:

- Always have a file that specifies what your current environment is, even when just using user installs
- Avoids unnecessary duplication of package installs, lowering the space used on user devices and the time taken for installs
- No overwriting of packages during updates

As a proof of concept I implemented this in the most basic way I could think of doing, it's pretty hacky but works alright as a rough proof of concept to demonstrate the idea. The PoC works by:

- Using [installer](https://github.com/pypa/installer) to implement a basic wheel installer that installs packages to `multi-site-packages/{package_name}/{package_version}`
- Using [Poetry](https://github.com/python-poetry/poetry) to manage the `pyproject.toml` and `poetry.lock` files
- Adding a custom `importlib` finder which reads a lockfile and inserts the path to the requested version of the package into `sys.path` before importing
- Importing this finder and prepending it to `sys.meta_path` in the `sitecustomize.py` file
- Adding a very crappy `pipm` (meaning 'pip multi', I am not creative) CLI call which just runs `pip download . -d ./tmp-wheelhouse` in a Poetry-managed project, then runs the custom wheel installer on all files in the wheelhouse, this is what actually installs dependencies to `multi-site-packages`

I tend to use Poetry for all of my projects so to test this out I ran `pipm` in a few different repos to populate the `multi-site-packages` directory and played around a bit, surprisingly enough this basic approach sort of works:

```shell
~/.../pipm ❯ python3 -c 'import click; print(click.__file__)'
/home/roscar/.cache/pypoetry/virtualenvs/pipm-p7aS5F8W-py3.10/lib/python3.10/multi-site-packages/click/8.1.3/click/__init__.py

~/.../beanie ❯ python3 -c 'import click; print(click.__file__)'
/home/roscar/.cache/pypoetry/virtualenvs/pipm-p7aS5F8W-py3.10/lib/python3.10/multi-site-packages/click/8.0.4/click/__init__.py

~/.../starlite ❯ python3 -c 'import click; print(click.__file__)'
/home/roscar/.cache/pypoetry/virtualenvs/pipm-p7aS5F8W-py3.10/lib/python3.10/multi-site-packages/click/8.1.3/click/__init__.py

~/.../starlite ❯ python3 -c 'import httpx; print(httpx.__file__)'
/home/roscar/.cache/pypoetry/virtualenvs/pipm-p7aS5F8W-py3.10/lib/python3.10/multi-site-packages/httpx/0.23.1/httpx/__init__.py

~/.../beanie ❯ python3 -c 'import httpx; print(httpx.__file__)'
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'httpx'
```

Above you can see:

1. In `pipm` directory, `click` is version 8.1.3
2. In `beanie` directory, `click` is version 8.0.4
3. In `starlite` directory, `click` is version 8.1.3
4. In `starlite` directory, `httpx` is version 0.23.1
5. In `beanie` directory, `httpx` is 'not installed'

Which is the desired behaviour.

I'd be interested in hearing feedback for this approach, both in the context of a standalone tool and on the potential of something vaguely like this being included in Python.

I have found some similar (historic) discussions on having multiple packages installed at the same time, however they were mostly centred around the idea of being able to import incompatible versions of packages in the same environment, which this does not attempt to do or enable. You would still have one and only one version of a package available.

There has been a lot of discussion on this topic in the past and there is ongoing discussion on topics like PEP 582, but I didn't find anything too similar to this apart from a few suggestions like https://github.com/pypa/pip/issues/11092.

Also I am aware that the proof of concept implementation has a great deal of flaws, but my goal with it was to keep it simple and minimal not complete.
