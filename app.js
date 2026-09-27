const search=document.querySelector('#food-search');
const list=document.querySelector('#food-options');
const count=document.querySelector('#match-count');
let foods=[];
let selected=null;
let activeIndex=-1;
let barrierLimits={};
const $=id=>document.getElementById(id);
const value=(v,suffix='')=>v!==''&&v!=null&&Number.isFinite(Number(v))?`${Number(v).toLocaleString('en',{maximumFractionDigits:2})}${suffix}`:'Not available';
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function renderOptions(){
  const q=search.value.trim().toLocaleLowerCase();
  const matches=foods.filter(f=>!q||`${f.name} ${f.code} ${f.grup}`.toLocaleLowerCase().includes(q));
  const open=q.length>0;
  list.hidden=!open;
  search.setAttribute('aria-expanded',String(open));
  activeIndex=-1;
  count.textContent=`${matches.length.toLocaleString()} ${matches.length===1?'food':'foods'}`;
  list.innerHTML=matches.slice(0,80).map(f=>`<button class="food-option ${selected?.code===f.code?'selected':''}" id="food-option-${safe(f.code)}" type="button" role="option" aria-selected="${selected?.code===f.code?'true':'false'}" data-code="${safe(f.code)}"><span>${safe(f.name)}</span><small>${safe(f.code)}</small></button>`).join('')||'<p class="empty">No matching foods. Try another name.</p>';
}
function explain(f){
  if(f.Description?.trim())return f.Description.trim();
  const bits=[];
  if(f.fatce!==''&&Number(f.fatce)>15)bits.push(`The food has ${value(f.fatce,'%')} fat, which can increase oxidation sensitivity.`);
  if(f.water!==''&&Number(f.water)<10)bits.push(`Its low water content (${value(f.water,'%')}) may make moisture uptake important.`);
  if(f.moisture_barrier_requirement)bits.push(`The derived profile marks its moisture barrier need as “${f.moisture_barrier_requirement.replaceAll('_',' ')}”.`);
  return bits.length?bits.join(' '):'The project data maps this food group to the selected category. No specific requirement explanation is available in the source row.';
}
function configureBarrierSlider(metric,food){
  const minKey=metric==='otr'?'Min_OTR':'Min_WVTR';
  const maxKey=metric==='otr'?'Max_OTR':'Max_WVTR';
  const slider=$(`${metric}-slider`),output=$(`${metric}-target`);
  const lower=Number(food[minKey]),maximum=Number(food[maxKey]);
  if(!Number.isFinite(maximum)||maximum<=0){
    slider.disabled=true;output.textContent='Not available';delete barrierLimits[`max_${metric}`];return;
  }
  const minimum=Number.isFinite(lower)&&lower>=0?lower:0;
  slider.disabled=maximum<=minimum;
  slider.dataset.min=String(minimum);slider.dataset.max=String(maximum);slider.value='1000';
  barrierLimits[`max_${metric}`]=maximum;output.textContent=value(maximum);
  $(`${metric}-range-fill`).style.width='100%';
}
function updateBarrierSlider(metric){
  const slider=$(`${metric}-slider`);
  if(slider.disabled||!selected)return;
  const minimum=Number(slider.dataset.min),maximum=Number(slider.dataset.max),progress=Number(slider.value)/1000;
  const current=minimum>0?minimum*Math.pow(maximum/minimum,progress):minimum+(maximum-minimum)*progress*progress;
  const target=Number(current.toPrecision(4));
  barrierLimits[`max_${metric}`]=target;
  $(`${metric}-target`).textContent=value(target);
  $(`${metric}-range-fill`).style.width=`calc(${progress*100}% - ${progress*4}px)`;
  $('analysis').hidden=true;
}
function showFood(f){
  selected=f;renderOptions();
  $('food-name').textContent=f.name||'Unnamed food';$('record-id').textContent=f.code||'';$('food-grup').textContent=f.grup||'Food group unavailable';$('reason-text').textContent=explain(f);
  $('otr-min').textContent=value(f.Min_OTR);$('otr-max').textContent=value(f.Max_OTR);$('wvtr-min').textContent=value(f.Min_WVTR);$('wvtr-max').textContent=value(f.Max_WVTR);
  $('otr-explain').textContent=f.Min_OTR!==''||f.Max_OTR!==''?`Dataset OTR interval: ${value(f.Min_OTR)}–${value(f.Max_OTR)} cm³/m²/day.`:'No OTR range is recorded for this food category.';
  $('wvtr-explain').textContent=f.Min_WVTR!==''||f.Max_WVTR!==''?`Dataset WVTR interval: ${value(f.Min_WVTR)}–${value(f.Max_WVTR)} g/m²/day.`:'No WVTR range is recorded for this food category.';
  $('category').textContent=f.packaging_category||'Unmapped';$('water').textContent=value(f.water,'%');$('fat').textContent=value(f.fatce,'%');$('moisture').textContent=f.moisture_class||'Not available';$('risk').textContent=f.food_risk_profile||'Not available';
  configureBarrierSlider('otr',f);configureBarrierSlider('wvtr',f);
  $('analysis').hidden=true;
}
function chooseOption(button){
  if(!button)return;
  const food=foods.find(item=>item.code===button.dataset.code);
  if(!food)return;
  showFood(food);search.value=food.name;list.hidden=true;search.setAttribute('aria-expanded','false');search.removeAttribute('aria-activedescendant');
}
list.addEventListener('click',e=>chooseOption(e.target.closest('[data-code]')));
search.addEventListener('input',renderOptions);
search.addEventListener('keydown',e=>{
  const options=[...list.querySelectorAll('[data-code]')];
  if(e.key==='ArrowDown'&&options.length){e.preventDefault();list.hidden=false;search.setAttribute('aria-expanded','true');activeIndex=Math.min(activeIndex+1,options.length-1);options.forEach((b,i)=>b.classList.toggle('active',i===activeIndex));search.setAttribute('aria-activedescendant',options[activeIndex].id);options[activeIndex].scrollIntoView({block:'nearest'});}
  else if(e.key==='ArrowUp'&&options.length){e.preventDefault();activeIndex=Math.max(activeIndex-1,0);options.forEach((b,i)=>b.classList.toggle('active',i===activeIndex));search.setAttribute('aria-activedescendant',options[activeIndex].id);options[activeIndex].scrollIntoView({block:'nearest'});}
  else if(e.key==='Enter'&&activeIndex>=0){e.preventDefault();chooseOption(options[activeIndex]);}
  else if(e.key==='Escape'){list.hidden=true;search.setAttribute('aria-expanded','false');search.removeAttribute('aria-activedescendant');}
});
search.addEventListener('focus',()=>{if(search.value.trim()){list.hidden=false;search.setAttribute('aria-expanded','true');}});
document.addEventListener('click',e=>{if(!e.target.closest('.picker')){list.hidden=true;search.setAttribute('aria-expanded','false');}});
$('otr-slider').addEventListener('input',()=>updateBarrierSlider('otr'));
$('wvtr-slider').addEventListener('input',()=>updateBarrierSlider('wvtr'));

