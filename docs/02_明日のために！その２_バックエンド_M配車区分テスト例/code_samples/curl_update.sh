curl -X POST http://localhost:8091/apps/M配車区分/変更 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"配車区分ID\": \"99\", \"配車区分名\": \"検証\", \"配車区分備考\": \"赤\", \"配色枠\": \"#660000\", \"配色背景\": \"#ffcccc\", \"配色前景\": \"#000000\"}"

