/** Staggered tile arrival/collapse. Every tween belongs to AnimationQueue. */
import * as THREE from "three";
export class TransitionManager {
  constructor(scene, queue) {
    this.scene = scene;
    this.queue = queue;
  }
  async tiles(arriving) {
    const floor = this.scene.floorMesh,
      cells = this.scene.normalCells;
    const start = this.scene.level.grid
      .flatMap((row, r) =>
        [...row].map((ch, c) =>
          this.scene.level.legend[ch] === "start" ? [r, c] : null,
        ),
      )
      .find(Boolean);
    const special = this.scene.tiles.map((mesh) => ({
      mesh,
      y: mesh.position.y,
    }));
    const animation = { t: 0 },
      matrix = new THREE.Matrix4();
    const offset = (r, c) => {
      const delay = Math.min(
        0.4,
        Math.hypot(r - start[0], c - start[1]) * 0.025,
      );
      const p = Math.min(1, Math.max(0, (animation.t - delay) / 0.6));
      return arriving ? 3 * (1 - p) ** 2 : -4 * p * p;
    };
    const update = () => {
      cells.forEach(([r, c], i) => {
        matrix.makeTranslation(c, offset(r, c), r);
        floor.setMatrixAt(i, matrix);
      });
      floor.instanceMatrix.needsUpdate = true;
      special.forEach(({ mesh, y }) => {
        mesh.position.y = y + offset(...mesh.userData.cell);
      });
    };
    update();
    await this.queue.tween(animation, {
      t: 1,
      duration: arriving ? 0.65 : 0.45,
      onUpdate: update,
      ease: "none",
    });
  }
  async intro(block, name) {
    const token = this.queue.generation,
      banner = document.querySelector("#level-banner");
    this.scene.rig.reveal = 1.08;
    this.scene.rig.yawOffset = 0.06;
    banner.textContent = name;
    banner.style.opacity = 0;
    block.meshes.forEach((mesh) => (mesh.position.y += 3));
    await Promise.all([
      this.tiles(true),
      this.queue.tween(this.scene.rig, {
        reveal: 1,
        yawOffset: 0,
        duration: 0.65,
        ease: "power2.inOut",
      }),
      this.queue.tween(banner, { opacity: 1, duration: 0.22 }),
    ]);
    if (token !== this.queue.generation) return;
    await Promise.all(
      block.meshes.map((mesh) =>
        this.queue.tween(mesh.position, {
          y: mesh.position.y - 3,
          duration: 0.25,
          ease: "power2.out",
        }),
      ),
    );
    if (token !== this.queue.generation) return;
    await this.queue.tween(banner, { opacity: 0, duration: 0.23 });
  }
  async outro() {
    await this.tiles(false);
  }
}
