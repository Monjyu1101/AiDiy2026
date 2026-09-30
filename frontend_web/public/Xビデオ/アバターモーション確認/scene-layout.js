const scene = window.MOTION_SCENES.find(item => item.id === window.MOTION_SCENE_ID);
if (!scene) {
  document.body.textContent = "シーンが見つかりません。";
} else {
  const title = document.createElement("h1");
  title.textContent = scene.title;
  const number = document.createElement("div");
  number.className = "scene-number";
  number.textContent = scene.number;
  const description = document.createElement("p");
  description.className = "scene-description";
  description.textContent = scene.description;
  const note = document.createElement("p");
  note.className = "scene-note";
  note.textContent = scene.file
    ? "左のアバターを見て、腕・手・首の位置と待機中の揺れを確認してください。"
    : "前へ戻るか、下の一覧から任意のモーションを選べます。";
  const card = document.createElement("main");
  card.className = "scene-card";
  card.append(number, title, description, note);
  document.body.append(card);
}
document.addEventListener("keydown", event => {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  event.preventDefault();
  window.parent.postMessage({ type: "avatar-motion-page", direction: event.key === "ArrowRight" ? 1 : -1 }, window.location.origin);
});
