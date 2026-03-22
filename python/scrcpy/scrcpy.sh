#!/usr/bin/env bash
# 在 Git Bash 下使用本目录的 scrcpy.exe（需将官方 Windows 包中的 scrcpy.exe 放到与此脚本同一目录）
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/scrcpy.exe" "$@"
