#!/usr/bin/env python3

import os
import sys
import json
import argparse
import subprocess
import shutil
from datetime import datetime

IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "heic", "bmp", "tiff", "webp"}


def get_content_creation_date(filepath):
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemContentCreationDate", "-raw", filepath],
            capture_output=True, text=True, timeout=5
        )
        raw = result.stdout.strip()
        if not raw or raw == "(null)":
            return None
        dt_utc = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")
        return dt_utc.astimezone()
    except Exception:
        return None


def get_file_mtime(filepath):
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime)


def collect_pending_images(target_dir):
    pending = []
    for entry in os.listdir(target_dir):
        filepath = os.path.join(target_dir, entry)
        if not os.path.isfile(filepath):
            continue
        ext = entry.rsplit(".", 1)[-1].lower() if "." in entry else ""
        if ext in IMAGE_EXTS:
            pending.append((entry, filepath))
    return pending


def scan_snapshot(base_dir):
    snap = {}
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            full = os.path.join(root, d)
            rel = os.path.relpath(full, base_dir)
            snap[rel + "/"] = "DIR"
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, base_dir)
            try:
                st = os.stat(full)
                snap[rel] = {"size": st.st_size, "mtime": st.st_mtime}
            except OSError:
                snap[rel] = None
    return snap


def diff_snapshots(old, new):
    added, removed, modified = [], [], []
    for path, info in new.items():
        if path not in old:
            added.append(path)
        elif info != old[path]:
            modified.append(path)
    for path in old:
        if path not in new:
            removed.append(path)
    return added, removed, modified


def run(target_dir, log_file, snapshot_file, enable_snapshot=True):
    target_dir = os.path.abspath(target_dir)

    def log(msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    pending = collect_pending_images(target_dir)

    if not pending:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] ℹ️ 根目录下无待处理图片，跳过本次执行"
        print(line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return 0

    if enable_snapshot:
        old_snap = scan_snapshot(target_dir)

    subfolder_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    subfolder_path = os.path.join(target_dir, subfolder_name)
    os.makedirs(subfolder_path, exist_ok=True)

    log(f"=== 开始执行 ===")
    log(f"目标目录: {target_dir}")
    log(f"创建子文件夹: {subfolder_name}")

    for entry, filepath in pending:
        dt = get_content_creation_date(filepath)
        if dt is None:
            dt = get_file_mtime(filepath)

        new_name = dt.strftime("%Y-%m-%d-%H-%M-%S")
        new_ext = entry.rsplit(".", 1)[-1].lower()

        target_path = os.path.join(subfolder_path, f"{new_name}.{new_ext}")
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(subfolder_path, f"{new_name}_{counter}.{new_ext}")
            counter += 1

        shutil.move(filepath, target_path)
        log(f"重命名并移动: {entry} -> {os.path.basename(target_path)}")

    log(f"=== 执行结束，共处理 {len(pending)} 张图片，子文件夹: {subfolder_name} ===")
    print()
    print(f"完成！日志已写入: {log_file}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="按EXIF拍摄日期重命名图片并归档到时间戳子文件夹（macOS专用）"
    )
    parser.add_argument(
        "target_dir", nargs="?", default=".",
        help="要处理的目标目录（默认: 当前目录）"
    )
    parser.add_argument(
        "--log", dest="log_file", default=None,
        help="日志文件路径（默认: 目标目录下的 rename_log.log）"
    )
    parser.add_argument(
        "--no-snapshot", action="store_true",
        help="跳过目录快照对比"
    )

    args = parser.parse_args()

    target_dir = os.path.abspath(args.target_dir)
    if not os.path.isdir(target_dir):
        print(f"❌ 目录不存在: {target_dir}", file=sys.stderr)
        sys.exit(1)

    log_file = args.log_file or os.path.join(target_dir, "rename_log.log")
    snapshot_file = os.path.join(target_dir, ".dir_snapshot.json")

    sys.exit(run(target_dir, log_file, snapshot_file, enable_snapshot=not args.no_snapshot))


if __name__ == "__main__":
    main()
