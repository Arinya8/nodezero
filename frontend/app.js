const $=id=>document.getElementById(id);
const search=$('food-search');
const options=$('food-options');
let selectedFood=null;
let matches=[];
let activeIndex=-1;
let requestNumber=0;
let searchTimer;
let searchAbort;
let categories=[];
let selectedCategory=null;
const manualLimits={};

const safe=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const numeric=value=>value!==null&&value!==undefined&&value!==''&&Number.isFinite(Number(value))?Number(value):null;
const format=value=>numeric(value)===null?'Not available':Number(value).toLocaleString('en',{maximumFractionDigits:3});
const unitRange=(minimum,maximum)=>{
  const min=numeric(minimum),max=numeric(maximum);
  if(min===null&&max===null)return 'Not available';
  if(min===null)return `Up to ${format(max)}`;
  if(max===null)return `At least ${format(min)}`;
  return `${format(min)} – ${format(max)}`;
};
const groupOf=food=>food.raw_attributes?.grup||'Food group not recorded';

function showOptions(items){
  matches=items;
  activeIndex=-1;
  options.innerHTML=items.map((food,index)=>`<button class="food-option" id="food-option-${index}" type="button" role="option" aria-selected="false" data-index="${index}"><span class="option-name">${safe(food.name)}</span><span class="option-group">${safe(groupOf(food))}</span></button>`).join('')||'<p class="empty-options">No foods found. Try a shorter name or search by group.</p>';
  options.hidden=false;
  search.setAttribute('aria-expanded','true');
}

async function searchFoods(query){
  const current=++requestNumber;
  searchAbort?.abort();
  searchAbort=new AbortController();
  $('search-status').textContent='Searching the food database…';
  try{
    const response=await fetch(`/api/foods?q=${encodeURIComponent(query)}&limit=30`,{signal:searchAbort.signal});
    const payload=await response.json();
    if(!response.ok)throw new Error(payload.error||`Food search failed (${response.status})`);
    if(current!==requestNumber)return;
    showOptions(payload.foods||[]);
    $('search-status').textContent=`${Number(payload.count||0).toLocaleString()} matching foods`;
  }catch(error){
    if(error.name==='AbortError'||current!==requestNumber)return;
    options.innerHTML=`<p class="empty-options">${safe(error.message)}. Check that the API is running.</p>`;
    options.hidden=false;search.setAttribute('aria-expanded','true');
    $('search-status').textContent='Food search is unavailable.';
  }
}

function queueSearch(){
  const query=search.value.trim();
  clearTimeout(searchTimer);
  if(!query){
    requestNumber++;searchAbort?.abort();options.hidden=true;search.setAttribute('aria-expanded','false');
    $('search-status').textContent='Search the food database to begin.';
    return;
  }
  searchTimer=setTimeout(()=>searchFoods(query),160);
}

function selectFood(food){
  selectedFood=food;
  search.value=food.name;
  options.hidden=true;search.setAttribute('aria-expanded','false');search.removeAttribute('aria-activedescendant');
  $('search-status').textContent=`Selected from ${groupOf(food)}.`;
  $('food-name').textContent=food.name||'Unnamed food';
  $('food-code').textContent=food.code||'';
  $('food-group').textContent=groupOf(food);
  $('food-category').textContent=food.food_category||'No mapped category';
  $('otr-range').textContent=unitRange(food.min_otr,food.max_otr);
  $('wvtr-range').textContent=unitRange(food.min_wvtr,food.max_wvtr);
  $('reason-text').textContent=food.requirement_description||(food.food_category?'The selected category provides the barrier range shown above. The source data has no additional explanation for this food.':'This food is in the source dataset, but its group has no mapped packaging range. Choose a category manually below before checking materials.');
  $('food-water').textContent=numeric(food.water_pct)===null?'Not recorded':`${format(food.water_pct)}%`;
  $('food-fat').textContent=numeric(food.fat_pct)===null?'Not recorded':`${format(food.fat_pct)}%`;
  $('food-moisture').textContent=food.moisture_class||'Not recorded';
  $('food-risk').textContent=food.food_risk_profile||'Not recorded';
  const canAnalyze=Boolean(food.food_category)&&[food.min_otr,food.max_otr,food.min_wvtr,food.max_wvtr].some(value=>numeric(value)!==null);
  $('analyze-food').disabled=!canAnalyze;
  $('analyze-food').innerHTML=canAnalyze?'Check materials <span aria-hidden="true">→</span>':'Choose a manual category to check materials';
  $('food-result').hidden=false;
  $('food-analysis').hidden=true;
}

