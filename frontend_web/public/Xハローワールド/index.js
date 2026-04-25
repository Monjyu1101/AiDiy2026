// -*- coding: utf-8 -*-

const AUTO_INTERVAL_MS = 24000;
const COUNTRY_HOLD_MS = 3500;  // 国レベル表示の保持時間
const LOCAL_REVEAL_MS = 5000;  // 地区レベル開始後に photo を許可するまでの時間

const places = [
  {
    title: 'グランドキャニオン',
    country: 'アメリカ',
    lat: 36.1069,
    lng: -112.1129,
    zoom: 10,
    category: '峡谷',
    wikiTitle: 'Grand_Canyon',
    note: 'コロラド川が長い時間をかけて刻んだ巨大な峡谷。地層の縞が地球の時間を見せます。',
  },
  {
    title: 'ウユニ塩湖',
    country: 'ボリビア',
    lat: -20.1338,
    lng: -67.4891,
    zoom: 10,
    category: '塩湖',
    wikiTitle: 'Salar_de_Uyuni',
    note: '雨季には空を映す鏡のような景色になる、世界最大級の塩原です。',
  },
  {
    title: 'マチュピチュ',
    country: 'ペルー',
    lat: -13.1631,
    lng: -72.5450,
    zoom: 15,
    category: '遺跡',
    wikiTitle: 'Machu_Picchu',
    note: 'アンデスの山稜に築かれたインカ帝国の都市遺跡。地形と建築が一体化しています。',
  },
  {
    title: 'サントリーニ島',
    country: 'ギリシャ',
    lat: 36.3932,
    lng: 25.4615,
    zoom: 12,
    category: '島',
    wikiTitle: 'Santorini',
    note: '白い街並みと青い海、火山カルデラがつくるエーゲ海の景観です。',
  },
  {
    title: 'モン・サン＝ミシェル',
    country: 'フランス',
    lat: 48.6361,
    lng: -1.5115,
    zoom: 14,
    category: '修道院',
    wikiTitle: 'Mont-Saint-Michel',
    note: '潮の満ち引きで表情が変わる海上の修道院。周囲の干潟も印象的です。',
  },
  {
    title: 'イグアスの滝',
    country: 'アルゼンチン / ブラジル',
    lat: -25.6953,
    lng: -54.4367,
    zoom: 13,
    category: '滝',
    wikiTitle: 'Iguazu_Falls',
    note: '大小多数の滝が連なる壮大な水の景観。国境をまたぐ大瀑布です。',
  },
  {
    title: 'ナミブ砂漠',
    country: 'ナミビア',
    lat: -24.7390,
    lng: 15.2887,
    zoom: 11,
    category: '砂漠',
    wikiTitle: 'Namib',
    note: '赤い砂丘が連なる古い砂漠。影と稜線が地図上でも美しい場所です。',
  },
  {
    title: 'アンテロープキャニオン',
    country: 'アメリカ',
    lat: 36.8619,
    lng: -111.3743,
    zoom: 15,
    category: '峡谷',
    wikiTitle: 'Antelope_Canyon',
    note: '水と風が削った細い砂岩の峡谷。光の差し込みが独特の景色を作ります。',
  },
  {
    title: '富士山',
    country: '日本',
    lat: 35.3606,
    lng: 138.7274,
    zoom: 11,
    category: '火山',
    wikiTitle: 'Mount_Fuji',
    note: '日本を代表する成層火山。左右に広がる裾野が地図でもよく分かります。',
  },
  {
    title: 'プリトヴィツェ湖群',
    country: 'クロアチア',
    lat: 44.8654,
    lng: 15.5820,
    zoom: 13,
    category: '湖群',
    wikiTitle: 'Plitvice_Lakes_National_Park',
    note: '湖と滝が階段状につながる国立公園。水の色と森の組み合わせが特徴です。',
  },
  {
    title: 'カッパドキア',
    country: 'トルコ',
    lat: 38.6431,
    lng: 34.8289,
    zoom: 12,
    category: '奇岩',
    wikiTitle: 'Cappadocia',
    note: '火山灰が削られて生まれた奇岩地帯。谷と岩窟住居が広がります。',
  },
  {
    title: 'アマルフィ海岸',
    country: 'イタリア',
    lat: 40.6333,
    lng: 14.6029,
    zoom: 12,
    category: '海岸',
    wikiTitle: 'Amalfi_Coast',
    note: '断崖沿いに街が連なる地中海の景観。曲がりくねった海岸線が魅力です。',
  },
  {
    title: 'ハロン湾',
    country: 'ベトナム',
    lat: 20.9101,
    lng: 107.1839,
    zoom: 11,
    category: '湾',
    wikiTitle: 'Ha_Long_Bay',
    note: '石灰岩の島々が海に浮かぶ景観。入り組んだ湾全体が絶景です。',
  },
  {
    title: 'モニュメントバレー',
    country: 'アメリカ',
    lat: 36.9980,
    lng: -110.0985,
    zoom: 11,
    category: '台地',
    wikiTitle: 'Monument_Valley',
    note: '赤い大地にビュートがそびえる象徴的な西部の風景です。',
  },
  {
    title: 'テーブルマウンテン',
    country: '南アフリカ',
    lat: -33.9628,
    lng: 18.4098,
    zoom: 12,
    category: '山',
    wikiTitle: 'Table_Mountain',
    note: 'ケープタウンを見下ろす平らな頂の山。都市と海と山が近接しています。',
  },
  {
    title: 'パタゴニア フィッツロイ',
    country: 'アルゼンチン',
    lat: -49.2712,
    lng: -73.0432,
    zoom: 11,
    category: '山岳',
    wikiTitle: 'Monte_Fitz_Roy',
    note: '鋭い岩峰と氷河湖が連なる南米南端の山岳景観です。',
  },
  {
    title: 'バンフ国立公園',
    country: 'カナダ',
    lat: 51.4968,
    lng: -115.9281,
    zoom: 11,
    category: '山岳湖',
    wikiTitle: 'Banff_National_Park',
    note: 'ロッキー山脈の湖と森が広がる国立公園。氷河地形が美しい場所です。',
  },
  {
    title: 'チンクエ・テッレ',
    country: 'イタリア',
    lat: 44.1461,
    lng: 9.6439,
    zoom: 13,
    category: '海辺の村',
    wikiTitle: 'Cinque_Terre',
    note: '断崖と小さな入り江に沿って村が並ぶ、リグリア海沿岸の景観です。',
  },
  {
    title: 'ペトラ',
    country: 'ヨルダン',
    lat: 30.3285,
    lng: 35.4444,
    zoom: 14,
    category: '遺跡',
    wikiTitle: 'Petra',
    note: '岩山を削って作られた古代都市。谷筋に沿って遺跡が点在します。',
  },
  {
    title: 'ギーザのピラミッド',
    country: 'エジプト',
    lat: 29.9792,
    lng: 31.1342,
    zoom: 14,
    category: '遺跡',
    wikiTitle: 'Giza_pyramid_complex',
    note: '砂漠と都市の境界に立つ巨大建造物。地図上でも配置の明快さが分かります。',
  },
];

