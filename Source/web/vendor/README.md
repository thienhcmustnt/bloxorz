# Vendored runtime libraries

- `three.module.js`: Three.js 0.160.1, fetched from https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js . MIT text is in THREE-LICENSE.txt.
- `gsap.min.js`: GSAP 3.12.5, fetched from https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js . The original copyright and license reference are retained in its header: https://gsap.com/standard-license .

These are runtime dependencies, not external art assets. Application textures, geometry and sounds are generated locally. No CDN is contacted at runtime. Application source is ES modules; GSAP's pinned UMD distribution supplies the `gsap` global.
