from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

from yt_bugs_downloader.yt_exporter.config import load_settings
from yt_bugs_downloader.yt_exporter.api.youtrack import YouTrackClient
from yt_bugs_downloader.yt_exporter.services.defects import build_defects_dataframe
from yt_bugs_downloader.yt_exporter.services.versions import collect_versions
from yt_bugs_downloader.yt_exporter.exporters.excel import export_excel
from yt_bugs_downloader.yt_exporter.exporters.charts import build_defects_dashboard_by_week
from yt_bugs_downloader.yt_exporter.metrics.der import export_der_excel


def parse_args(allowed_projects: set[str]):
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=False, help="Project short name (VM, BA, DCI6)")
    args = p.parse_args()

    if not args.project or args.project not in allowed_projects:
        print("Неверно указан проект!")
        sys.exit(1)
    return args


def build_query(project: str, defect_type: str, created_from: str | None) -> str:
    # Ваш локализованный формат:
    # Создана после 2023-01-01
    q = [f"project: {project}", f"Type: {defect_type}"]
    if created_from:
        q.append(f"Создана: {created_from} .. *")
    return " ".join(q)


def main():
    s = load_settings()
    args = parse_args(s.allowed_projects)

    project = args.project
    prefix = s.file_prefix_by_project[project]
    out_path = f"{prefix}_defects.xlsx"

    query = build_query(project, s.issue_type_defect, s.created_from)

    fields = (
        "id,idReadable,summary,created,resolved,"
        "customFields(name,value(name,localizedName,fullName,login,idReadable,values(name,localizedName,fullName,login,idReadable))),"
        "links(direction,linkType(name,localizedName),issues(idReadable,project(shortName),customFields(name,value(name,localizedName,fullName,login,idReadable,values(name,localizedName,fullName,login,idReadable)))))"
    )

    yt = YouTrackClient(s.base_url, s.token)
    issues = yt.fetch_issues(query=query, fields=fields, page_size=s.page_size, max_pages=s.max_pages)

    df, stats = build_defects_dataframe(
        issues,
        resolved_cutoff=s.resolved_cutoff,
        field_status=s.field_status,
        field_priority=s.field_priority,
        field_release=s.field_release,
        ps_project=s.ps_project,
        ps_version_field=s.ps_version_field,
    )

    versions = collect_versions(project)  # если нужно — можно сделать optional флагом


    final_path, coral_count, fix_filled, affected_filled = export_excel(
        df,
        out_path,
        versions=versions,
        ps_links_col_name="PS links (IDs)",
        ps_version_col_name="PS_Версия",
    )

    excel_path_obj = Path(final_path)
    chart_path = str(excel_path_obj.with_name(f"{excel_path_obj.stem}_dashboard.png"))

    build_defects_dashboard_by_week(
        df,
        chart_path,
        created_col="Created",
        resolved_col="Resolved",
        priority_col="Priority",
        ps_links_col="PS links (IDs)",
        title_prefix=project,
    )

    excel_path_obj = Path(final_path)
    der_path = str(excel_path_obj.with_name(f"{excel_path_obj.stem}_der.xlsx"))

    df_for_der = pd.read_excel(final_path, sheet_name="Defects")

    export_der_excel(
        df_for_der,
        der_path,
        affected_version_col="Affected version",
        quarter_col="C_Qtr",
        ps_links_col="PS links (IDs)",
        status_col="Status",
        priority_col="Priority",
    )

    print(f"Saved: {final_path}")
    print("\n===== SUMMARY =====")
    print(f"Всего получено из API:                 {stats.total_fetched}")
    print(f"Отфильтровано (resolved < {s.resolved_cutoff}): {stats.filtered_out_resolved_before_cutoff}")
    print(f"Итого в файле:                         {stats.kept_total}")
    print(f"Из них unresolved:                     {stats.kept_unresolved}")
    print(f"Issue с PS links (>=1):                {stats.kept_with_ps_links}")
    print(f"Есть PS links, но нет версии:          {coral_count}")
    print(f"Автозаполнено Fix version:             {fix_filled}")
    print(f"Автозаполнено Affected version:        {affected_filled}")
    print(f"Chart saved:                           {chart_path}")
    print(f"DER saved:                             {der_path}")
    print("===================")


if __name__ == "__main__":
    main()