---
name: image_organizer
description: 按EXIF拍摄日期重命名图片并归档到时间戳子文件夹。当用户需要整理图片、按拍摄日期归档、批量重命名照片时自动激活。
---

# Image Organizer - 图片按拍摄日期归档

## 功能说明

扫描指定目录下的图片文件，读取 EXIF 拍摄日期，按 `YYYY-MM-DD-HH-MM-SS` 格式重命名，并移动到以当前执行时间命名的子文件夹中。

## 触发条件

当用户提到以下意图时激活此 skill：
- 整理图片 / 照片归档
- 按拍摄日期重命名图片
- 批量重命名照片
- 图片按日期分组

## 调用方式

```bash
python3 /Users/liuxinlei/Downloads/test/脚本工具/image_organizer/image_organizer.py <目标目录>
```

### 参数

| 参数 | 说明 |
|---|---|
| `target_dir` | 要处理的目录路径，默认当前目录 `.` |
| `--log <path>` | 自定义日志文件路径，默认 `<目标目录>/rename_log.log` |
| `--no-snapshot` | 跳过目录快照对比功能 |

### 示例

```bash
# 处理 Downloads 文件夹
python3 /Users/liuxinlei/Downloads/test/脚本工具/image_organizer/image_organizer.py ~/Downloads

# 处理当前目录
python3 /Users/liuxinlei/Downloads/test/脚本工具/image_organizer/image_organizer.py
```

## 处理逻辑

1. **扫描**：仅扫描目标目录根目录下的图片（不递归子目录），支持 `png jpg jpeg gif heic bmp tiff webp`
2. **无图跳过**：根目录没有待处理图片时直接退出，不创建空文件夹
3. **读取日期**：优先用 macOS `mdls` 读取 `kMDItemContentCreationDate`（EXIF拍摄时间），自动从 UTC 转换为本地时区；读取失败时回退到文件修改时间
4. **同名冲突**：同秒拍摄的图片自动追加 `_1`、`_2` 后缀
5. **日志**：所有操作追加写入 `<目标目录>/rename_log.log`，带时间戳

## 依赖

- **系统**：macOS（依赖 `mdls` 命令）
- **Python**：3.6+，仅使用标准库（`os` `sys` `json` `argparse` `subprocess` `shutil` `datetime`）
- **无需**安装第三方包
