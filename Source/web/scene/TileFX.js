/** Tile effects consume ordered server events and never decide tile behavior. */
import * as THREE from "three";
export class TileFX {
  constructor(scene, queue) {
    this.scene = scene;
    this.queue = queue;
  }
  async bridge(event) {
    const tiles = this.scene.bridgeMeshes.get(event.bridge_id) || [];
    await Promise.all(
      tiles.flatMap((tile) => {
        tile.traverse((o) => {
          if (o.material) {
            o.material.transparent = true;
          }
        });
        const fades = [];
        tile.traverse((o) => {
          if (o.material)
            fades.push(
              this.queue.tween(o.material, {
                opacity: event.open ? 1 : 0.16,
                duration: 0.24,
              }),
            );
        });
        return [
          this.queue.tween(tile.position, {
            y: event.open ? 0 : -0.65,
            duration: 0.24,
            ease: "power2.inOut",
          }),
          this.queue.tween(tile.scale, {
            x: event.open ? 1 : 0.72,
            y: event.open ? 1 : 0.72,
            z: event.open ? 1 : 0.72,
            duration: 0.24,
          }),
          ...fades,
        ];
      }),
    );
  }
  async press(event) {
    const token = this.queue.generation;
    const tile = this.scene.specials.get(event.cell.join(","));
    if (!tile) return;
    await this.queue.tween(tile.position, {
      y: -0.07,
      duration: 0.07,
      yoyo: true,
      repeat: 1,
    });
    if (token !== this.queue.generation) return;
    await this.ripple(event.cell);
  }
  async ripple(cell) {
    const ring = new THREE.Mesh(
      this.scene.own(new THREE.RingGeometry(0.2, 0.23, 32)),
      this.scene.own(
        new THREE.MeshBasicMaterial({
          color: 0x8aead6,
          transparent: true,
          opacity: 0.8,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      ),
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.set(cell[1], 0.03, cell[0]);
    this.scene.add(ring);
    await Promise.all([
      this.queue.tween(ring.scale, { x: 3, y: 3, duration: 0.18 }),
      this.queue.tween(ring.material, { opacity: 0, duration: 0.18 }),
    ]);
    this.scene.root.remove(ring);
    this.release(ring);
  }
  release(mesh) {
    this.scene.resources.delete(mesh.geometry);
    this.scene.resources.delete(mesh.material);
    mesh.geometry.dispose();
    mesh.material.dispose();
  }
  async fragile(event) {
    const token = this.queue.generation;
    const tile = this.scene.specials.get(event.cell.join(","));
    if (tile) {
      await this.queue.tween(tile.rotation, {
        z: 0.09,
        duration: 0.04,
        yoyo: true,
        repeat: 3,
      });
      if (token !== this.queue.generation) return;
      tile.visible = false;
    }
    const pieces = [];
    for (let i = 0; i < 6; i++) {
      const piece = new THREE.Mesh(
        this.scene.own(new THREE.BoxGeometry(0.24, 0.12, 0.24)),
        this.scene.own(new THREE.MeshStandardMaterial({ color: 0xbd874f })),
      );
      piece.position.set(
        event.cell[1] + ((i % 3) - 1) * 0.27,
        -0.02,
        event.cell[0] + (Math.floor(i / 3) - 0.5) * 0.3,
      );
      this.scene.add(piece);
      pieces.push(piece);
    }
    await Promise.all(
      pieces.map((m, i) =>
        this.queue.tween(m.position, {
          x: m.position.x + (i % 2 ? 0.3 : -0.3),
          y: -3,
          z: m.position.z + 0.3,
          duration: 0.36,
          ease: "power2.in",
        }),
      ),
    );
    pieces.forEach((m) => {
      this.scene.root.remove(m);
      this.release(m);
    });
  }
  async landing(event) {
    if (this.queue.reduced) return;
    const cell = event.to_cells[0];
    const particles = [];
    for (let i = 0; i < 4; i++) {
      const m = new THREE.Mesh(
        this.scene.own(new THREE.SphereGeometry(0.025, 4, 3)),
        this.scene.own(
          new THREE.MeshBasicMaterial({ color: 0xf1c17b, transparent: true }),
        ),
      );
      m.position.set(cell[1], 0.08, cell[0]);
      this.scene.add(m);
      particles.push(m);
    }
    await Promise.all(
      particles.flatMap((m, i) => [
        this.queue.tween(m.position, {
          x: m.position.x + Math.cos((i * Math.PI) / 2) * 0.7,
          z: m.position.z + Math.sin((i * Math.PI) / 2) * 0.7,
          y: 0.18,
          duration: 0.12,
        }),
        this.queue.tween(m.material, { opacity: 0, duration: 0.12 }),
      ]),
    );
    particles.forEach((m) => {
      this.scene.root.remove(m);
      this.release(m);
    });
  }
}
