/** Own every tween. Cancellation settles pending promises and invalidates the generation. */
export class AnimationQueue {
  constructor(){this.generation=0;this.pending=new Set();this.speed=1;this.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;}
  tween(target,vars){const generation=this.generation;return new Promise(resolve=>{
    const item={tween:null,finish:null};
    item.finish=()=>{this.pending.delete(item);resolve(generation===this.generation);};
    item.tween=gsap.to(target,{...vars,duration:this.reduced?.012:(vars.duration??.28)/this.speed,onComplete:item.finish,onInterrupt:item.finish});
    this.pending.add(item);
  });}
  async play(events,handler){const token=this.generation;for(const event of events){if(token!==this.generation)return false;await handler(event);}return token===this.generation;}
  cancel(){this.generation++;for(const item of [...this.pending]){item.tween.kill();item.finish();}this.pending.clear();}
  visibility(hidden){for(const item of this.pending)hidden?item.tween.pause():item.tween.resume();}
}
