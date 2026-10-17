/** Procedural board renderer. Owns and disposes every level resource; no game rules. */
import * as THREE from 'three';
import {CameraRig} from './CameraRig.js';
export const COLORS={floor:0x64778a,start:0x76899b,fragile:0xc38549,bridge:0x328f9e,soft_switch:0x368c80,heavy_switch:0x8e70b7,split_switch:0x527fb4,goal:0x5ae0d2};
export function stoneGeometry(){const shape=new THREE.Shape();shape.moveTo(-.44,-.44);shape.lineTo(.44,-.44);shape.lineTo(.44,.44);shape.lineTo(-.44,.44);shape.closePath();const geo=new THREE.ExtrudeGeometry(shape,{depth:.23,bevelEnabled:true,bevelSegments:1,steps:1,bevelSize:.035,bevelThickness:.035});geo.rotateX(-Math.PI/2);geo.translate(0,-.265,0);return geo;}
function texture(kind,debugLabel=''){
  const canvas=document.createElement('canvas');canvas.width=canvas.height=128;const c=canvas.getContext('2d');
  c.fillStyle='#ffffff';let seed=17;for(let i=0;i<170;i++){seed=(seed*16807)%2147483647;const x=seed%128;seed=(seed*16807)%2147483647;c.globalAlpha=.015+(seed%5)/200;c.fillRect(x,seed%128,2,2);}c.globalAlpha=1;
  c.strokeStyle=kind==='fragile'?'#392c25':'#d9f6f1';c.lineWidth=6;c.lineCap='round';
  if(kind==='soft_switch'){c.beginPath();c.arc(64,64,30,0,Math.PI*2);c.stroke();c.beginPath();c.arc(64,64,8,0,Math.PI*2);c.fill();}
  if(kind==='heavy_switch'){c.beginPath();c.moveTo(40,40);c.lineTo(88,88);c.moveTo(40,88);c.lineTo(88,40);c.stroke();}
  if(kind==='split_switch'){c.font='bold 65px sans-serif';c.textAlign='center';c.fillText('( )',64,85);}
  if(kind==='start'){c.globalAlpha=.4;c.strokeRect(49,49,30,30);c.globalAlpha=1;}
  if(kind==='fragile'){c.lineWidth=3;c.beginPath();c.moveTo(20,0);c.lineTo(42,40);c.lineTo(72,54);c.lineTo(61,86);c.lineTo(91,128);c.moveTo(72,54);c.lineTo(119,26);c.stroke();}
  if(debugLabel){c.font='22px monospace';c.textAlign='center';c.fillStyle='#ffffff';c.fillText(debugLabel,64,116);}
  const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;return t;
}
export class SceneManager{
  constructor(container,queue,debug=false){this.container=container;this.queue=queue;this.debug=debug;this.scene=new THREE.Scene();this.scene.fog=new THREE.FogExp2(0x142332,.009);
    this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.3;container.prepend(this.renderer.domElement);
    this.camera=new THREE.PerspectiveCamera(36,1,.1,180);this.rig=new CameraRig(this.camera);this.scene.add(new THREE.HemisphereLight(0xc5e0ff,0x243342,2.3));
    const light=new THREE.DirectionalLight(0xffe1b5,3.2);light.position.set(-5,16,8);light.castShadow=true;light.shadow.mapSize.set(2048,2048);Object.assign(light.shadow.camera,{left:-28,right:28,top:28,bottom:-28,near:.1,far:70});light.shadow.bias=-.0006;light.shadow.normalBias=.025;this.scene.add(light);this.light=light;
    this.root=new THREE.Group();this.scene.add(this.root);this.resources=new Set();this.bridgeMeshes=new Map();this.specials=new Map();this.fps=0;this.last=performance.now();this.hidden=false;
    new ResizeObserver(()=>this.resize()).observe(container);document.addEventListener('visibilitychange',()=>{this.hidden=document.hidden;this.queue.visibility(this.hidden);this.last=performance.now();});
    this.renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();document.querySelector('#context-error').hidden=false;});
    this.renderer.setAnimationLoop(now=>{if(this.hidden)return;const dt=Math.min((now-this.last)/1000,.1);this.last=now;this.fps=this.fps*.94+(1/Math.max(dt,.001))*.06;this.rig.update(this.follow?.(),dt);this.renderer.render(this.scene,this.camera);this.onFrame?.();});
  }
  own(resource){this.resources.add(resource);return resource;}
  add(mesh){this.root.add(mesh);return mesh;}
  clear(){this.root.clear();for(const r of this.resources)r.dispose?.();this.resources.clear();this.bridgeMeshes.clear();this.specials.clear();this.renderer.renderLists.dispose();}
  material(kind){const options={color:COLORS[kind]??COLORS.floor,roughness:.76,metalness:.12};return this.own(new THREE.MeshStandardMaterial(options));}
  build(level,state){this.clear();this.level=level;this.tiles=[];const normal=[];const geo=this.own(stoneGeometry());
    for(let r=0;r<level.grid.length;r++)for(let c=0;c<level.grid[r].length;c++){
      const kind=level.legend[level.grid[r][c]];if(kind==='void')continue;
      if(kind==='floor'){normal.push([r,c]);continue;}
      const group=new THREE.Group();group.position.set(c,0,r);group.userData.cell=[r,c];this.add(group);this.tiles.push(group);
      if(kind==='goal'){
        const mat=this.own(new THREE.MeshStandardMaterial({color:0x54e4d0,emissive:0x29a99c,emissiveIntensity:.65,metalness:.3,roughness:.3}));
        for(const [x,z,w,d] of [[0,-.45,.98,.08],[0,.45,.98,.08],[-.45,0,.08,.82],[.45,0,.08,.82]]){const m=new THREE.Mesh(this.own(new THREE.BoxGeometry(w,.1,d)),mat);m.position.set(x,-.02,z);group.add(m);}
        const pit=new THREE.Mesh(this.own(new THREE.BoxGeometry(.86,.12,.86)),this.own(new THREE.MeshStandardMaterial({color:0x07121b})));pit.position.y=-1.4;group.add(pit);
        const walls=new THREE.Mesh(this.own(new THREE.BoxGeometry(.87,1.4,.87)),this.own(new THREE.MeshStandardMaterial({color:0x16363b,side:THREE.BackSide})));walls.position.y=-.7;group.add(walls);
      }else{
        const mesh=new THREE.Mesh(geo,this.material(kind));mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
        const symbol=new THREE.Mesh(this.own(new THREE.PlaneGeometry(.87,.87)),this.own(new THREE.MeshBasicMaterial({map:this.own(texture(kind)),transparent:true,depthWrite:false})));symbol.rotation.x=-Math.PI/2;symbol.position.y=.008;group.add(symbol);
      }
      this.specials.set(`${r},${c}`,group);
      if(kind==='bridge'){const bridge=level.bridges.find(b=>b.cells.some(cell=>cell[0]===r&&cell[1]===c));if(!this.bridgeMeshes.has(bridge.id))this.bridgeMeshes.set(bridge.id,[]);this.bridgeMeshes.get(bridge.id).push(group);}
    }
    const instanced=new THREE.InstancedMesh(geo,this.material('floor'),normal.length);instanced.castShadow=instanced.receiveShadow=true;this.add(instanced);this.own(instanced);const matrix=new THREE.Matrix4();
    normal.forEach(([r,c],i)=>instanced.setMatrixAt(i,matrix.makeTranslation(c,0,r)));instanced.instanceMatrix.needsUpdate=true;this.floorMesh=instanced;this.normalCells=normal;
    if(this.debug){for(let r=0;r<level.grid.length;r++)for(let c=0;c<level.grid[r].length;c++){if(level.legend[level.grid[r][c]]==='void')continue;const label=new THREE.Mesh(this.own(new THREE.PlaneGeometry(.87,.87)),this.own(new THREE.MeshBasicMaterial({map:this.own(texture('',`${r},${c}`)),transparent:true,depthWrite:false})));label.rotation.x=-Math.PI/2;label.position.set(c,.015,r);this.add(label);}}
    // A translucent receiving plane grounds the suspended board without external assets.
    const shadow=new THREE.Mesh(this.own(new THREE.PlaneGeometry(100,100)),this.own(new THREE.ShadowMaterial({opacity:.16})));shadow.rotation.x=-Math.PI/2;shadow.position.y=-2.5;shadow.receiveShadow=true;this.add(shadow);
    this.syncBridges(state);this.resize();this.light.target.position.copy(this.rig.center);this.scene.add(this.light.target);this.light.position.copy(this.rig.center).add(new THREE.Vector3(-5,16,8));
  }
  syncBridges(state){for(const [id,meshes] of this.bridgeMeshes){const open=state.bridges_open.includes(id);for(const mesh of meshes){mesh.visible=true;mesh.position.y=open?0:-.65;mesh.scale.setScalar(open?1:.72);mesh.traverse(o=>{if(o.material){o.material.transparent=!open;o.material.opacity=open?1:.16;}});}}
  }
  resize(){const w=this.container.clientWidth,h=this.container.clientHeight;this.renderer.setSize(w,h);this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));if(this.level)this.rig.fit(this.level.grid[0].length,this.level.grid.length,w/h);}
  memory(){return {...this.renderer.info.memory};}
}
