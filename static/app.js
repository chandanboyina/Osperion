let currentInvestigation = null;
let currentReport = null;
let currentImageReport = null;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(url, options={}) {
  const r = await fetch(url, options);
  const text = await r.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = {detail:text}; }
  if (!r.ok) throw new Error(data.detail || 'Request failed');
  return data;
}
function jsonOptions(method, body){ return {method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}; }

async function loadInvestigations(){
  const j=await api('/api/investigations');
  const list=$('investigationList');
  $('emptyInvestigations').classList.toggle('hidden', j.items.length!==0);
  list.innerHTML=j.items.map(i=>`
    <button class="investigation-card" onclick="openInvestigation(${i.investigation_id})">
      <div class="card-top"><span class="folder">INV</span><span class="date">${esc(formatDate(i.updated_at))}</span></div>
      <h2>${esc(i.name)}</h2>
      <p>${esc(i.description||'No description yet.')}</p>
      <div class="card-meta"><span>${i.evidence_count} evidence</span><span>${i.artifact_count} artifacts</span><span>${i.image_count||0} images</span><span>${i.entry_count} journal entries</span></div>
    </button>`).join('');
}
function formatDate(v){ try{return new Date(v).toLocaleString()}catch{return v}}
function show(id, yes=true){$(id).classList.toggle('hidden',!yes)}
function openCreate(){ 
  $('modalTitle').textContent='Create investigation';
  $('modalBody').innerHTML=`<form onsubmit="createInvestigation(event)">
    <label>Name<input id="formName" required maxlength="120" placeholder="Investigation 1"></label>
    <label>Description<textarea id="formDescription" rows="4" placeholder="What is this investigation about?"></textarea></label>
    <div class="form-actions"><button type="button" onclick="closeModal()">Cancel</button><button class="primary">Create investigation</button></div>
  </form>`;
  show('modal');
}
async function createInvestigation(e){e.preventDefault();try{const j=await api('/api/investigations',jsonOptions('POST',{name:$('formName').value,description:$('formDescription').value}));closeModal();await loadInvestigations();openInvestigation(j.investigation_id)}catch(err){alert(err.message)}}
function closeModal(){show('modal',false)}
$('newInvestigation').onclick=openCreate;

async function openInvestigation(id){
  try{
    const j=await api('/api/investigations/'+id);
    currentInvestigation=j.investigation;
    $('invName').textContent=j.investigation.name;
    $('invDescription').textContent=j.investigation.description||'No description yet.';
    $('invStats').innerHTML=`<span>${j.stats.evidence} evidence</span><span>${j.stats.artifacts} artifacts</span><span>${j.images?.length||0} images</span><span>${j.entries.length} entries</span>`;
    show('investigationHome',false); show('investigationDetail',true);
    renderEntries(j.entries); renderEvidence(j.evidence); renderImages(j.images||[]); renderOverview(j);
    switchTab('overview');
  }catch(err){alert(err.message)}
}
$('backHome').onclick=()=>{show('investigationDetail',false);show('investigationHome',true);currentInvestigation=null;loadInvestigations()};
$('editInvestigation').onclick=()=>openEditInvestigation();
$('downloadReport').onclick=()=>{if(currentInvestigation)window.location.href='/api/investigations/'+currentInvestigation.investigation_id+'/report.pdf';};
$('deleteInvestigation').onclick=async()=>{
  if(!currentInvestigation)return;
  if(!confirm(`Delete "${currentInvestigation.name}" and all its evidence and journal entries? This cannot be undone.`))return;
  try{await api('/api/investigations/'+currentInvestigation.investigation_id,{method:'DELETE'});$('backHome').click()}catch(e){alert(e.message)}
};
function openEditInvestigation(){
  $('modalTitle').textContent='Edit investigation';
  $('modalBody').innerHTML=`<form onsubmit="updateInvestigation(event)">
    <label>Name<input id="formName" required maxlength="120" value="${esc(currentInvestigation.name)}"></label>
    <label>Description<textarea id="formDescription" rows="4">${esc(currentInvestigation.description||'')}</textarea></label>
    <div class="form-actions"><button type="button" onclick="closeModal()">Cancel</button><button class="primary">Save changes</button></div>
  </form>`;show('modal');
}
async function updateInvestigation(e){e.preventDefault();try{const j=await api('/api/investigations/'+currentInvestigation.investigation_id,jsonOptions('PUT',{name:$('formName').value,description:$('formDescription').value}));currentInvestigation=j;closeModal();await openInvestigation(j.investigation_id)}catch(err){alert(err.message)}}

