<!-- カテゴリメニュー（C管理.vue等）にカードを追加 -->

<template>
  <div class="category-menu">
    <!-- 既存のカード... -->

    <!-- 新しいカードを追加 -->
    <div class="menu-card" @click="$router.push('/C管理/C新テーブル/一覧')">
      <h3>C新テーブル</h3>
      <p>新テーブルの管理</p>
    </div>
  </div>
</template>

<!-- カードのスタイル例 -->
<style scoped>
.category-menu {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  padding: 20px;
}

.menu-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.menu-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.menu-card h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.menu-card p {
  margin: 0;
  color: #666;
  font-size: 14px;
}
</style>
