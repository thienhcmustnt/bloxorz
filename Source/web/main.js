/** Bootstrap. Debug hooks are exposed only when explicitly requested. */
import { GameController } from "./GameController.js";
try {
  const game = new GameController();
  if (game.debug) window.__bloxorz = game;
  void game.init();
} catch (error) {
  document.querySelector("#context-error").hidden = false;
  document
    .querySelector("#context-error")
    .prepend(
      document.createTextNode(`Unable to initialize 3D: ${error.message}. `),
    );
}
