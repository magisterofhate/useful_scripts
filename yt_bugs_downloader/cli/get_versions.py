from yt_bugs_downloader.yt_exporter.config import load_settings
from yt_bugs_downloader.yt_exporter.services.versions import collect_versions
import argparse
import sys


def main():
    settings = load_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=False)
    args = parser.parse_args()

    if not args.project or args.project not in settings.allowed_projects:
        print("Неверно указан проект!")
        sys.exit(1)

    versions = collect_versions(args.project)
    for v, d in versions:
        print(v, d)


if __name__ == "__main__":
    main()