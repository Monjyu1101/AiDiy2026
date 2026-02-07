curl -X POST http://localhost:8092/apps/M配車区分/登録 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"配車区分ID\": \"99\", \"配車区分名\": \"検証\", \"配車区分備考\": \"紫\", \"配色枠\": \"#330044\", \"配色背景\": \"#e6ccff\", \"配色前景\": \"#000000\"}"