fetch('./foods.json')
  .then(response=>{if(!response.ok)throw new Error('Could not load food data');return response.json();})
  .then(data=>{
    foods=data;renderOptions();
    const initialCode=new URLSearchParams(location.search).get('food');
    const initial=foods.find(food=>food.code===initialCode)||foods[0];
    if(initial)showFood(initial);
  })
  .catch(()=>{
    count.textContent='Food data unavailable';list.hidden=false;
    list.innerHTML='<p class="empty">Could not load foods.json. Open this page from a local web server, or deploy it to Vercel.</p>';
  });

document.querySelector('#analyze').addEventListener('click',async()=>{
  const output=$('analysis');
  if(!selected)return;
  output.hidden=false;output.innerHTML='<p class="analysis-status">Grouping materials, then checking the hard rules…</p>';
  try{
    const response=await fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({food_code:selected.code,use_clustering:true,barrier_limits:barrierLimits})});
    if(!(response.headers.get('content-type')||'').includes('application/json'))throw new Error('The recommendation API is not running. Start the local Python app or use the Vercel deployment.');
    const payload=await response.json();
    if(!response.ok)throw new Error(payload.error||`API returned ${response.status}`);
    const result=payload.result,summary=result.cluster_summary||{};
    const outcomes=[...(result.candidates||[]),...(result.requires_review_candidates||[]),...(result.rejected_candidates||[])];
    const cards=outcomes.slice(0,12).map(item=>`<li><strong>${safe(item.material_name)}</strong><span>${safe(item.status.replaceAll('_',' '))}${item.cluster_id===null||item.cluster_id===undefined?' · unclustered':` · cluster ${item.cluster_id+1}`}</span></li>`).join('');
    output.innerHTML=`<p class="eyebrow">CLUSTERING → RULE GATE</p><p class="analysis-status">${safe(summary.explanation||'Clustering summary unavailable.')}</p><p class="analysis-count">${summary.clustered_count||0} clustered · ${summary.unclustered_count||0} unclustered · ${summary.cluster_count||0} groups</p>${cards?`<ul class="analysis-list">${cards}</ul>`:'<p class="analysis-status">No materials returned.</p>'}`;
  }catch(error){output.innerHTML=`<p class="analysis-error">${safe(error.message)}</p>`;}
});
