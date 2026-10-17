/** Level intro/outro share cancellable animation ownership with gameplay. */
import * as THREE from 'three';
export class TransitionManager{
 constructor(scene,queue){this.scene=scene;this.queue=queue;}
 async intro(block,name){const token=this.queue.generation;const banner=document.querySelector('#level-banner');banner.textContent=name;banner.style.opacity=0;const floor=this.scene.floorMesh,cells=this.scene.normalCells;const start=this.scene.level.grid.flatMap((row,r)=>[...row].map((ch,c)=>this.scene.level.legend[ch]==='start'?[r,c]:null)).find(Boolean);const animation={t:0};
 const update=()=>{const matrix=new THREE.Matrix4();cells.forEach(([r,c],i)=>{const delay=Math.min(.4,Math.hypot(r-start[0],c-start[1])*.025);const progress=Math.min(1,Math.max(0,(animation.t-delay)/.6));matrix.makeTranslation(c,-3*(1-progress)**2,r);floor.setMatrixAt(i,matrix);});floor.instanceMatrix.needsUpdate=true;};update();
 block.meshes.forEach(m=>m.position.y+=3);await Promise.all([this.queue.tween(animation,{t:1,duration:.65,onUpdate:update,ease:'none'}),this.queue.tween(banner,{opacity:1,duration:.22})]);if(token!==this.queue.generation)return;
 await Promise.all(block.meshes.map(m=>this.queue.tween(m.position,{y:m.position.y-3,duration:.25,ease:'power2.out'})));if(token!==this.queue.generation)return;await this.queue.tween(banner,{opacity:0,duration:.23});
 }
 async outro(){const token=this.queue.generation;const root=this.scene.root;await this.queue.tween(root.position,{y:-5,duration:.45,ease:'power2.in'});if(token===this.queue.generation)root.position.y=0;}
}