document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
function switchTab(tab){
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  ['overview','evidence','images','notes','search'].forEach(x=>show('tab-'+x,x===tab));
  if((tab==='notes'||tab==='images')&&currentInvestigation)refreshInvestigation();
}
function renderOverview(j){
  $('overviewRecent').innerHTML=j.evidence.length?`<table><thead><tr><th>Time</th><th>Platform</th><th>File</th><th>Matched Artifacts</th></tr></thead><tbody>${j.evidence.slice(0,6).map(e=>{
    const matches=e.matches||[];
    const preview=matches.slice(0,2).map(m=>`<div class="evidence-match"><span>${esc(m.artifact_type)}</span><code>${esc(m.value)}</code></div>`).join('');
    const more=matches.length>2?`<div class="evidence-more">+${matches.length-2} more</div>`:'';
    const body=matches.length?`<div class="match-count">${matches.length} match${matches.length===1?'':'es'}</div><div class="evidence-match-list">${preview}${more}</div>`:'<span class="no-match">No previous matches</span>';
    return `<tr><td>${esc(formatDate(e.created_at))}</td><td>${esc(e.platform)}</td><td>${esc(e.filename)}</td><td>${body}</td></tr>`;
  }).join('')}</tbody></table>`:'<div class="empty">No evidence saved in this investigation yet.</div>';
}function renderEvidence(items){
  $('evidenceHistory').innerHTML=items.length?`<table><thead><tr><th>ID</th><th>Time</th><th>Platform</th><th>File</th><th>Matched Artifacts</th></tr></thead><tbody>${items.map(e=>{
    const matches=e.matches||[];
    const preview=matches.slice(0,3).map(m=>`<div class="evidence-match"><span>${esc(m.artifact_type)}</span><code>${esc(m.value)}</code></div>`).join('');
    const more=matches.length>3?`<div class="evidence-more">+${matches.length-3} more</div>`:'';
    const body=matches.length?`<div class="match-count">${matches.length} match${matches.length===1?'':'es'}</div><div class="evidence-match-list">${preview}${more}</div>`:'<span class="no-match">No previous matches</span>';
    return `<tr><td>#${e.evidence_id}</td><td>${esc(formatDate(e.created_at))}</td><td>${esc(e.platform)}</td><td>${esc(e.filename)}</td><td>${body}</td></tr>`;
  }).join('')}</tbody></table>`:'<div class="empty">No saved evidence yet.</div>';
}
}
function renderImages(items){
  $('imageHistory').innerHTML=items.length?`<table><thead><tr><th>Time</th><th>Label</th><th>Platform</th><th>pHash</th><th>SHA-256</th><th>Action</th></tr></thead><tbody>${items.map(i=>`<tr><td>${esc(formatDate(i.created_at))}</td><td>${esc(i.label||i.filename)}</td><td>${esc(i.platform)}</td><td class="mono">${esc(i.phash)}</td><td class="mono">${esc(i.sha256.slice(0,18))}…</td><td><button class="danger-outline" onclick="deleteImage(${i.image_id})">Delete</button></td></tr>`).join('')}</tbody></table>`:'<div class="empty">No saved images in this investigation yet.</div>';
}
function renderImageReport(r){
  show('imageResults');
  $('imageSha').textContent=r.sha256.slice(0,18)+'…';
  $('imagePhash').textContent=r.phash;
  $('imageMatches').textContent=r.match_count;
  $('imageDimensions').textContent=`${r.width} × ${r.height}`;
  $('imageCorrelations').innerHTML=r.matches.length?r.matches.map(m=>`<div class="match"><div><span class="badge ${m.match_type==='exact_file'?'high':'observed'}">${esc(m.match_type.replace('_',' '))}</span> <b>${esc(m.label||m.filename)}</b></div><div class="mono">pHash: ${esc(m.phash)}</div><small>Platform: ${esc(m.platform)} · Distance: ${m.phash_distance} · ${esc(formatDate(m.created_at))}</small><p>${esc(m.note)}</p></div>`).join(''):'<div class="empty">No exact or close perceptual match was found in this investigation.</div>';
  $('saveImage').disabled=false;$('saveImage').textContent='Save image to this investigation';
}

async function refreshInvestigation(){const j=await api('/api/investigations/'+currentInvestigation.investigation_id);currentInvestigation=j.investigation;renderEntries(j.entries);renderEvidence(j.evidence);renderImages(j.images||[]);renderOverview(j);$('invStats').innerHTML=`<span>${j.stats.evidence} evidence</span><span>${j.stats.artifacts} artifacts</span><span>${j.images?.length||0} images</span><span>${j.entries.length} entries</span>`;}
$('refreshEvidence').onclick=refreshInvestigation;

$('file').addEventListener('change',async e=>{const f=e.target.files[0];if(f)$('input').value=await f.text()});
$('clear').onclick=()=>{$('input').value='';$('file').value='';show('results',false);currentReport=null};
$('analyze').onclick=async()=>{
  const text=$('input').value;if(!text.trim()){alert('Paste or upload inspect/source code first.');return}
  const fd=new FormData();fd.append('text',text);fd.append('platform',$('platform').value);fd.append('investigation_id',currentInvestigation.investigation_id);
  $('analyze').disabled=true;
  try{currentReport=await api('/api/analyze',{method:'POST',body:fd});renderReport(currentReport);}
  catch(e){alert('Analysis failed: '+e.message)}finally{$('analyze').disabled=false}
};
function renderReport(r){
 show('results');
 $('mPlatform').textContent=r.platform;$('mArtifacts').textContent=r.artifact_count;$('mMatches').textContent=r.correlation_count;$('mHash').textContent=r.input_sha256.slice(0,18)+'…';
 $('artifacts').innerHTML=r.artifacts.length?`<table><thead><tr><th>Confidence</th><th>Type</th><th>Value</th><th>Context</th></tr></thead><tbody>${r.artifacts.map(a=>`<tr><td><span class="badge ${esc(a.confidence)}">${esc(a.confidence)}</span></td><td>${esc(a.type)}</td><td class="mono">${esc(a.value)}</td><td>${esc(a.context)}</td></tr>`).join('')}</tbody></table>`:'<div class="empty">No artifacts extracted.</div>';
 $('correlations').innerHTML=r.correlations.length?r.correlations.map(m=>`<div class="match"><div><span class="badge exact">previously observed</span> <b>${esc(m.artifact_type)}</b></div><div class="mono">${esc(m.value)}</div><small>Evidence #${m.matched_evidence_id} — ${esc(m.matched_filename)} — ${esc(formatDate(m.matched_at))}</small><p>${esc(m.note)}</p></div>`).join(''):'<div class="empty">No previously saved artifact matched this evidence in this investigation.</div>';
 $('save').disabled=false;$('save').textContent='Save to this investigation';
}
$('save').onclick=async()=>{if(!currentReport)return;try{const j=await api('/api/save',jsonOptions('POST',{report:currentReport,filename:'browser-inspect-evidence',investigation_id:currentInvestigation.investigation_id}));$('save').textContent='Saved ✓';$('save').disabled=true;await refreshInvestigation()}catch(e){alert(e.message)}};