places.push(
  { title: 'ヴィクトリアの滝', country: 'ザンビア / ジンバブエ', lat: -17.9243, lng: 25.8572, zoom: 13, category: '滝', wikiTitle: 'Victoria_Falls', note: 'ザンベジ川にかかる巨大な滝。水煙が遠くからも見える迫力ある景観です。' },
  { title: 'エンジェルフォール', country: 'ベネズエラ', lat: 5.9675, lng: -62.5356, zoom: 12, category: '滝', wikiTitle: 'Angel_Falls', note: 'テーブルマウンテンから落ちる世界有数の落差を持つ滝です。' },
  { title: 'ヨセミテ渓谷', country: 'アメリカ', lat: 37.7456, lng: -119.5936, zoom: 12, category: '渓谷', wikiTitle: 'Yosemite_Valley', note: '花崗岩の絶壁と滝が並ぶ、アメリカ西部を代表する山岳景観です。' },
  { title: 'イエローストーン', country: 'アメリカ', lat: 44.4280, lng: -110.5885, zoom: 8, category: '国立公園', wikiTitle: 'Yellowstone_National_Park', note: '間欠泉、温泉、峡谷、野生動物が集まる広大な国立公園です。' },
  { title: 'グレートバリアリーフ', country: 'オーストラリア', lat: -18.2871, lng: 147.6992, zoom: 7, category: '珊瑚礁', wikiTitle: 'Great_Barrier_Reef', note: '宇宙からも分かるほど広大な珊瑚礁群。海の色の変化が印象的です。' },
  { title: 'ウルル', country: 'オーストラリア', lat: -25.3444, lng: 131.0369, zoom: 12, category: '一枚岩', wikiTitle: 'Uluru', note: '砂漠の中にそびえる巨大な一枚岩。時間帯で色が変わります。' },
  { title: 'ホワイトヘブンビーチ', country: 'オーストラリア', lat: -20.2820, lng: 149.0418, zoom: 13, category: 'ビーチ', wikiTitle: 'Whitehaven_Beach', note: '白い砂と浅瀬の青が渦を描く、ウィットサンデー諸島の景観です。' },
  { title: 'ミルフォード・サウンド', country: 'ニュージーランド', lat: -44.6414, lng: 167.8974, zoom: 12, category: 'フィヨルド', wikiTitle: 'Milford_Sound', note: '切り立った山と海が入り込む、ニュージーランド南島のフィヨルドです。' },
  { title: 'マウントクック', country: 'ニュージーランド', lat: -43.5950, lng: 170.1418, zoom: 11, category: '山岳', wikiTitle: 'Aoraki_/_Mount_Cook', note: '氷河と鋭い山稜が続くニュージーランド最高峰周辺の景観です。' },
  { title: 'ロフォーテン諸島', country: 'ノルウェー', lat: 68.2090, lng: 13.6270, zoom: 9, category: '諸島', wikiTitle: 'Lofoten', note: '北極圏の海に山がせり出す、漁村と岩峰の景観です。' },
  { title: 'ガイランゲルフィヨルド', country: 'ノルウェー', lat: 62.1049, lng: 7.0052, zoom: 12, category: 'フィヨルド', wikiTitle: 'Geirangerfjord', note: '細長い入り江と滝が続く、ノルウェーを代表するフィヨルドです。' },
  { title: 'トロルの舌', country: 'ノルウェー', lat: 60.1240, lng: 6.7408, zoom: 13, category: '断崖', wikiTitle: 'Trolltunga', note: '湖を見下ろす岩棚が突き出した、スケールの大きい断崖景観です。' },
  { title: 'アイスランド南海岸', country: 'アイスランド', lat: 63.5321, lng: -19.5114, zoom: 9, category: '海岸', wikiTitle: 'South_Coast_(Iceland)', note: '滝、黒砂海岸、氷河が短い距離に集まる景観地帯です。' },
  { title: 'ヨークルスアゥルロゥン', country: 'アイスランド', lat: 64.0481, lng: -16.1790, zoom: 12, category: '氷河湖', wikiTitle: 'Jökulsárlón', note: '氷河から崩れた氷山が浮かぶ、青く冷たい氷河湖です。' },
  { title: 'ブルーラグーン', country: 'アイスランド', lat: 63.8804, lng: -22.4495, zoom: 13, category: '温泉', wikiTitle: 'Blue_Lagoon_(geothermal_spa)', note: '溶岩台地の中に乳白色の温泉が広がる独特の景観です。' },
  { title: 'スカフタフェットル', country: 'アイスランド', lat: 64.0167, lng: -16.9667, zoom: 10, category: '氷河', wikiTitle: 'Skaftafell', note: '氷河、山、滝が近接するヴァトナヨークトル周辺の景観です。' },
  { title: 'スイス・アルプス ユングフラウ', country: 'スイス', lat: 46.5368, lng: 7.9622, zoom: 10, category: '山岳', wikiTitle: 'Jungfrau', note: '氷河と高峰が連なるベルナーアルプスの名所です。' },
  { title: 'マッターホルン', country: 'スイス / イタリア', lat: 45.9763, lng: 7.6586, zoom: 11, category: '山岳', wikiTitle: 'Matterhorn', note: '鋭く美しいピラミッド型の山容で知られるアルプスの象徴です。' },
  { title: 'ドロミーティ', country: 'イタリア', lat: 46.4102, lng: 11.8440, zoom: 9, category: '山岳', wikiTitle: 'Dolomites', note: '淡い岩壁と草原が広がる、北イタリアの山岳景観です。' },
  { title: 'ブレッド湖', country: 'スロベニア', lat: 46.3636, lng: 14.0938, zoom: 13, category: '湖', wikiTitle: 'Lake_Bled', note: '湖の小島と城、背後の山並みがまとまった絵画的な景観です。' },
  { title: 'ドゥブロヴニク旧市街', country: 'クロアチア', lat: 42.6410, lng: 18.1106, zoom: 14, category: '旧市街', wikiTitle: 'Dubrovnik', note: '城壁に囲まれた街とアドリア海の青が対比する景観です。' },
  { title: 'メテオラ', country: 'ギリシャ', lat: 39.7217, lng: 21.6306, zoom: 13, category: '奇岩修道院', wikiTitle: 'Meteora', note: '岩柱の上に修道院が建つ、地形と建築が一体になった景観です。' },
  { title: 'パムッカレ', country: 'トルコ', lat: 37.9137, lng: 29.1187, zoom: 13, category: '石灰棚', wikiTitle: 'Pamukkale', note: '白い石灰棚と温泉水が段々に広がる景観です。' },
  { title: 'エフェソス', country: 'トルコ', lat: 37.9398, lng: 27.3413, zoom: 14, category: '遺跡', wikiTitle: 'Ephesus', note: '古代都市の街路や劇場が残る、地中海世界の大規模遺跡です。' },
  { title: 'ワディ・ラム', country: 'ヨルダン', lat: 29.5760, lng: 35.4200, zoom: 11, category: '砂漠', wikiTitle: 'Wadi_Rum', note: '赤い砂漠と岩山が続く、広大で静かな景観です。' },
  { title: '死海', country: 'イスラエル / ヨルダン', lat: 31.5590, lng: 35.4732, zoom: 9, category: '塩湖', wikiTitle: 'Dead_Sea', note: '海抜の低い塩湖。周囲の荒地と水面の対比が印象的です。' },
  { title: 'カッターラ低地', country: 'エジプト', lat: 30.0000, lng: 27.5000, zoom: 8, category: '砂漠低地', wikiTitle: 'Qattara_Depression', note: '広大な砂漠低地が続く、北アフリカらしい地形景観です。' },
  { title: 'シナイ山', country: 'エジプト', lat: 28.5397, lng: 33.9733, zoom: 12, category: '山岳', wikiTitle: 'Mount_Sinai', note: '岩山と砂漠が広がるシナイ半島の歴史的な山です。' },
  { title: 'セレンゲティ', country: 'タンザニア', lat: -2.3333, lng: 34.8333, zoom: 8, category: 'サバンナ', wikiTitle: 'Serengeti_National_Park', note: '広大な草原と野生動物の移動で知られるサバンナ景観です。' },
  { title: 'ンゴロンゴロ', country: 'タンザニア', lat: -3.1618, lng: 35.5877, zoom: 11, category: 'カルデラ', wikiTitle: 'Ngorongoro_Conservation_Area', note: '巨大な火山カルデラの中に草原と湖が広がります。' },
  { title: 'キリマンジャロ', country: 'タンザニア', lat: -3.0674, lng: 37.3556, zoom: 10, category: '山岳', wikiTitle: 'Mount_Kilimanjaro', note: 'アフリカ最高峰。サバンナから雪を抱く山頂まで変化があります。' },
  { title: 'ボルダーズビーチ', country: '南アフリカ', lat: -34.1970, lng: 18.4510, zoom: 14, category: '海岸', wikiTitle: 'Boulders_Beach', note: '丸い岩と白砂の海岸で知られる、ケープ半島の名所です。' },
  { title: 'オカバンゴ・デルタ', country: 'ボツワナ', lat: -19.3045, lng: 22.6437, zoom: 8, category: '湿地', wikiTitle: 'Okavango_Delta', note: '砂漠の中に川が広がる内陸デルタ。水路と緑が網目状に広がります。' },
  { title: 'モロッコ サハラ砂丘', country: 'モロッコ', lat: 31.0802, lng: -4.0118, zoom: 11, category: '砂丘', wikiTitle: 'Erg_Chebbi', note: 'オレンジ色の砂丘が連なる、サハラらしい景観です。' },
  { title: 'シェフシャウエン', country: 'モロッコ', lat: 35.1714, lng: -5.2697, zoom: 14, category: '街並み', wikiTitle: 'Chefchaouen', note: '青く塗られた街並みで知られる、山間の小さな街です。' },
  { title: 'レンソイス・マラニャンセス', country: 'ブラジル', lat: -2.5333, lng: -43.1167, zoom: 10, category: '砂丘湖', wikiTitle: 'Lençóis_Maranhenses_National_Park', note: '白い砂丘の間に雨季のラグーンが現れる独特の景観です。' },
  { title: 'パンタナル', country: 'ブラジル', lat: -17.6500, lng: -57.5000, zoom: 7, category: '湿地', wikiTitle: 'Pantanal', note: '南米最大級の湿地。水と草原が季節で大きく変化します。' },
  { title: 'アマゾン川', country: 'ブラジル / ペルー', lat: -3.4653, lng: -62.2159, zoom: 7, category: '大河', wikiTitle: 'Amazon_River', note: '巨大な蛇行河川と熱帯雨林が広がる地球規模の景観です。' },
  { title: 'ガラパゴス諸島', country: 'エクアドル', lat: -0.8293, lng: -91.1355, zoom: 8, category: '諸島', wikiTitle: 'Galápagos_Islands', note: '火山島と固有種で知られる太平洋の諸島です。' },
  { title: 'トーレス・デル・パイネ', country: 'チリ', lat: -50.9423, lng: -73.4068, zoom: 10, category: '山岳', wikiTitle: 'Torres_del_Paine_National_Park', note: '岩峰、氷河湖、草原が重なるパタゴニアの国立公園です。' },
  { title: 'アタカマ砂漠', country: 'チリ', lat: -24.5000, lng: -69.2500, zoom: 7, category: '砂漠', wikiTitle: 'Atacama_Desert', note: '非常に乾燥した高地砂漠。塩湖や火山が点在します。' },
  { title: 'ペリト・モレノ氷河', country: 'アルゼンチン', lat: -50.4967, lng: -73.1377, zoom: 12, category: '氷河', wikiTitle: 'Perito_Moreno_Glacier', note: '湖へ流れ込む巨大な氷河。氷壁のスケールが圧倒的です。' },
  { title: 'イースター島', country: 'チリ', lat: -27.1127, lng: -109.3497, zoom: 11, category: '島と遺跡', wikiTitle: 'Easter_Island', note: '太平洋の孤島にモアイ像が点在する、独特の文化景観です。' },
  { title: 'ナイアガラの滝', country: 'カナダ / アメリカ', lat: 43.0962, lng: -79.0377, zoom: 13, category: '滝', wikiTitle: 'Niagara_Falls', note: '都市のすぐ近くにある大瀑布。地図でも水の落ち込みが分かります。' },
  { title: 'アラスカ デナリ', country: 'アメリカ', lat: 63.0695, lng: -151.0074, zoom: 8, category: '山岳', wikiTitle: 'Denali', note: '北米最高峰を中心に氷河と荒野が広がります。' },
  { title: 'アンカレッジ近郊氷河', country: 'アメリカ', lat: 61.2176, lng: -149.8997, zoom: 8, category: '氷河地形', wikiTitle: 'Chugach_Mountains', note: 'アラスカ南部の山脈と氷河地形が海岸近くまで迫ります。' },
  { title: 'ザイオン国立公園', country: 'アメリカ', lat: 37.2982, lng: -113.0263, zoom: 12, category: '峡谷', wikiTitle: 'Zion_National_Park', note: '赤い砂岩の壁がそびえる、ユタ州の峡谷景観です。' },
  { title: 'ブライスキャニオン', country: 'アメリカ', lat: 37.5930, lng: -112.1871, zoom: 12, category: '奇岩', wikiTitle: 'Bryce_Canyon_National_Park', note: 'フードゥーと呼ばれる細い岩柱が密集する景観です。' },
  { title: 'アーチーズ国立公園', country: 'アメリカ', lat: 38.7331, lng: -109.5925, zoom: 12, category: '岩石アーチ', wikiTitle: 'Arches_National_Park', note: '自然の岩のアーチが多数点在する赤い大地の景観です。' },
  { title: 'セドナ', country: 'アメリカ', lat: 34.8697, lng: -111.7609, zoom: 12, category: '赤岩', wikiTitle: 'Sedona,_Arizona', note: '赤い岩山と乾いた森がつくる、アリゾナの印象的な景観です。' },
  { title: 'ビッグサー', country: 'アメリカ', lat: 36.2704, lng: -121.8081, zoom: 10, category: '海岸', wikiTitle: 'Big_Sur', note: '太平洋沿いの断崖と海岸線が続くカリフォルニアの名所です。' },
  { title: 'ナパリ・コースト', country: 'アメリカ', lat: 22.1733, lng: -159.6530, zoom: 12, category: '海岸', wikiTitle: 'Nā_Pali_Coast_State_Park', note: 'カウアイ島北岸の険しい崖と海がつくる景観です。' },
  { title: 'マウナケア', country: 'アメリカ', lat: 19.8207, lng: -155.4681, zoom: 11, category: '火山', wikiTitle: 'Mauna_Kea', note: 'ハワイ島の高山火山。山頂部には天文台が並びます。' },
  { title: 'テオティワカン', country: 'メキシコ', lat: 19.6925, lng: -98.8438, zoom: 14, category: '遺跡', wikiTitle: 'Teotihuacan', note: '太陽と月のピラミッドが一直線に並ぶ古代都市遺跡です。' },
  { title: 'チチェン・イッツァ', country: 'メキシコ', lat: 20.6843, lng: -88.5678, zoom: 14, category: '遺跡', wikiTitle: 'Chichen_Itza', note: 'マヤ文明のピラミッドと都市遺跡が残るユカタンの名所です。' },
  { title: 'カナイマ国立公園', country: 'ベネズエラ', lat: 5.3333, lng: -61.5000, zoom: 8, category: 'テーブルマウンテン', wikiTitle: 'Canaima_National_Park', note: 'テーブルマウンテンと滝が点在する、ギアナ高地の景観です。' },
  { title: '張家界', country: '中国', lat: 29.1170, lng: 110.4790, zoom: 12, category: '奇岩', wikiTitle: 'Zhangjiajie_National_Forest_Park', note: '細長い岩柱が森から立ち上がる、幻想的な地形景観です。' },
  { title: '桂林', country: '中国', lat: 25.2345, lng: 110.1799, zoom: 10, category: 'カルスト', wikiTitle: 'Guilin', note: '川沿いに石灰岩の山が連なる中国南部の景観です。' },
  { title: '九寨溝', country: '中国', lat: 33.2600, lng: 103.9180, zoom: 11, category: '湖沼', wikiTitle: 'Jiuzhaigou', note: '青い湖と滝、森が連なる四川省の景勝地です。' },
  { title: '黄山', country: '中国', lat: 30.1320, lng: 118.1660, zoom: 12, category: '山岳', wikiTitle: 'Huangshan', note: '奇松、雲海、花崗岩の峰で知られる中国の名山です。' },
  { title: '万里の長城 八達嶺', country: '中国', lat: 40.3599, lng: 116.0200, zoom: 13, category: '城壁', wikiTitle: 'Great_Wall_of_China', note: '山稜に沿って長く続く巨大な城壁景観です。' },
  { title: 'アンコール・ワット', country: 'カンボジア', lat: 13.4125, lng: 103.8670, zoom: 14, category: '遺跡', wikiTitle: 'Angkor_Wat', note: '水濠と伽藍が整然と配置されたクメール建築の大遺跡です。' },
  { title: 'バガン', country: 'ミャンマー', lat: 21.1717, lng: 94.8585, zoom: 13, category: '仏塔群', wikiTitle: 'Bagan', note: '平原に無数の仏塔が点在する、ミャンマーの文化景観です。' },
  { title: 'タージ・マハル', country: 'インド', lat: 27.1751, lng: 78.0421, zoom: 15, category: '建築', wikiTitle: 'Taj_Mahal', note: '白い大理石の廟と庭園が軸線上に配置された名建築です。' },
  { title: 'ラダック', country: 'インド', lat: 34.1526, lng: 77.5771, zoom: 8, category: '高地', wikiTitle: 'Ladakh', note: 'ヒマラヤ北側の乾いた高地。谷と僧院が点在します。' },
  { title: 'ゴールデン・テンプル', country: 'インド', lat: 31.6200, lng: 74.8765, zoom: 15, category: '寺院', wikiTitle: 'Golden_Temple', note: '水面に囲まれた黄金の寺院が輝くアムリトサルの聖地です。' },
  { title: 'エベレスト', country: 'ネパール / 中国', lat: 27.9881, lng: 86.9250, zoom: 10, category: '山岳', wikiTitle: 'Mount_Everest', note: '世界最高峰。ヒマラヤの巨大な山脈地形が広がります。' },
  { title: 'ポカラ', country: 'ネパール', lat: 28.2096, lng: 83.9856, zoom: 12, category: '湖と山', wikiTitle: 'Pokhara', note: '湖の背後にアンナプルナ山群が見えるネパールの景観地です。' },
  { title: 'ブータン パロ・タクツァン', country: 'ブータン', lat: 27.4915, lng: 89.3638, zoom: 15, category: '寺院', wikiTitle: 'Paro_Taktsang', note: '断崖に張り付くように建つ、ブータンを象徴する僧院です。' },
  { title: 'モルディブ', country: 'モルディブ', lat: 3.2028, lng: 73.2207, zoom: 6, category: '環礁', wikiTitle: 'Maldives', note: 'インド洋に環礁が連なる、青い海の景観です。' },
  { title: 'ラジャ・アンパット', country: 'インドネシア', lat: -0.2346, lng: 130.5279, zoom: 8, category: '諸島', wikiTitle: 'Raja_Ampat_Islands', note: '小島と珊瑚礁が密集する、インドネシア東部の海域です。' },
  { title: 'ボロブドゥール', country: 'インドネシア', lat: -7.6079, lng: 110.2038, zoom: 15, category: '寺院遺跡', wikiTitle: 'Borobudur', note: '火山地帯に立つ巨大な仏教遺跡。幾何学的な構造が特徴です。' },
  { title: 'コミノ島 ブルーラグーン', country: 'マルタ', lat: 36.0131, lng: 14.3236, zoom: 15, category: '海', wikiTitle: 'Blue_Lagoon_(Malta)', note: '浅い海の透明な青が際立つ、マルタ近海の景観です。' },
  { title: 'セーシェル ラ・ディーグ', country: 'セーシェル', lat: -4.3591, lng: 55.8412, zoom: 13, category: '島', wikiTitle: 'La_Digue', note: '花崗岩の巨石と白砂の海岸で知られるインド洋の島です。' },
  { title: 'ソコトラ島', country: 'イエメン', lat: 12.4634, lng: 53.8237, zoom: 9, category: '島', wikiTitle: 'Socotra', note: '独特な植物相と乾いた地形が広がる、孤立した島の景観です。' },
  { title: 'ドバイ パーム・ジュメイラ', country: 'アラブ首長国連邦', lat: 25.1124, lng: 55.1390, zoom: 13, category: '人工島', wikiTitle: 'Palm_Jumeirah', note: '椰子の形をした人工島。空から見て分かりやすい都市景観です。' },
  { title: 'シンガポール マリーナベイ', country: 'シンガポール', lat: 1.2834, lng: 103.8607, zoom: 14, category: '都市景観', wikiTitle: 'Marina_Bay,_Singapore', note: '湾を囲む高層建築と緑が組み合わさった都市景観です。' },
  { title: '香港 ヴィクトリア・ハーバー', country: '香港', lat: 22.2940, lng: 114.1698, zoom: 13, category: '都市湾', wikiTitle: 'Victoria_Harbour', note: '高層都市と港が近接する、アジアを代表する都市景観です。' },
  { title: '東京スカイツリー', country: '日本', lat: 35.7101, lng: 139.8107, zoom: 15, category: '都市景観', wikiTitle: 'Tokyo_Skytree', note: '東京東部に立つ電波塔。都市密度の高さも地図上で分かります。' },
  { title: '京都 嵐山', country: '日本', lat: 35.0094, lng: 135.6668, zoom: 14, category: '渓谷と寺社', wikiTitle: 'Arashiyama', note: '川、山、寺社、竹林が近接する京都西部の景観地です。' },
  { title: '屋久島', country: '日本', lat: 30.3588, lng: 130.5281, zoom: 11, category: '森林島', wikiTitle: 'Yakushima', note: '深い森と山岳が島全体に広がる、雨の多い自然景観です。' },
  { title: '白川郷', country: '日本', lat: 36.2578, lng: 136.9067, zoom: 14, category: '集落', wikiTitle: 'Shirakawa-gō_and_Gokayama', note: '合掌造りの家並みと山里が残る、日本の伝統的な集落景観です。' },
  { title: '宮島 厳島神社', country: '日本', lat: 34.2959, lng: 132.3199, zoom: 14, category: '社寺と海', wikiTitle: 'Itsukushima_Shrine', note: '海上の鳥居と山を背景にした、瀬戸内海の象徴的な景観です。' },
  { title: '済州島 城山日出峰', country: '韓国', lat: 33.4580, lng: 126.9424, zoom: 13, category: '火山地形', wikiTitle: 'Seongsan_Ilchulbong', note: '海沿いに立つ火山性の凝灰丘。上から見ると円形の地形が分かります。' },
  { title: '台湾 太魯閣峡谷', country: '台湾', lat: 24.1587, lng: 121.6216, zoom: 12, category: '峡谷', wikiTitle: 'Taroko_National_Park', note: '大理石の峡谷と急峻な山地が連なる台湾東部の景観です。' },
  { title: 'フィリピン エルニド', country: 'フィリピン', lat: 11.1956, lng: 119.4075, zoom: 12, category: '海と島', wikiTitle: 'El_Nido,_Palawan', note: '石灰岩の島々とラグーンが連なるパラワン島北部の景観です。' },
  { title: 'ボホール チョコレートヒルズ', country: 'フィリピン', lat: 9.8297, lng: 124.1397, zoom: 12, category: '丘陵', wikiTitle: 'Chocolate_Hills', note: '丸い丘が多数並ぶ、ボホール島の独特な地形です。' },
  { title: 'ボラボラ島', country: 'フランス領ポリネシア', lat: -16.5004, lng: -151.7415, zoom: 12, category: '環礁', wikiTitle: 'Bora_Bora', note: 'ラグーンと山が組み合わさった南太平洋の島景観です。' },
  { title: 'タヒチ', country: 'フランス領ポリネシア', lat: -17.6509, lng: -149.4260, zoom: 10, category: '島', wikiTitle: 'Tahiti', note: '火山島の山地と珊瑚礁の海が広がる南太平洋の島です。' },
  { title: 'フィジー ママヌザ諸島', country: 'フィジー', lat: -17.6775, lng: 177.1050, zoom: 10, category: '諸島', wikiTitle: 'Mamanuca_Islands', note: '小さな島と青い海が連なる、フィジー西部のリゾート景観です。' },
  { title: 'グリーンランド イルリサット', country: 'グリーンランド', lat: 69.2198, lng: -51.0986, zoom: 11, category: '氷山', wikiTitle: 'Ilulissat_Icefjord', note: '氷河から生まれた氷山が海へ流れ出す北極圏の景観です。' },
  { title: 'スヴァールバル', country: 'ノルウェー', lat: 78.2232, lng: 15.6267, zoom: 6, category: '北極圏', wikiTitle: 'Svalbard', note: '氷河と山、フィヨルドが広がる北極圏の群島です。' },
  { title: '南極半島', country: '南極', lat: -64.0000, lng: -60.0000, zoom: 5, category: '氷雪', wikiTitle: 'Antarctic_Peninsula', note: '氷河と海氷、山が連なる南極で比較的アクセスされる地域です。' },
  { title: 'ロス棚氷', country: '南極', lat: -81.5000, lng: -175.0000, zoom: 4, category: '棚氷', wikiTitle: 'Ross_Ice_Shelf', note: '巨大な氷の平原が海へ張り出す、南極の圧倒的な地形です。' },
);

