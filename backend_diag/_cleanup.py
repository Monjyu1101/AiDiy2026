"""この作業コピーに属する診断ランチャーのみ解除する。"""
from pathlib import Path
import hashlib
import secrets


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
        for name in ('aidiy_diag', 'aidiy_diag.cmd'):
            launcher = Path.home() / '.local' / 'bin' / name
            if launcher.is_file() and marker in launcher.read_text(encoding='utf-8'):
                launcher.unlink()
                print(f'診断ランチャーを解除しました: {launcher}')
        print('この作業コピーの診断へ停止を通知しました。')
        return True
    except OSError as exc:
        print(f'診断ランチャーの解除に失敗しました: {exc}')
        return False


if __name__ == '__main__':
    raise SystemExit(0 if cleanup() else 1)