function renderEntries(items){
  $('entryList').innerHTML=items.length?items.map(e=>`<article class="entry"><div class="entry-head"><div><span class="type ${e.entry_type}">${esc(e.entry_type)}</span><h3>${esc(e.title)}</h3></div><div class="entry-buttons"><button onclick='openEntryModal("edit",${JSON.stringify(e).replace(/'/g,"&#39;")})'>Edit</button><button class="danger-outline" onclick="deleteEntry(${e.entry_id})">Delete</button></div></div><div class="entry-content">${esc(e.content).replace(/\n/g,'<br>')}</div><small>Updated ${esc(formatDate(e.updated_at))}</small></article>`).join(''):'<div class="empty-card"><h2>Your research journal is empty</h2><p>Create a note, report or remark to document your investigation.</p></div>';
}
function openEntryModal(mode='note', data=null){
  const edit=mode==='edit', type=edit?data.entry_type:mode;
  $('modalTitle').textContent=edit?'Edit '+type:'New '+type;
  $('modalBody').innerHTML=`<form onsubmit="${edit?'updateEntry(event,'+data.entry_id+')':'createEntry(event)'}">
    <label>Type<select id="entryType"><option value="note" ${type==='note'?'selected':''}>Note</option><option value="report" ${type==='report'?'selected':''}>Report</option><option value="remark" ${type==='remark'?'selected':''}>Remark</option></select></label>
    <label>Title<input id="entryTitle" maxlength="200" value="${edit?esc(data.title):''}" placeholder="Short title"></label>
    <label>Content<textarea id="entryContent" rows="12" required placeholder="Record your research, observations, findings or next steps...">${edit?esc(data.content):''}</textarea></label>
    <div class="form-actions"><button type="button" onclick="closeModal()">Cancel</button><button class="primary">${edit?'Update':'Create'}</button></div>
  </form>`;show('modal');
}
async function createEntry(e){e.preventDefault();try{await api(`/api/investigations/${currentInvestigation.investigation_id}/entries`,jsonOptions('POST',{entry_type:$('entryType').value,title:$('entryTitle').value,content:$('entryContent').value}));closeModal();await refreshInvestigation()}catch(err){alert(err.message)}}
async function updateEntry(e,id){e.preventDefault();try{await api('/api/entries/'+id,jsonOptions('PUT',{entry_type:$('entryType').value,title:$('entryTitle').value,content:$('entryContent').value}));closeModal();await refreshInvestigation()}catch(err){alert(err.message)}}
async function deleteEntry(id){if(!confirm('Delete this entry?'))return;try{await api('/api/entries/'+id,{method:'DELETE'});await refreshInvestigation()}catch(e){alert(e.message)}}

