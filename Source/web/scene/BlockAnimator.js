/** Event-driven rigid-body animation. poseFromState is the only state-to-pose mapping. */
import * as THREE from 'three';
export function poseFromState(state){if(!state)return[];if(state.orientation==='split')return state.cubes.map(([r,c])=>({position:[c,.5,r],rotation:[0,0,0],scale:[1,1,1]}));
 const cells=state.cubes;const x=cells.reduce((s,c)=>s+c[1],0)/cells.length,z=cells.reduce((s,c)=>s+c[0],0)/cells.length;
 return[{position:[x,state.orientation==='standing'?1:.5,z],rotation:state.orientation==='lying_h'?[0,0,Math.PI/2]:state.orientation==='lying_v'?[Math.PI/2,0,0]:[0,0,0],scale:[1,1,1]}];}
export class BlockAnimator{
 constructor(scene,queue){this.scene=scene;this.queue=queue;this.meshes=[];this.group=new THREE.Group();scene.add(this.group);this.marker=null;}
 create(split){this.group.clear();this.meshes=[];
   const geo=this.scene.own(new THREE.BoxGeometry(.92,split?.92:1.92,.92));
   for(let i=0;i<(split?2:1);i++){const mat=this.scene.own(new THREE.MeshStandardMaterial({color:0xe8b267,roughness:.3,metalness:.48,transparent:true}));const mesh=new THREE.Mesh(geo,mat);mesh.castShadow=true;mesh.receiveShadow=true;this.group.add(mesh);this.meshes.push(mesh);
     const edges=new THREE.LineSegments(this.scene.own(new THREE.EdgesGeometry(geo)),this.scene.own(new THREE.LineBasicMaterial({color:0xffe0a6,transparent:true,opacity:.58})));mesh.add(edges);
     const stripe=new THREE.Mesh(this.scene.own(new THREE.BoxGeometry(.935,.045,.935)),this.scene.own(new THREE.MeshStandardMaterial({color:0x83562b,roughness:.5,metalness:.4})));mesh.add(stripe);
   }
   if(split){this.marker=new THREE.Mesh(this.scene.own(new THREE.ConeGeometry(.12,.23,4)),this.scene.own(new THREE.MeshBasicMaterial({color:0xa5fff0})));this.marker.rotation.z=Math.PI;this.group.add(this.marker);}else this.marker=null;
   this.split=split;
 }
 snap(state){if(!state)return;const poses=poseFromState(state);if(this.split!==state.split||this.meshes.length!==poses.length)this.create(state.split);
   poses.forEach((pose,i)=>{const mesh=this.meshes[i];this.group.attach(mesh);mesh.position.fromArray(pose.position);mesh.rotation.set(...pose.rotation);mesh.scale.set(1,1,1);mesh.material.opacity=1;});
   if(this.marker){this.marker.position.copy(this.meshes[state.active].position);this.marker.position.y=1.4;this.meshes.forEach((m,i)=>{m.material.emissive.setHex(i===state.active?0x28675c:0x000000);m.material.emissiveIntensity=.35;});}
   this.state=state;
 }
 center(){if(!this.meshes.length)return null;return this.meshes[this.state?.split?this.state.active:0].position;}
 async roll(event){const index=event.cube_index??0;const mesh=this.meshes[index];if(!mesh)return;
   const cells=event.cube_index===null?event.from_cells:[event.from_cells[index]];
   const minR=Math.min(...cells.map(c=>c[0])),maxR=Math.max(...cells.map(c=>c[0]));const minC=Math.min(...cells.map(c=>c[1])),maxC=Math.max(...cells.map(c=>c[1]));
   const pivot=new THREE.Group();const d=event.direction;const horizontal=d==='LEFT'||d==='RIGHT';
   pivot.position.set(horizontal?(d==='LEFT'?minC-.5:maxC+.5):(minC+maxC)/2,0,horizontal?(minR+maxR)/2:(d==='UP'?minR-.5:maxR+.5));this.group.add(pivot);pivot.attach(mesh);
   if(this.marker)this.marker.visible=false;
   const ok=await this.queue.tween(pivot.rotation,{[horizontal?'z':'x']:horizontal?(d==='LEFT'?Math.PI/2:-Math.PI/2):(d==='UP'?-Math.PI/2:Math.PI/2),duration:.28,ease:'power2.inOut'});
   if(!ok)return;this.group.attach(mesh);this.group.remove(pivot);
   // Destination event carries display orientation; no movement rules are inferred here.
   const display={cubes:event.to_cells,orientation:event.to_orientation,split:event.to_orientation==='split',active:index};
   const poses=poseFromState(display);const pose=poses[index];mesh.position.fromArray(pose.position);mesh.rotation.set(...pose.rotation);mesh.scale.set(1,1,1);
   if(this.marker)this.marker.visible=true;
   await this.queue.tween(mesh.scale,{y:.97,duration:.035,yoyo:true,repeat:1});
 }
 async splitEvent(event){const origin=this.meshes[0].position.clone();this.create(true);this.meshes.forEach(m=>m.position.copy(origin));await Promise.all(this.meshes.map((m,i)=>this.queue.tween(m.position,{x:event.to_cells[i][1],y:.5,z:event.to_cells[i][0],duration:.45,ease:'power2.inOut'})));}
 async mergeEvent(event){const state={cubes:event.cells,orientation:event.orientation,split:false,active:0};this.snap(state);await this.queue.tween(this.meshes[0].scale,{x:1.05,z:1.05,duration:.08,repeat:1,yoyo:true});}
 async swapEvent(event){if(this.marker){const [r,c]=event.cells[event.active];await this.queue.tween(this.marker.position,{x:c,z:r,y:1.4,duration:.16});}}
 async fall(){this.scene.rig.shake();await Promise.all(this.meshes.flatMap(m=>[this.queue.tween(m.position,{y:-5,duration:.6,ease:'power2.in'}),this.queue.tween(m.rotation,{z:m.rotation.z+.8,duration:.6}),this.queue.tween(m.material,{opacity:0,duration:.6})]));}
 async win(){this.scene.rig.shake();await Promise.all(this.meshes.map(m=>this.queue.tween(m.position,{y:-2.2,duration:.65,ease:'power2.inOut'})));}
 check(state){if(!state)return true;const poses=poseFromState(state);return poses.every((p,i)=>this.meshes[i]&&this.meshes[i].position.distanceTo(new THREE.Vector3(...p.position))<1e-5&&this.meshes[i].quaternion.angleTo(new THREE.Quaternion().setFromEuler(new THREE.Euler(...p.rotation)))<1e-5);}
}
