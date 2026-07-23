import { computed, ref } from 'vue';
import apiClient from '../../api/client';
import {
  type エージェント,
  type エージェント状態,
  type チーム要員,
  type 稼働要員,
  状態情報,
  要員色一覧,
} from './AIチーム_型';

const 稼働要員を変換 = (要員: 稼働要員, index: number): エージェント => {
  const state: エージェント状態 = 要員.状態 in 状態情報 ? 要員.状態 : '召喚中';
  return {
    id: 要員.エージェントID,
    名前: 要員.エージェント名,
    役割: 要員.役割,
    人格情報: 要員.人格情報,
    ...要員色一覧[index % 要員色一覧.length],
    状態: state,
    作業内容: 要員.作業内容 || '次の行動を考えています',
    ひとこと: 要員.ひとこと || '',
    状態更新時刻: 8 + Math.random() * 8,
  };
};

export const useAIチーム = () => {
  const エージェント一覧 = ref<エージェント[]>([]);
  const 召喚要員一覧 = ref<チーム要員[]>([]);
  const 選択中ID = ref('');
  const 召喚対象ID = ref('');
  const 要員読込中 = ref(false);
  const 要員読込エラー = ref('');
  const 召喚中 = ref(false);
  const 排除中ID = ref('');

  const 選択中エージェント = computed(
    () => エージェント一覧.value.find((agent) => agent.id === 選択中ID.value) ?? null,
  );
  const 稼働数 = computed(
    () => エージェント一覧.value.filter((agent) => agent.状態 === '作業中').length,
  );
  const 相談数 = computed(
    () => エージェント一覧.value.filter((agent) => agent.状態 === '相談中').length,
  );
  const 瞑想数 = computed(
    () => エージェント一覧.value.filter((agent) => agent.状態 === '瞑想中').length,
  );
  const 召喚可能要員一覧 = computed(() => {
    const summonedIds = new Set(エージェント一覧.value.map((agent) => agent.id));
    return 召喚要員一覧.value.filter((member) => !summonedIds.has(member.要員ID));
  });

  const 召喚対象を補正 = (preferredId = '') => {
    if (preferredId && 召喚可能要員一覧.value.some((member) => member.要員ID === preferredId)) {
      召喚対象ID.value = preferredId;
      return;
    }
    if (!召喚可能要員一覧.value.some((member) => member.要員ID === 召喚対象ID.value)) {
      召喚対象ID.value = 召喚可能要員一覧.value[0]?.要員ID ?? '';
    }
  };

  const 要員一覧を読み込む = async () => {
    if (要員読込中.value) return;
    要員読込中.value = true;
    要員読込エラー.value = '';
    try {
      const [activeResponse, summonResponse] = await Promise.all([
        apiClient.post('/team/エージェント/一覧', {}),
        apiClient.post('/team/召喚要員/一覧', {}),
      ]);
      if (activeResponse.data?.status !== 'OK') {
        throw new Error(activeResponse.data?.message || '稼働要員を取得できませんでした');
      }
      if (summonResponse.data?.status !== 'OK') {
        throw new Error(summonResponse.data?.message || '召喚要員一覧を取得できませんでした');
      }
      const activeItems = activeResponse.data?.data?.items;
      const summonItems = summonResponse.data?.data?.items;
      if (!Array.isArray(activeItems) || !Array.isArray(summonItems)) {
        throw new Error('要員一覧の応答形式が正しくありません');
      }
      召喚要員一覧.value = summonItems as チーム要員[];
      エージェント一覧.value = (activeItems as 稼働要員[]).map(稼働要員を変換);
      選択中ID.value = エージェント一覧.value[0]?.id ?? '';
      召喚対象を補正();
    } catch (error) {
      要員読込エラー.value = error instanceof Error ? error.message : '要員一覧を取得できませんでした';
    } finally {
      要員読込中.value = false;
    }
  };

  const 選択要員を召喚 = async () => {
    if (召喚中.value || !召喚対象ID.value) return false;
    召喚中.value = true;
    要員読込エラー.value = '';
    try {
      const response = await apiClient.post('/team/エージェント/召喚', {
        要員ID: 召喚対象ID.value,
      });
      if (response.data?.status !== 'OK') {
        throw new Error(response.data?.message || '要員を召喚できませんでした');
      }
      const item = response.data?.data as 稼働要員 | undefined;
      if (!item?.エージェントID) {
        throw new Error('召喚結果の応答形式が正しくありません');
      }
      const agent = 稼働要員を変換(item, エージェント一覧.value.length);
      エージェント一覧.value.push(agent);
      選択中ID.value = agent.id;
      召喚対象を補正();
      return true;
    } catch (error) {
      要員読込エラー.value = error instanceof Error ? error.message : '要員を召喚できませんでした';
      return false;
    } finally {
      召喚中.value = false;
    }
  };

  const 選択要員を排除 = async () => {
    const agent = 選択中エージェント.value;
    if (!agent || agent.id === 'admin' || 排除中ID.value) return;
    排除中ID.value = agent.id;
    要員読込エラー.value = '';
    try {
      const response = await apiClient.post('/team/エージェント/排除', {
        要員ID: agent.id,
      });
      if (response.data?.status !== 'OK') {
        throw new Error(response.data?.message || '要員を排除できませんでした');
      }
      エージェント一覧.value = エージェント一覧.value.filter((item) => item.id !== agent.id);
      選択中ID.value = エージェント一覧.value[0]?.id ?? '';
      召喚対象を補正(agent.id);
    } catch (error) {
      要員読込エラー.value = error instanceof Error ? error.message : '要員を排除できませんでした';
    } finally {
      排除中ID.value = '';
    }
  };

  const 状態を更新 = (
    id: string,
    state: エージェント状態,
    work: string,
    comment: string,
  ) => {
    const agent = エージェント一覧.value.find((item) => item.id === id);
    if (!agent) return;
    agent.状態 = state;
    agent.作業内容 = work;
    agent.ひとこと = comment;
  };

  return {
    エージェント一覧,
    召喚要員一覧,
    選択中ID,
    召喚対象ID,
    要員読込中,
    要員読込エラー,
    召喚中,
    排除中ID,
    選択中エージェント,
    稼働数,
    相談数,
    瞑想数,
    召喚可能要員一覧,
    要員一覧を読み込む,
    選択要員を召喚,
    選択要員を排除,
    状態を更新,
  };
};
