#!/usr/bin/env python3
"""Read-only external-command reference scan. Never imports target code or executes commands.
Usage: python source_scan.py REPOSITORY OUTPUT_JSON [PINNED_COMMIT]
Review candidates before using them: a string can be a subcommand, test fixture, or example.
"""
from __future__ import annotations
import ast, hashlib, json, re, sys
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
OUTPUT=Path(sys.argv[2]).resolve()
COMMIT=sys.argv[3] if len(sys.argv)>3 else None
SELECTED={e['path'] for e in json.loads(Path(sys.argv[4]).read_text())} if len(sys.argv)>4 else None
EXT={'.py','.js','.mjs','.cjs','.ts','.cts','.mts','.vue','.sh','.bat','.cmd','.ps1','.toml','.json','.yaml','.yml','.ini','.conf','.cnf','.c','.h','.html','.css','.tmpl','.service','.fixture','.lock','.example','.sql'}
SPECIAL={'Dockerfile','Makefile','AGENTS.md','README.md','hermes-gateway'}
SKIP={'.git','.venv','node_modules','__pycache__'}
REFERENCE=re.compile(r'\b(?:subprocess|Popen|create_subprocess|spawnSync|spawn|execSync|execFileSync|execFile|exec|os\.system|os\.popen|find_executable|find_node_executable|shutil\.which|command|executable|INSTALL_RECIPES|\.exe)\b',re.I)
files=[];refs=[];candidates={};errors=[]
def add(value,path,line,kind):
 if not isinstance(value,str) or not value or len(value)>160 or '\n' in value:return
 candidates.setdefault(value,[]).append({'path':path,'line':line,'kind':kind})
def strings(node):
 if isinstance(node,ast.Constant) and isinstance(node.value,str):return [node.value]
 if isinstance(node,(ast.List,ast.Tuple)):return [x.value for x in node.elts if isinstance(x,ast.Constant) and isinstance(x.value,str)]
 return []
for p in sorted(ROOT.rglob('*')):
 rel=p.relative_to(ROOT)
 if p.is_symlink() or not p.is_file() or SKIP.intersection(rel.parts):continue
 path=rel.as_posix()
 if SELECTED is not None and path not in SELECTED:continue
 if SELECTED is None and p.suffix not in EXT and p.name not in SPECIAL and not (p.stat().st_mode&0o111) and not ('requirements' in p.name and p.suffix=='.txt'):continue
 try:b=p.read_bytes();s=b.decode('utf-8-sig')
 except (OSError,UnicodeDecodeError) as exc:errors.append({'path':path,'error':str(exc)});continue
 files.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
 for line,text in enumerate(s.splitlines(),1):
  if REFERENCE.search(text):refs.append({'path':path,'line':line,'text':text[:1500]})
 if p.suffix=='.py':
  try:tree=ast.parse(s)
  except (SyntaxError,ValueError) as exc:errors.append({'path':path,'error':'AST: '+str(exc)});continue
  for n in ast.walk(tree):
   if isinstance(n,ast.Call):
    f=ast.unparse(n.func)
    if f.endswith(('.which','.find_executable')) or f in ('which','_which','find_executable','find_node_executable','_has_command') or f.endswith('._has_command'):
     for a in n.args:
      for val in strings(a):add(val,path,n.lineno,'resolver')
    if re.search(r'(run|Popen|call|check_output|check_call|create_subprocess_exec|create_subprocess_shell|execv|spawn|bounded_probe_run|os.system|os.popen|_exec)$',f) and n.args:
     vals=strings(n.args[0]);a=n.args[0]
     if isinstance(a,ast.Constant) and isinstance(a.value,str):add(a.value,path,n.lineno,'exec_string')
     if isinstance(a,ast.JoinedStr) and a.values and isinstance(a.values[0],ast.Constant):add(a.values[0].value.strip().split(' ')[0],path,n.lineno,'dynamic_shell_prefix')
     if isinstance(a,(ast.List,ast.Tuple)) and vals and a.elts and isinstance(a.elts[0],ast.Constant):add(vals[0],path,n.lineno,'exec_argv')
   if isinstance(n,ast.For) and re.search(r'(cmd|command|binary|exe|candidate)',ast.unparse(n.target),re.I):
    for val in strings(n.iter):add(val,path,n.lineno,'resolver_candidates')
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and re.search(r'(player|cmd|command|argv)',ast.unparse(n.func.value),re.I) and n.args:
    vals=strings(n.args[0])
    if isinstance(n.args[0],(ast.List,ast.Tuple)) and vals:add(vals[0],path,n.lineno,'argv_append')
   if isinstance(n,(ast.Assign,ast.AnnAssign)):
    names=' '.join(ast.unparse(x) for x in n.targets) if isinstance(n,ast.Assign) else ast.unparse(n.target)
    v=n.value
    if re.search(r'(cmd|command|argv|binaries|candidates)',names,re.I) and isinstance(v,(ast.List,ast.Tuple)) and v.elts and isinstance(v.elts[0],ast.Constant):add(v.elts[0].value,path,n.lineno,'argv_assignment')
   if isinstance(n,ast.Dict):
    for k,v in zip(n.keys,n.values):
     if isinstance(k,ast.Constant) and k.value in ('command','cmd','binary','bin','executable'):
      vals=strings(v)
      if vals:add(vals[0],path,n.lineno,'registry')
 else:
  for line,text in enumerate(s.splitlines(),1):
   for m in re.finditer(r'''(?:spawn|spawnSync|execFile|execFileSync|exec|execSync|which)\(\s*['"]([^'"]+)['"]''',text):add(m[1],path,line,'js_exec')
result={'repository':'monjyu1101/AiDiy2026','commit':COMMIT,'method':'All selected source text read; Python AST and cross-language reference matching; no target code imported or executed. Candidates require review.','files_scanned':len(files),'missing_files':sorted(SELECTED-{f['path'] for f in files}) if SELECTED is not None else [],'files':files,'errors':errors,'command_candidates':candidates,'execution_references':refs}
OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files_scanned':len(files),'candidates':len(candidates),'execution_references':len(refs),'errors':len(errors)},ensure_ascii=False))
