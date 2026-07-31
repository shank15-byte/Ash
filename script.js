/* A little interactive universe, made without external dependencies. */
const $ = (selector) => document.querySelector(selector);

// Cursor glow and gentle parallax
const cursor = $('.cursor-glow');
window.addEventListener('pointermove', (event) => {
  cursor.style.left = `${event.clientX}px`; cursor.style.top = `${event.clientY}px`;
});

// Star field
const sky = $('#sky'), skyCtx = sky.getContext('2d'); let stars = [];
function sizeSky(){ sky.width = innerWidth * devicePixelRatio; sky.height = innerHeight * devicePixelRatio; sky.style.width=`${innerWidth}px`; sky.style.height=`${innerHeight}px`; skyCtx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0); stars=Array.from({length:Math.min(180,Math.floor(innerWidth/7))},()=>({x:Math.random()*innerWidth,y:Math.random()*innerHeight,r:Math.random()*1.3+.15,a:Math.random(),s:Math.random()*.015+.003})); }
function drawSky(){ skyCtx.clearRect(0,0,innerWidth,innerHeight); stars.forEach(s=>{s.a+=s.s;const a=.25+Math.abs(Math.sin(s.a))*.7;skyCtx.fillStyle=`rgba(255,235,255,${a})`;skyCtx.beginPath();skyCtx.arc(s.x,s.y,s.r,0,Math.PI*2);skyCtx.fill();});requestAnimationFrame(drawSky); } sizeSky();drawSky();addEventListener('resize',sizeSky);

// Background particles
const particles = $('#particles');
for(let i=0;i<22;i++){const dot=document.createElement('i');dot.className='particle';const size=Math.random()*3+1;dot.style.cssText=`left:${Math.random()*100}%;bottom:-20px;width:${size}px;height:${size}px;animation-duration:${9+Math.random()*14}s;animation-delay:-${Math.random()*16}s`;particles.append(dot);}

// Reveal sections
const revealObserver = new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');revealObserver.unobserve(e.target)}}),{threshold:.14}); document.querySelectorAll('.reveal').forEach(el=>revealObserver.observe(el));
document.querySelectorAll('.love-card').forEach(card=>card.addEventListener('click',()=>card.classList.toggle('is-loved')));

// Landing loading experience
$('#enterBtn').addEventListener('click', async ()=>{const overlay=$('#loadingOverlay');overlay.classList.add('show');overlay.setAttribute('aria-hidden','false');const items=[...$('#loadingList').children];for(let i=0;i<items.length;i++){await wait(500);items[i].classList.add('done');$('#loadBar').style.width=`${(i+1)*20}%`;$('#loadPercent').textContent=`${(i+1)*20}%`;}await wait(600);$('.loader').classList.add('matched');await wait(1900);overlay.classList.remove('show');overlay.setAttribute('aria-hidden','true');document.querySelector('#love').scrollIntoView({behavior:'smooth'});});
const wait=(ms)=>new Promise(resolve=>setTimeout(resolve,ms));

// A polite runaway "No" button
const no=$('#noBtn'); no.addEventListener('pointerenter',()=>{const x=(Math.random()-.5)*180,y=(Math.random()-.5)*110;no.style.transform=`translate(${x}px,${y}px)`;});no.addEventListener('click',()=>{no.textContent='Hmm...';no.style.transform='translate(0,0)';});

function celebrate(hearts=false){const box=$('#celebration');for(let i=0;i<(hearts?180:90);i++){const piece=document.createElement('i');piece.className=hearts?'float-heart':'confetti';piece.textContent=hearts?'♥':'✦';piece.style.left=`${Math.random()*100}%`;piece.style.setProperty('--x',`${(Math.random()-.5)*260}px`);piece.style.color=['#ff70bb','#a96aff','#ffd06e','#86e7ff'][Math.floor(Math.random()*4)];piece.style.animationDuration=`${2.2+Math.random()*2.5}s`;piece.style.animationDelay=`${Math.random()*.5}s`;box.append(piece);setTimeout(()=>piece.remove(),5200);}}
function unlock(text){$('#achievementText').innerHTML=text;$('#achievement').classList.add('show');$('#achievement').setAttribute('aria-hidden','false');celebrate();}
$('#yesBtn').addEventListener('click',()=>unlock('Certified 4 AM<br />7UP Supplier 🥤♥'));$('#closeAchievement').addEventListener('click',()=>{$('#achievement').classList.remove('show');$('#achievement').setAttribute('aria-hidden','true');});

// Gallery lightbox
const lightbox=$('#lightbox');document.querySelectorAll('.gallery-item').forEach(item=>item.addEventListener('click',()=>{$('#lightboxImage').src=item.dataset.image;$('#lightboxImage').alt=item.querySelector('img').alt;$('#lightboxCaption').textContent=item.dataset.caption;lightbox.showModal();}));$('#lightboxClose').addEventListener('click',()=>lightbox.close());lightbox.addEventListener('click',event=>{if(event.target===lightbox)lightbox.close();});

// Typewriter begins only when its letter enters view
const letter=`Happy Girlfriend's Day ❤️\n\nI don't think words could ever fully explain what you mean to me.\n\nI love your kindness.\nI love your soul.\nI love your heart.\nI love your sweetness.\n\nMost of all...\n\nI love the way you love me.\n\nThank you for every laugh, every conversation, and every little memory we've created together.\n\nIf you ever ask for 7UP at 4 AM...\n\nI'd probably still go looking for one. ❤️\n\nI hope today reminds you how deeply loved you are.\n\nHappy Girlfriend's Day.\n\nForever yours,\n\nShashank`;
let typed=false;const typeObserver=new IntersectionObserver(([entry])=>{if(entry.isIntersecting&&!typed){typed=true;let i=0;const output=$('#typewriter');const type=()=>{output.textContent=letter.slice(0,i++);if(i<=letter.length)setTimeout(type,letter[i-1]==='\n'?130:17);};type();typeObserver.disconnect();}},{threshold:.28});typeObserver.observe($('#letter'));

// Heart constellation
const cc=$('#constellationCanvas'), cx=cc.getContext('2d');function drawConstellation(){const rect=cc.getBoundingClientRect(),d=devicePixelRatio;cc.width=rect.width*d;cc.height=rect.height*d;cx.setTransform(d,0,0,d,0,0);const ox=rect.width/2,oy=rect.height/2-40,scale=Math.min(rect.width,rect.height)/35;const pts=[];for(let t=0;t<Math.PI*2;t+=Math.PI/13){const x=16*Math.sin(t)**3;const y=-(13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t));pts.push([ox+x*scale,oy+y*scale]);}cx.strokeStyle='rgba(222,146,255,.43)';cx.lineWidth=1;cx.beginPath();pts.forEach((p,i)=>i?cx.lineTo(...p):cx.moveTo(...p));cx.closePath();cx.stroke();pts.forEach(([x,y])=>{cx.shadowBlur=18;cx.shadowColor='#ed9ee5';cx.fillStyle='#fff0ff';cx.beginPath();cx.arc(x,y,2.6,0,7);cx.fill();});}drawConstellation();addEventListener('resize',drawConstellation);

// Last surprise and secret star
$('#finalHeart').addEventListener('click',()=>{celebrate(true);$('#finalMessage').classList.add('show');$('#finalHeart').setAttribute('aria-label','A heart full of love');});let secretClicks=0;$('#secretStar').addEventListener('click',()=>{secretClicks++;if(secretClicks===5){unlock('Unlimited Hugs<br />♥');secretClicks=0;}});
