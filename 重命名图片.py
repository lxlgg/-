#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime, timezone

TARGET_DIR = "/Users/liuxinlei/Downloads/test"
LOG_FILE = os.path.join(TARGET_DIR, "rename_log.log")
SNAPSHOT_FILE = os.path.join(TARGET_DIR, ".dir_snapshot.json")

IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "heic", "bmp", "tiff", "webp"}


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_tree_snapshot(base_dir):
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
    added = []
    removed = []
    modified = []

    for path, info in new.items():
        if path not in old:
            added.append(path)
        elif info != old[path]:
            modified.append(path)

    for path in old:
        if path not in new:
            removed.append(path)

    return added, removed, modified


def record_snapshot(label=""):
    snap = get_tree_snapshot(TARGET_DIR)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        old = {}

    if old:
        added, removed, modified = diff_snapshots(old, snap)
        if added or removed or modified:
            log(f"📋 文件夹快照对比 [{ts}] {label}")
            if added:
                log(f"  ➕ 新增 ({len(added)}):")
                for p in sorted(added):
                    log(f"      + {p}")
            if removed:
                log(f"  ➖ 删除 ({len(removed)}):")
                for p in sorted(removed):
                    log(f"      - {p}")
            if modified:
                log(f"  🔄 修改 ({len(modified)}):")
                for p in sorted(modified):
                    log(f"      ~ {p}")
        else:
            log(f"📋 快照对比 [{ts}] {label} — 无变化")
    else:
        log(f"📋 首次快照记录 [{ts}] {label} — {len(snap)} 项")

    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)

    return snap


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


def main():
    pending = []
    for entry in os.listdir(TARGET_DIR):
        filepath = os.path.join(TARGET_DIR, entry)
        if not os.path.isfile(filepath):
            continue
        ext = entry.rsplit(".", 1)[-1].lower() if "." in entry else ""
        if ext in IMAGE_EXTS:
            pending.append((entry, filepath))

    if not pending:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] ℹ️ 根目录下无待处理图片，跳过本次执行"
        print(line)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return

    record_snapshot("(执行前)")

    subfolder_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    subfolder_path = os.path.join(TARGET_DIR, subfolder_name)
    os.makedirs(subfolder_path, exist_ok=True)

    log("=== 开始执行 ===")
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

    log(f"=== 执行结束，所有图片已移入子文件夹: {subfolder_name} ===")

    record_snapshot("(执行后)")

    print()
    print(f"完成！日志已写入: {LOG_FILE}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--snapshot":
        label = sys.argv[2] if len(sys.argv) > 2 else "手动快照"
        record_snapshot(label)
        print(f"快照已记录，对比结果已写入 {LOG_FILE}")
    else:
        main()
