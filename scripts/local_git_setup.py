"""未管理の作業フォルダだけに、外部接続のないローカル Git を用意する。"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


def ensure_local_git(base_dir: Path) -> tuple[str, str]:
    """既存 Git 管理情報は変更しない。初回 add / commit / remote 設定も行わない。"""
    root = Path(base_dir).resolve(strict=True)
    if not root.is_dir():
        return "error", "Git: 対象がフォルダではありません。"
    # .git はディレクトリだけでなく worktree/submodule のファイルも有効。
    # 壊れたポインタやリンクも再初期化せず、利用者の管理情報を保護する。
    for directory in (root, *root.parents):
        if os.path.lexists(directory / ".git"):
            return "existing", "Git: 既存の管理環境を維持します。"
    metadata = root / ".git_local"
    if os.path.lexists(metadata):
        return "skipped", "Git: .git_local が既にあるため変更しません。"
    git = shutil.which("git")
    if not git:
        return "skipped", "Git: 未導入のためローカル管理をスキップします。"
    # 呼び出し元の GIT_DIR / WORK_TREE / INDEX_FILE / CONFIG_* 等で別の
    # リポジトリに作用しないよう、この処理の子プロセスだけから除く。
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}

    def run(*args: str):
        return subprocess.run([git, "-C", str(root), *args], env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=30, check=False)

    try:
        # 所有権エラー等を「未管理」と誤認しない。英語固定で判定する。
        # ファイルによる検出に加えて Git 自身の探索も確認する。
        env["LC_ALL"] = "C"
        probe = run("rev-parse", "--git-dir")
        if probe.returncode == 0:
            return "existing", "Git: 既存の管理環境を維持します。"
        if "not a git repository" not in probe.stderr.lower():
            return "error", "Git: 管理状態を確認できないため初期化しません。"
        # テンプレートの独自フックを持ち込まず、空の履歴だけを作る。
        result = run("init", "--template=", "--initial-branch=main",
                     f"--separate-git-dir={metadata}", str(root))
        if result.returncode != 0:
            return "error", "Git: ローカル管理の初期化に失敗しました（既存情報は削除しません）。"
        # 作業フォルダごとの移動でも利用できる相対参照にする。
        (root / ".git").write_text("gitdir: .git_local\n", encoding="utf-8")
        exclude = metadata / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as stream:
            stream.write("\n# AiDiy local Git metadata and ignore definitions\n/.git_local/\n.gitignore\n")
        return "created", "Git: .git_local を作成しました（ローカル履歴専用・未コミット）。"
    except (OSError, subprocess.SubprocessError):
        return "error", "Git: ローカル管理を準備できませんでした（既存情報は削除しません）。"