$('analyzeImage').onclick=async()=>{
  const f=$('imageFile').files[0];
  if(!f){alert('Choose a profile/media image first.');return;}
  const fd=new FormData();fd.append('file',f);fd.append('investigation_id',currentInvestigation.investigation_id);
  $('analyzeImage').disabled=true;
  try{currentImageReport=await api('/api/images/analyze',{method:'POST',body:fd});renderImageReport(currentImageReport);}
  catch(e){alert('Image analysis failed: '+e.message)}finally{$('analyzeImage').disabled=false}
};
$('saveImage').onclick=async()=>{
  const f=$('imageFile').files[0];
  if(!f||!currentImageReport)return;
  const fd=new FormData();fd.append('file',f);fd.append('investigation_id',currentInvestigation.investigation_id);fd.append('label',$('imageLabel').value);fd.append('platform',$('imagePlatform').value);
  try{await api('/api/images/save',{method:'POST',body:fd});$('saveImage').textContent='Saved ✓';$('saveImage').disabled=true;await refreshInvestigation();}catch(e){alert('Could not save image: '+e.message)}
};
$('clearImage').onclick=()=>{$('imageFile').value='';$('imageLabel').value='';show('imageResults',false);currentImageReport=null};
$('refreshImages').onclick=refreshInvestigation;
async function deleteImage(id){if(!confirm('Delete this saved image and its local hash record?'))return;try{await api('/api/images/'+id,{method:'DELETE'});await refreshInvestigation();}catch(e){alert(e.message)}}

$('searchBtn').onclick=async()=>{const q=$('query').value.trim();if(!q)return;const j=await api('/api/search?q='+encodeURIComponent(q));const items=j.items.filter(x=>x.investigation_id===currentInvestigation.investigation_id);$('searchResults').innerHTML=items.length?`<table><thead><tr><th>Type</th><th>Value</th><th>Evidence</th><th>Observed</th></tr></thead><tbody>${items.map(x=>`<tr><td>${esc(x.type)}</td><td class="mono">${esc(x.value)}</td><td>#${x.evidence_id} ${esc(x.filename)}</td><td>${esc(formatDate(x.created_at))}</td></tr>`).join('')}</tbody></table>`:'<div class="empty">No saved artifact found in this investigation.</div>'};

loadInvestigations();
