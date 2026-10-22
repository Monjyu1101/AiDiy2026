"""この作業コピーに属する診断ランチャーのみ解除する。"""
from pathlib import Path
import hashlib
import secrets
import importlib.util


_path_spec = importlib.util.spec_from_file_location('aidiy_diag_cleanup_path', Path(__file__).resolve().parent.parent / 'scripts' / '_setup_path.py')
_path_helper = importlib.util.module_from_spec(_path_spec)
_path_spec.loader.exec_module(_path_helper)
remove_launcher_path = _path_helper.remove_launcher_path

_stop_spec = importlib.util.spec_from_file_location(
    'aidiy_diag_stop', Path(__file__).resolve().parent / '起動' / 'プロセス停止.py')
_stop_helper = importlib.util.module_from_spec(_stop_spec)
_stop_spec.loader.exec_module(_stop_helper)


def stop_processes():
    """ランチャー解除の選択と独立して、本体・残留子プロセスの終了を確認する。"""
    return _stop_helper.stop(Path(__file__).resolve().parent)


def cleanup(choices=None):
    if choices is not None and choices.get('diag') is False:
        return True
    script = str(Path(__file__).resolve().with_name('diag_main.mjs'))
    marker = 'aidiy_diag-owner:' + hashlib.sha256(script.encode('utf-8')).hexdigest()
    try:
        stop_file = Path(__file__).resolve().with_name('.stop-request')
        temporary = stop_file.with_suffix('.tmp')
        temporary.write_text(secrets.token_hex(16), encoding='utf-8')
        temporary.replace(stop_file)
        if not stop_processes():
            return False
        for name in ('aidiy_diag', 'aidiy_diag.cmd'):
            launcher = Path.home() / '.local' / 'bin' / name
            if launcher.is_file() and marker in launcher.read_text(encoding='utf-8'):
                launcher.unlink()
                print(f'診断ランチャーを解除しました: {launcher}')
        print('この作業コピーの診断の終了を確認しました。')
        return remove_launcher_path()
    except OSError as exc:
        print(f'診断ランチャーの解除に失敗しました: {exc}')
        return False


if __name__ == '__main__':
    raise SystemExit(0 if cleanup() else 1)