class HelloWorldScenery {
  constructor() {
    this.mapSlots = [];
    this.activeMapIndex = 0;
    this.currentIndex = -1;
    this.history = [];
    this.randomQueue = [];
    this.autoEnabled = true;
    this.autoTimer = null;
    this.progressTimer = null;
    this.mapReadyPromise = Promise.resolve();
    this.mapRequestId = 0;
    this.progressStartedAt = 0;
    this.photoRequestId = 0;
    this.photoCache = new Map();

    this.titleEl = document.getElementById('place-title');
    this.locationEl = document.getElementById('place-location');
    this.noteEl = document.getElementById('place-note');
    this.categoryEl = document.getElementById('place-category');
    this.coordsEl = document.getElementById('place-coords');
    this.historyEl = document.getElementById('history-list');
    this.progressEl = document.getElementById('auto-progress');
    this.nextBtn = document.getElementById('next-btn');
    this.prevBtn = document.getElementById('prev-btn');
    this.autoBtn = document.getElementById('auto-btn');
    this.fullscreenBtn = document.getElementById('fullscreen-btn');
    this.photoLayer = document.getElementById('photo-layer');
    this.photoCredit = document.getElementById('photo-credit');
    this.appShell = document.querySelector('.app-shell');

    this.initMap();
    this.bindEvents();
    this.goRandom(true);
    this.setAuto(true);
  }

