/** Perspective camera fit uses all board corners; follow is deliberately subtle. */
import * as THREE from 'three';
export class CameraRig {
  constructor(camera){this.camera=camera;this.center=new THREE.Vector3();this.target=new THREE.Vector3();this.distance=15;this.shakeAmount=0;this.direction=new THREE.Vector3(0.72,1.3,1).normalize();}
  fit(width,height,aspect){this.center.set((width-1)/2,0,(height-1)/2);this.target.copy(this.center);
    this.camera.aspect=aspect;this.camera.updateProjectionMatrix();
    const forward=this.direction.clone().negate(),right=new THREE.Vector3().crossVectors(forward,new THREE.Vector3(0,1,0)).normalize(),up=new THREE.Vector3().crossVectors(right,forward).normalize();
    const tan=Math.tan(THREE.MathUtils.degToRad(this.camera.fov/2));let d=1;
    for(const x of [-width/2,width/2])for(const z of [-height/2,height/2])for(const y of [-1,3]){
      const v=new THREE.Vector3(x,y,z);const depth=v.dot(this.direction);
      d=Math.max(d,depth+Math.abs(v.dot(right))/(tan*aspect),depth+Math.abs(v.dot(up))/tan);
    }this.distance=d*1.22;this.update(null,1);
  }
  update(position,dt){const desired=this.center.clone();if(position)desired.lerp(position,.025);this.target.lerp(desired,Math.min(1,dt*4));
    this.camera.position.copy(this.target).addScaledVector(this.direction,this.distance);
    if(this.shakeAmount){this.camera.position.x+=Math.sin(performance.now()*.07)*this.shakeAmount;this.shakeAmount*=.86;}
    this.camera.lookAt(this.target);
  }
  shake(){this.shakeAmount=.1;}
}
