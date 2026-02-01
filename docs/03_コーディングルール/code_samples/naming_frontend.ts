// ■ フロントエンド（TypeScript）の命名例

// ✅ 正解：ビジネスドメインは日本語
const 利用者名 = ref('')
const 権限ID = ref('')

const 利用者一覧取得 = async () => {
  const response = await apiClient.post('/core/C利用者/一覧')
  return response.data.data.items
}

// ✅ 正解：システム/フレームワーク用語は英語
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)

// ■ Vue componentタグの制約
// ❌ 誤り（日本語タグ名は無効）
// <C利用者一覧 />

// ✅ 正解（動的コンポーネント）
// <component :is="C利用者一覧" />