function chooseOption(button){
  const index=Number(button?.dataset.index);
  if(Number.isInteger(index)&&matches[index])selectFood(matches[index]);
}

search.addEventListener('input',queueSearch);
search.addEventListener('focus',()=>{if(search.value.trim()&&!options.hidden)search.setAttribute('aria-expanded','true');});
search.addEventListener('keydown',event=>{
  const buttons=[...options.querySelectorAll('[data-index]')];
  if(event.key==='ArrowDown'&&buttons.length){event.preventDefault();activeIndex=Math.min(activeIndex+1,buttons.length-1);buttons.forEach((button,index)=>button.classList.toggle('active',index===activeIndex));search.setAttribute('aria-activedescendant',buttons[activeIndex].id);buttons[activeIndex].scrollIntoView({block:'nearest'});}
  else if(event.key==='ArrowUp'&&buttons.length){event.preventDefault();activeIndex=Math.max(activeIndex-1,0);buttons.forEach((button,index)=>button.classList.toggle('active',index===activeIndex));search.setAttribute('aria-activedescendant',buttons[activeIndex].id);buttons[activeIndex].scrollIntoView({block:'nearest'});}
  else if(event.key==='Enter'&&activeIndex>=0){event.preventDefault();chooseOption(buttons[activeIndex]);}
  else if(event.key==='Escape'){options.hidden=true;search.setAttribute('aria-expanded','false');search.removeAttribute('aria-activedescendant');}
});
options.addEventListener('click',event=>chooseOption(event.target.closest('[data-index]')));
document.addEventListener('click',event=>{if(!event.target.closest('.finder')){options.hidden=true;search.setAttribute('aria-expanded','false');}});

function setManualSlider(metric,category){
  const slider=$(`manual-${metric}`),wrap=$(`manual-${metric}-wrap`),target=$(`manual-${metric}-value`);
  const minimum=numeric(category[`min_${metric}`]);
  const maximum=numeric(category[`max_${metric}`]);
  if(maximum===null||maximum<=0){wrap.hidden=true;delete manualLimits[`max_${metric}`];return;}
  const min=minimum===null?0:minimum;
  wrap.hidden=false;slider.min=String(min);slider.max=String(maximum);
  slider.step='any';
  slider.value=String(maximum);slider.disabled=maximum<=min;
  target.textContent=format(maximum);manualLimits[`max_${metric}`]=maximum;
}

function setManualCategory(name){
  selectedCategory=categories.find(category=>category.name===name)||null;
  const analyze=$('analyze-manual');
  analyze.disabled=!selectedCategory;
  if(!selectedCategory){$('manual-description').textContent='Select a category to see its saved requirements.';$('manual-otr-wrap').hidden=true;$('manual-wvtr-wrap').hidden=true;return;}
  $('manual-description').textContent=`OTR ${unitRange(selectedCategory.min_otr,selectedCategory.max_otr)} cm³/m²/day · WVTR ${unitRange(selectedCategory.min_wvtr,selectedCategory.max_wvtr)} g/m²/day. ${selectedCategory.description||''}`;
  setManualSlider('otr',selectedCategory);setManualSlider('wvtr',selectedCategory);
  $('manual-analysis').hidden=true;
}