  initMap() {
    this.mapSlots = ['map-a', 'map-b'].map((id) => ({
      element: document.getElementById(id),
    }));
    // 初期状態：両方非表示
    this.mapSlots.forEach((s) => {
      s.element.style.opacity = '0';
      s.element.style.zIndex = '1';
    });
  }

  buildMapUrl(place, zoom) {
    return `https://maps.google.com/maps?q=${place.lat},${place.lng}&z=${zoom}&t=h&output=embed`;
  }

  countryZoom(place) {
    // 目的地の国レベルズーム（上位概観）
    return Math.min(5, Math.max(2, place.zoom - 4));
  }

  bindEvents() {
    this.nextBtn.addEventListener('click', () => {
      this.goRandom(false);
      this.restartAutoIfNeeded();
    });
    this.prevBtn.addEventListener('click', () => {
      this.goPrevious();
      this.restartAutoIfNeeded();
    });
    this.autoBtn.addEventListener('click', () => this.setAuto(!this.autoEnabled));
    this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    window.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowRight' || event.key === ' ') {
        event.preventDefault();
        this.goRandom(false);
        this.restartAutoIfNeeded();
      }
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        this.goPrevious();
        this.restartAutoIfNeeded();
      }
    });
  }

  goRandom(initial = false) {
    const nextIndex = this.takeRandomIndex(initial);
    this.showPlace(nextIndex, true);
  }

  takeRandomIndex(initial = false) {
    if (places.length <= 1) return 0;
    if (this.randomQueue.length === 0) this.refillRandomQueue(initial);
    return this.randomQueue.pop();
  }

  refillRandomQueue(initial = false) {
    this.randomQueue = places
      .map((_, index) => index)
      .filter((index) => initial || index !== this.currentIndex);

    for (let i = this.randomQueue.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.randomQueue[i], this.randomQueue[j]] = [this.randomQueue[j], this.randomQueue[i]];
    }
  }

  goPrevious() {
    if (this.history.length < 2) return;
    this.history.pop();
    const previousIndex = this.history.pop();
    this.showPlace(previousIndex, false);
  }

  showPlace(index, addToHistory) {
    const place = places[index];
    if (!place) return;
    this.currentIndex = index;
    if (addToHistory) this.history.push(index);
    if (this.history.length > 12) this.history = this.history.slice(-12);

    this.titleEl.textContent = `${place.title} / ${place.country}`;
    this.locationEl.textContent = `${place.country}`;
    this.noteEl.textContent = place.note;
    this.categoryEl.textContent = place.category;
    this.coordsEl.textContent = `${place.lat.toFixed(4)}, ${place.lng.toFixed(4)}`;

    this.appShell.classList.add('is-traveling');
    this.mapReadyPromise = this.revealLoadedMap(place);
    this.loadPhoto(place);
    this.renderHistory();
  }

  async loadPhoto(place) {
    const requestId = ++this.photoRequestId;
    this.photoLayer.classList.remove('visible');
    this.appShell.classList.remove('photo-active');
    this.photoCredit.textContent = 'Photo: loading...';

    const cached = this.photoCache.get(place.wikiTitle);
    if (cached) {
      this.applyPhoto(cached, requestId, place);
      return;
    }

    try {
      const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(place.wikiTitle)}`;
      const response = await fetch(url, { headers: { accept: 'application/json' } });
      if (!response.ok) throw new Error(`photo fetch failed: ${response.status}`);
      const data = await response.json();
      const source = data?.originalimage?.source || data?.thumbnail?.source;
      if (!source) throw new Error('photo not found');
      const photo = {
        url: source,
        credit: `Photo: Wikipedia / Wikimedia Commons - ${data.title || place.title}`,
      };
      this.photoCache.set(place.wikiTitle, photo);
      this.applyPhoto(photo, requestId, place);
    } catch (error) {
      if (requestId !== this.photoRequestId) return;
      this.photoLayer.style.backgroundImage = '';
      this.photoLayer.classList.remove('visible');
      this.appShell.classList.remove('photo-active');
      this.photoCredit.textContent = 'Photo: unavailable';
      console.warn(error);
    }
  }

  applyPhoto(photo, requestId, place) {
    if (requestId !== this.photoRequestId) return;
    const image = new Image();
    image.onload = async () => {
      if (requestId !== this.photoRequestId) return;
      const mapReady = await this.mapReadyPromise;
      if (!mapReady) return;
      if (requestId !== this.photoRequestId) return;
      this.photoLayer.style.backgroundImage = `url("${photo.url}")`;
      this.photoLayer.classList.add('visible');
      this.appShell.classList.add('photo-active');
      this.photoCredit.textContent = photo.credit;
      this.titleEl.textContent = place.title;
    };
    image.onerror = () => {
      if (requestId !== this.photoRequestId) return;
      this.photoCredit.textContent = 'Photo: unavailable';
      this.photoLayer.classList.remove('visible');
      this.appShell.classList.remove('photo-active');
    };
    image.src = photo.url;
  }

  async toggleFullscreen() {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
        this.fullscreenBtn.textContent = '全画面';
      } else {
        await document.documentElement.requestFullscreen();
        this.fullscreenBtn.textContent = '全画面解除';
      }
    } catch (error) {
      console.warn(error);
    }
  }

  // エレメントを即座に指定スタイルへスナップしてからトランジション開始
  snapThenAnimate(el, snapStyles, animateStyles, transition) {
    el.style.transition = 'none';
    Object.assign(el.style, snapStyles);
    void el.offsetWidth;
    el.style.transition = transition;
    Object.assign(el.style, animateStyles);
  }

  async revealLoadedMap(place) {
    const requestId = ++this.mapRequestId;
    const activeIdx = this.activeMapIndex;
    const activeEl = this.mapSlots[activeIdx].element;
    const nextIdx = 1 - activeIdx;
    const nextEl = this.mapSlots[nextIdx].element;

    // ── Phase 1: 国レベル表示（nextEl） ──
    nextEl.src = this.buildMapUrl(place, this.countryZoom(place));
    await this.waitForFrameReady(nextEl, 8000);
    if (requestId !== this.mapRequestId) return false;

    // 旧アクティブをフェードアウト
    activeEl.style.transition = 'opacity 0.8s ease';
    activeEl.style.zIndex = '1';
    activeEl.style.opacity = '0';

    // 国レベルフレームをスナップ→フェードイン＋スケールイン
    this.snapThenAnimate(
      nextEl,
      { opacity: '0', transform: 'scale(1.1)', zIndex: '3' },
      { opacity: '1', transform: 'scale(1)' },
      'opacity 1.2s ease, transform 3.5s ease'
    );

    await this.wait(COUNTRY_HOLD_MS);
    if (requestId !== this.mapRequestId) return false;

    // ── Phase 2: 地区レベル表示（activeEl を再利用） ──
    activeEl.src = this.buildMapUrl(place, place.zoom);
    await this.waitForFrameReady(activeEl, 8000);
    if (requestId !== this.mapRequestId) return false;

    // 国レベルフレームをフェードアウト
    nextEl.style.transition = 'opacity 0.8s ease';
    nextEl.style.opacity = '0';

    // 地区レベルフレームをスナップ→フェードイン＋スケールイン
    this.snapThenAnimate(
      activeEl,
      { opacity: '0', transform: 'scale(1.07)', zIndex: '4' },
      { opacity: '1', transform: 'scale(1)' },
      'opacity 1.2s ease, transform 4.5s ease'
    );

    this.appShell.classList.remove('is-traveling');

    // photo 許可まで少し待つ（地区フレームが見え始めてから）
    await this.wait(LOCAL_REVEAL_MS);
    if (requestId !== this.mapRequestId) return false;

    // 落ち着いたら CSS クラスで管理（photo-active 時の opacity 制御に必要）
    const snap = requestId;
    this.wait(3000).then(() => {
      if (snap !== this.mapRequestId) return;
      activeEl.style.transition = 'none';
      Object.assign(activeEl.style, { opacity: '', transform: '', zIndex: '' });
      activeEl.className = 'world-map is-active';
      nextEl.style.transition = '';
      Object.assign(nextEl.style, { opacity: '', transform: '', zIndex: '' });
      nextEl.className = 'world-map';
      void activeEl.offsetWidth;
    });

    return true;
  }

  wait(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  waitForFrameReady(frame, timeoutMs) {
    return new Promise((resolve) => {
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        frame.removeEventListener('load', finish);
        window.setTimeout(resolve, 200);
      };
      frame.addEventListener('load', finish, { once: true });
      window.setTimeout(finish, timeoutMs);
    });
  }

  renderHistory() {
    this.historyEl.innerHTML = '';
    this.history.slice(-3).reverse().forEach((index) => {
      const place = places[index];
      const item = document.createElement('li');
      item.textContent = `${place.title} / ${place.country}`;
      this.historyEl.appendChild(item);
    });
  }

  setAuto(enabled) {
    this.autoEnabled = enabled;
    this.autoBtn.classList.toggle('active', enabled);
    this.autoBtn.textContent = enabled ? '自動巡回 ON' : '自動巡回 OFF';
    this.clearAutoTimers();
    if (enabled) this.scheduleAuto();
    else this.progressEl.style.width = '0%';
  }

  restartAutoIfNeeded() {
    if (!this.autoEnabled) return;
    this.clearAutoTimers();
    this.scheduleAuto();
  }

  scheduleAuto() {
    this.progressStartedAt = performance.now();
    this.autoTimer = window.setTimeout(() => {
      this.goRandom(false);
      this.scheduleAuto();
    }, AUTO_INTERVAL_MS);
    this.progressTimer = window.setInterval(() => {
      const elapsed = performance.now() - this.progressStartedAt;
      const percent = Math.min(100, (elapsed / AUTO_INTERVAL_MS) * 100);
      this.progressEl.style.width = `${percent}%`;
    }, 100);
  }

  clearAutoTimers() {
    if (this.autoTimer) {
      window.clearTimeout(this.autoTimer);
      this.autoTimer = null;
    }
    if (this.progressTimer) {
      window.clearInterval(this.progressTimer);
      this.progressTimer = null;
    }
    this.progressEl.style.width = '0%';
  }
}

window.addEventListener('DOMContentLoaded', () => {
  new HelloWorldScenery();
});
