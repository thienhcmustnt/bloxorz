/** Client state machine and API orchestration. Server owns every game transition. */
import { AnimationQueue } from "./scene/AnimationQueue.js";
import { SceneManager } from "./scene/SceneManager.js";
import { BlockAnimator } from "./scene/BlockAnimator.js";
import { TileFX } from "./scene/TileFX.js";
import { TransitionManager } from "./scene/TransitionManager.js";
import { UI } from "./ui/UI.js";
const TRANSITIONS = {
  LOADING: ["INTRO"],
  INTRO: ["IDLE"],
  IDLE: ["ANIMATING", "SOLVING", "REPLAY"],
  ANIMATING: ["IDLE", "LOSE_FX", "WIN_FX"],
  LOSE_FX: ["INTRO"],
  WIN_FX: ["OUTRO", "IDLE"],
  OUTRO: ["INTRO"],
  SOLVING: ["IDLE", "REPLAY"],
  REPLAY: ["IDLE", "WIN_FX", "LOSE_FX"],
};
export class GameController {
  constructor() {
    this.debug = new URLSearchParams(location.search).get("debug") === "1";
    this.mode = "LOADING";
    this.epoch = 0;
    this.moves = 0;
    this.seq = 0;
    this.state = null;
    this.status = "PLAYING";
    this.buffer = null;
    this.holdTerminal = false;
    this.queue = new AnimationQueue();
    this.scene = new SceneManager(
      document.querySelector("#stage"),
      this.queue,
      this.debug,
    );
    this.fx = new TileFX(this.scene, this.queue);
    this.transitions = new TransitionManager(this.scene, this.queue);
    this.ui = new UI();
    this.ui.bind(this);
    this.scene.follow = () => this.block?.center();
    this.scene.onFrame = () => {
      if (this.debug) {
        const d = document.querySelector("#debug");
        d.hidden = false;
        d.textContent = JSON.stringify(
          {
            mode: this.mode,
            status: this.status,
            orientation: this.state?.orientation,
            cubes: this.state?.cubes,
            active: this.state?.active,
            bridges: this.state?.bridges,
            FPS: Math.round(this.scene.fps),
          },
          null,
          2,
        );
      }
    };
  }
  setMode(next) {
    if (
      next !== this.mode &&
      next !== "LOADING" &&
      !TRANSITIONS[this.mode]?.includes(next)
    )
      throw Error(`Invalid mode ${this.mode} → ${next}`);
    this.mode = next;
    this.ui.update();
  }
  async request(path, body) {
    const abort = new AbortController();
    const timeout = setTimeout(
      () => abort.abort(),
      path === "/api/solve" ? 245000 : 15000,
    );
    try {
      const response = await fetch(path, {
        method: body ? "POST" : "GET",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
        signal: abort.signal,
      });
      const data = await response.json();
      if (!response.ok) {
        const error = Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail),
        );
        error.status = response.status;
        throw error;
      }
      return data;
    } finally {
      clearTimeout(timeout);
    }
  }
  async init() {
    try {
      const catalog = await this.request("/api/levels");
      this.boards = new Map(
        await Promise.all(
          catalog.map(async (l) => [
            l.id,
            await this.request(`/api/levels/${l.id}`),
          ]),
        ),
      );
      this.ui.catalog(catalog, this.boards);
      await this.load(1);
      this.ui.showWelcome();
    } catch (error) {
      this.ui.toast(`Could not load game: ${error.message}. Reload to retry.`);
    }
  }
  async load(id, { restart = false } = {}) {
    const previousMode = this.mode;
    const token = ++this.epoch;
    this.queue.cancel();
    this.buffer = null;
    this.replayData = null;
    this.replayBusy = false;
    document.querySelector("#replay").hidden = true;
    this.setMode("LOADING");
    try {
      const data = await this.request(
        restart && previousMode === "IDLE"
          ? "/api/game/restart"
          : "/api/game/new",
        restart && previousMode === "IDLE"
          ? { session_id: this.session }
          : { level_id: id },
      );
      if (token !== this.epoch) return;
      this.level = this.boards.get(id);
      this.session = data.session_id;
      this.seq = data.seq;
      this.moves = data.moves;
      this.state = data.state;
      this.status = data.status;
      this.scene.root.position.y = 0;
      this.scene.build(this.level, this.state);
      this.block = new BlockAnimator(this.scene, this.queue);
      this.block.snap(this.state);
      this.ui.level(this.level);
      this.setMode("INTRO");
      await this.transitions.intro(this.block, this.level.name);
      if (token !== this.epoch) return;
      this.block.snap(this.state);
      this.setMode("IDLE");
      this.verify();
    } catch (error) {
      if (token === this.epoch) {
        if (error.status === 404 && restart) return this.load(id);
        this.ui.toast(
          `Connection problem: ${error.message}. Press Restart to retry.`,
        );
      }
    }
  }
  input(action) {
    if (action === "SWAP" && !this.state?.split) return;
    if (this.mode === "ANIMATING") {
      if (!this.buffer) this.buffer = action;
      return;
    }
    if (this.mode !== "IDLE" || this.status !== "PLAYING") return;
    void this.move(action);
  }
  async event(event) {
    const token = this.epoch;
    switch (event.type) {
      case "roll":
        await this.block.roll(event);
        if (token !== this.epoch) return;
        await this.fx.landing(event);
        this.ui.beep();
        break;
      case "switch_pressed":
        await this.fx.press(event);
        break;
      case "bridge_changed":
        await this.fx.bridge(event);
        break;
      case "split":
        await this.block.splitEvent(event);
        break;
      case "merge":
        await this.block.mergeEvent(event);
        break;
      case "swap":
        await this.block.swapEvent(event);
        break;
      case "fragile_break":
        await this.fx.fragile(event);
        if (token !== this.epoch) return;
        await this.block.fall();
        break;
      case "fall":
        await this.block.fall();
        break;
      case "win":
        await Promise.all([
          this.block.win(),
          this.fx.ripple(event.cell),
          this.queue.tween(this.scene.light, {
            intensity: 5,
            duration: 0.12,
            yoyo: true,
            repeat: 1,
          }),
        ]);
        break;
    }
  }
  async move(action, replay = false) {
    if (
      (!replay && this.mode !== "IDLE") ||
      (replay && this.mode !== "REPLAY") ||
      this.status !== "PLAYING"
    )
      return;
    const token = this.epoch;
    if (!replay) this.setMode("ANIMATING");
    try {
      const result = await this.request("/api/game/move", {
        session_id: this.session,
        action,
        seq: this.seq + 1,
      });
      if (token !== this.epoch) return;
      this.seq = result.seq;
      this.moves = result.moves;
      this.status = result.status;
      this.lastResult = result;
      this.ui.update();
      if (
        !(await this.queue.play(result.events, (e) => this.event(e))) ||
        token !== this.epoch
      )
        return;
      if (result.state) {
        this.state = result.state;
        if (result.status !== "WON") {
          this.block.snap(this.state);
          this.scene.syncBridges(this.state);
          this.verify();
        }
      }
      if (result.status === "LOST") {
        this.setMode("LOSE_FX");
        this.buffer = null;
        if (!this.holdTerminal) await this.load(this.level.id);
        return;
      }
      if (result.status === "WON") {
        this.ui.complete(this.level.id);
        this.setMode("WIN_FX");
        this.buffer = null;
        if (this.holdTerminal) return;
        if (replay) {
          this.setMode("IDLE");
          this.ui.toast("Solution complete. Restart or choose the next level.");
          return;
        }
        this.setMode("OUTRO");
        await this.transitions.outro();
        if (token !== this.epoch) return;
        if (this.level.id === 15) {
          this.ui.toast("All fifteen worlds complete.");
          await this.load(1);
          this.ui.showLevels();
        } else await this.load(this.level.id + 1);
        return;
      }
      if (!replay) {
        this.setMode("IDLE");
        const buffered = this.buffer;
        this.buffer = null;
        if (buffered) void this.move(buffered);
      }
    } catch (error) {
      if (token !== this.epoch) return;
      if (error.status === 404) {
        this.ui.toast("Session restored after server restart.");
        await this.load(this.level.id);
      } else {
        this.ui.toast(error.message);
        await this.load(this.level.id);
      }
    }
  }
  verify() {
    if (
      this.debug &&
      this.status === "PLAYING" &&
      !this.block.check(this.state)
    )
      console.error("Pose mismatch", this.state);
  }
  async restart() {
    await this.load(this.level?.id || 1, { restart: true });
  }
  async undo() {
    if (!this.moves) return;
    const token = ++this.epoch;
    this.queue.cancel();
    this.buffer = null;
    this.replayData = null;
    document.querySelector("#replay").hidden = true;
    this.setMode("LOADING");
    try {
      const data = await this.request("/api/game/undo", {
        session_id: this.session,
      });
      if (token !== this.epoch) return;
      this.state = data.state;
      this.status = data.status;
      this.seq = data.seq;
      this.moves = data.moves;
      this.scene.root.position.y = 0;
      this.scene.build(this.level, this.state);
      this.block = new BlockAnimator(this.scene, this.queue);
      this.block.snap(this.state);
      this.setMode("INTRO");
      this.setMode("IDLE");
      this.verify();
    } catch (error) {
      if (token === this.epoch) {
        this.ui.toast(error.message);
        await this.load(this.level.id);
      }
    }
  }
  async solve(algo, heuristic) {
    if (this.mode !== "IDLE" || this.status !== "PLAYING") return;
    const token = this.epoch;
    this.buffer = null;
    this.setMode("SOLVING");
    try {
      const result = await this.request("/api/solve", {
        session_id: this.session,
        algo,
        heuristic: algo === "astar" ? heuristic : null,
        timeout: 30,
      });
      if (token !== this.epoch) return;
      this.ui.metrics(result, algo, heuristic);
      if (!result.found) {
        this.setMode("IDLE");
        return;
      }
      this.beginReplay(result.path);
    } catch (error) {
      if (token !== this.epoch) return;
      if (error.status === 404) await this.load(this.level.id);
      else {
        this.ui.toast(error.message);
        this.setMode("IDLE");
      }
    }
  }
  beginReplay(path) {
    this.replayData = { path, index: 0, paused: false };
    this.setMode("REPLAY");
    this.ui.replay(path, 0, false);
    void this.replayLoop();
  }
  async replayLoop(single = false) {
    if (this.replayBusy || this.mode !== "REPLAY" || !this.replayData) return;
    this.replayBusy = true;
    const token = this.epoch;
    const data = this.replayData;
    try {
      while (
        token === this.epoch &&
        this.mode === "REPLAY" &&
        data.index < data.path.length &&
        (!data.paused || single)
      ) {
        await this.move(data.path[data.index], true);
        if (token !== this.epoch) return;
        data.index++;
        this.ui.replay(data.path, data.index, data.paused);
        if (single) break;
      }
      if (
        token === this.epoch &&
        data.index === data.path.length &&
        this.mode === "REPLAY"
      )
        this.setMode("IDLE");
    } finally {
      if (token === this.epoch) this.replayBusy = false;
    }
  }
  pauseReplay() {
    if (!this.replayData) return;
    this.replayData.paused = !this.replayData.paused;
    this.ui.replay(
      this.replayData.path,
      this.replayData.index,
      this.replayData.paused,
    );
    if (!this.replayData.paused) void this.replayLoop();
  }
  stepReplay() {
    if (!this.replayData) return;
    this.replayData.paused = true;
    void this.replayLoop(true);
  }
  async stopReplay() {
    const data = this.replayData;
    if (!data) return;
    data.paused = true;
    while (this.replayBusy) await new Promise((r) => setTimeout(r, 15));
    if (this.replayData !== data) return;
    this.replayData = null;
    document.querySelector("#replay").hidden = true;
    if (["REPLAY", "WIN_FX"].includes(this.mode)) this.setMode("IDLE");
  }
}