async function loadCategories(){
  if(categories.length)return;
  const select=$('manual-category');
  try{
    const response=await fetch('/api/categories');
    const payload=await response.json();
    if(!response.ok)throw new Error(payload.error||`Category list failed (${response.status})`);
    categories=payload.categories||[];
    select.innerHTML='<option value="">Choose a category</option>'+categories.map(category=>`<option value="${safe(category.name)}">${safe(category.name)}</option>`).join('');
  }catch(error){select.innerHTML='<option value="">Categories unavailable</option>';$('manual-description').textContent=`Could not load category requirements: ${error.message}`;}
}

$('manual-toggle').addEventListener('click',async()=>{
  const panel=$('manual-panel'),open=panel.hidden;
  panel.hidden=!open;$('manual-toggle').setAttribute('aria-expanded',String(open));
  if(open){if(selectedFood&&!$('manual-name').value)$('manual-name').value=selectedFood.name;await loadCategories();}
});
$('manual-category').addEventListener('change',event=>setManualCategory(event.target.value));
for(const metric of ['otr','wvtr']){
  $(`manual-${metric}`).addEventListener('input',event=>{
    manualLimits[`max_${metric}`]=Number(event.target.value);
    $(`manual-${metric}-value`).textContent=format(event.target.value);
    $('manual-analysis').hidden=true;
  });
}

function renderAnalysis(payload,container){
  const result=payload.result,summary=result.cluster_summary||{};
  const reasonFor=item=>{
    const rules=item.rule_results||[];
    const relevant=rules.filter(rule=>rule.status==='FAIL'||rule.status==='UNKNOWN');
    const reasons=[...new Set(relevant.map(rule=>rule.reason).filter(Boolean))].slice(0,2);
    if(!reasons.length&&item.warnings?.length)reasons.push(item.warnings[0]);
    if(!reasons.length)reasons.push('All available hard checks passed for this material.');
    return reasons.join(' ');
  };
  const groups=[
    ['Potential fit',result.candidates||[]],
    ['Needs review',result.requires_review_candidates||[]],
    ['Does not fit',result.rejected_candidates||[]],
  ];
  const sections=groups.map(([title,items])=>items.length?`<section class="outcome-group"><h3>${title}<small>${items.length}</small></h3><ul class="analysis-list">${items.slice(0,3).map(item=>`<li class="material-result"><div class="material-head"><strong>${safe(item.material_name)}</strong><span class="status ${safe(item.status.toLowerCase())}">${safe(item.status.replaceAll('_',' '))}</span></div><p>${safe(reasonFor(item))}</p></li>`).join('')}</ul></section>`:'').join('');
  container.innerHTML=`<p class="eyebrow">MATERIAL CHECK</p><p class="analysis-summary">${safe(summary.explanation||'Materials checked against the selected food profile.')}</p><p class="analysis-count">${Number(summary.clustered_count||0)} grouped · ${Number(summary.unclustered_count||0)} without comparable OTR/WVTR data</p>${sections||'<p class="analysis-summary">No material outcomes returned.</p>'}`;
}

async function analyze(body,container,button){
  container.hidden=false;container.innerHTML='<p class="analysis-summary">Checking materials against the saved rule set…</p>';button.disabled=true;
  try{
    const response=await fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const payload=await response.json();
    if(!response.ok)throw new Error(payload.error||`Material check failed (${response.status})`);
    renderAnalysis(payload,container);
  }catch(error){container.innerHTML=`<p class="error-message">${safe(error.message)}. Check that the recommendation API is running.</p>`;}
  finally{button.disabled=false;}
}

$('analyze-food').addEventListener('click',()=>{
  if(selectedFood)analyze({food_code:selectedFood.code,use_clustering:true},$('food-analysis'),$('analyze-food'));
});
$('analyze-manual').addEventListener('click',()=>{
  if(!selectedCategory)return;
  analyze({
    manual_food:{name:$('manual-name').value.trim()||'Unlisted food',food_category:selectedCategory.name},
    barrier_limits:manualLimits,
    use_clustering:true,
  },$('manual-analysis'),$('analyze-manual'));
});
