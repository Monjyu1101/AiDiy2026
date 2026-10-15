from playwright.sync_api import sync_playwright
from pathlib import Path
import subprocess, shutil, os, tempfile, atexit
server=subprocess.Popen(['node',str(Path(__file__).with_name('ui-fixture.mjs'))],stdout=subprocess.PIPE,text=True)
atexit.register(server.terminate)
port=int(server.stdout.readline())
output=Path(tempfile.mkdtemp(prefix='diag-ui-synthetic-'))
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1360,'height':950}); errors=[];requests=[]
 page.on('pageerror',lambda e: errors.append(str(e)));page.on('request',lambda r: requests.append((r.method,r.url)))
 page.goto(f'http://127.0.0.1:{port}/proxy/8097/#token=synthetic-ui-test');page.wait_for_selector('#list .item');assert '#' not in page.url
 assert len(page.locator('#list .item').all())==19
 assert not any(m=='POST' for m,u in requests)
 page.locator('#run').click();page.wait_for_function("document.querySelector('#message').textContent.includes('完了')")
 page.locator('#search').fill('Node');assert len(page.locator('#list .item').all())==1;page.locator('#list .item').click();assert page.locator('#detail h2').inner_text()=='Node.js';page.locator('#search').fill('')
 page.screenshot(path=str(output/'install.png'),full_page=True)
 page.get_by_role('button',name='キー設定状況',exact=True).click();page.wait_for_selector('.key-row');assert len(page.locator('.key-row').all())==3
 assert 'OpenAI API' in page.locator('.key-row').first.inner_text()
 assert page.locator('.public-indicator').first.inner_text()=='公開モデル取得済'
 assert not any('キーテスト' in u or '%E3%82%AD%E3%83%BC%E3%83%86%E3%82%B9%E3%83%88' in u for m,u in requests)
 page.locator('.key-row').first.get_by_role('button',name='テスト',exact=True).click();page.wait_for_selector('.models li');assert page.locator('.models li').last.inner_text()=='<script>alert(1)</script>'
 assert page.locator('.key-row').nth(1).get_by_role('button',name='テスト').is_disabled()
 page.screenshot(path=str(output/'keys.png'),full_page=True)
 page.get_by_role('button',name='設定状況を更新').click();page.wait_for_function("document.querySelectorAll('.models li').length===0")
 assert not page.locator('.key-row').first.get_by_role('button',name='テスト',exact=True).is_disabled()
 page.get_by_role('button',name='公開モデルを再取得',exact=True).click()
 page.get_by_role('button',name='公開モデルを再取得',exact=True).wait_for()
 page.locator('#run').click();page.wait_for_function("!document.querySelector('#run').disabled")
 posts=[u for m,u in requests if m=='POST'];assert len(posts)==4,posts
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(output/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'horizontal overflow'
 page.reload();page.wait_for_selector('#login');assert page.locator('#run').is_disabled();assert not errors,errors
 print('PASS: Chromium Vue mount, strict CSP, prefix URL/auth hash removal, installation 19 items, search/detail, explicit-only tests, disabled unset key, escaped models, refresh invalidation, all-test scope, mobile, reload login. POST requests:',len(posts))
 b.close()

print('Synthetic screenshots:',output)
server.terminate()
server.wait(timeout=5)
