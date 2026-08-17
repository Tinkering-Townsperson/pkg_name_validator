import re
import sys
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from time import time

import requests

parser = ArgumentParser(prog="python -m pkg_name_validator")
parser.add_argument("name", help="Package name to validate")
parser.add_argument("-r", "--repository", "--repo", dest="repo", help="Repository to check.", default="pypi")
parser.add_argument("-u", "--ultranormalize", dest="ultranormalize", action="store_true",
    help="Check if an 'ultranormalized' match exists.")
args = parser.parse_args()

match args.repo:
	case "pypi":
		repo_url = "https://pypi.org"
	case "testpypi":
		repo_url = "https://test.pypi.org"
	case _:
		sys.exit(print(f"The repository {args.repo} is not defined. Feel free to add it here: https://github.com/tinkering-townsperson/pkg_name_validator"))

res = requests.get(f"{repo_url}/simple/{args.name}")
invalid_names_res = requests.get("https://raw.githubusercontent.com/tinkering-townsperson/pkg_name_validator/main/lists/invalid_names.txt")
invalid_names = invalid_names_res.text.split("\n")

if res.status_code == 200:
	print(f"Package \"{args.name}\" is not available.")
	print(f"View it at: {repo_url}/project/{args.name}")
elif args.name in invalid_names or " " in args.name or "\t" in args.name:
 	print(f"The package name \"{args.name}\" is not allowed")
elif res.status_code == 404:
    def ultranormalize(name: str):
        return (name
            .lower()
            .replace("o", "0")
            .replace("i", "1").replace("l", "1")
            .replace("-", "").replace("_", "").replace(".", "")
        )

    if args.ultranormalize:
        simple_file_path = Path(f"{tempfile.gettempdir()}/pkg_name_validator.{args.repo}.txt")
        simple_all = {}

        # Check cached temp file
        if (simple_file_path.is_file() and simple_file_path.stat().st_mtime > time() - 3600):
            with simple_file_path.open(mode="r") as f:
                for line in f:
                    n, un = line.rstrip("\n").split(sep=" ", maxsplit=1)
                    simple_all[un] = n
        else:
            print("Requesting all project names...")
            text = requests.get(f"{repo_url}/simple").text
            matches = re.findall(r"<a [^>]*>([^<]+)</a>", text)

            with simple_file_path.open(mode="w") as f:
                for n in matches:
                    un = ultranormalize(n)
                    simple_all[un] = n
                    _ = f.write(f"{n} {un}\n")

        ultra_name = ultranormalize(args.name)
        if pkg := simple_all.get(ultra_name):
            print(f"Package name \"{args.name}\" is too close to existing package \"{pkg}\".")
            print(f"View it at: {repo_url}/project/{pkg}")
        else:
            print(f"Package \"{args.name}\" is available!")
    else:
        print(f"Package \"{args.name}\" is available!")
else:
	print(f"Pinging {repo_url} gave the status code {res.status_code}. If you know what that means, feel free to drop a pull request or issue at https://github.com/tinkering-townsperson/pkg_name_validator. Thank you!")
