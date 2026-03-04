from __future__ import annotations

from yt_bugs_downloader.yt_exporter.services.versions import collect_versions


def main():
    versions = collect_versions()
    for v, d in versions:
        print(v, d)


if __name__ == "__main__":
    main()