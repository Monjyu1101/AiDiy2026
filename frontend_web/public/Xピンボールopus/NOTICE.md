# Xピンボールopus 外部ライブラリ

`game.js` は Three.js を 3D 描画エンジンとして利用します。ネットワークへアクセスせずに動作するよう、公開用モジュールをゲームと同じ配布物に同梱しています。

| 項目 | 内容 |
| --- | --- |
| ライブラリ | [Three.js](https://threejs.org/) |
| 固定版 | `0.178.0` |
| 配布元 | npm パッケージ [`three@0.178.0`](https://www.npmjs.com/package/three/v/0.178.0) の `build/three.module.js` / `build/three.core.js` |
| 配置先 | `vendor/three.module.js` / `vendor/three.core.js` |
| ライセンス | MIT License |
| 同梱ファイル SHA-256 | `three.module.js`: `BC0D236927F5163414E7C59A5567257DFE925F1929CE0A151AC4185DC45CA5A2`、`three.core.js`: `562B72799EF1145F77997ECE49A34F578422873757B0A13E41D76DCBFB776F06` |

`game.js` で使用する `WebGLRenderer`、`Scene`、`PerspectiveCamera`、各種 Geometry / Material、`SRGBColorSpace`、`ACESFilmicToneMapping`、`MathUtils` は Three.js `0.178.0` で提供される API です。

## ネットワーク制限時の挙動

Three.js の読込に外部 CDN は使用しません。`index.html`、`game.js`、`vendor/three.module.js`、`vendor/three.core.js` が同じ配布物に存在すれば、ネットワークを遮断した環境でも 3D ゲームを初期化できます。WebGL が無効、または同梱ファイルが破損・欠落した場合だけ、画面上に初期化エラーを表示します。

## MIT License

Copyright © 2010-2025 Three.js Authors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
