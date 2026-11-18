const API = window.NUTRITRACK_API || "";
const $ = id => document.getElementById(id);
let token = localStorage.getItem("nt_token") || "";
let me = null, chart = null;
const authHeaders = () => token ? {"Authorization": `Bearer ${token}`} : {};
async function api(path, options={}) {
  const res = await fetch(API + path, {headers: {"Content-Type":"application/json", ...authHeaders(), ...(options.headers||{})}, ...options});
  if (!res.ok) { let msg = "Request failed"; try { const x=await res.json(); msg=x.detail||msg; } catch {} throw new Error(msg); }
  if (res.status === 204) return null;
  return res.json();
}
function safe(s) { return String(s ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function showAuth(mode="login") {
  $("auth-view").hidden=false; $("app-view").hidden=true;
  $("login-form").hidden=mode!=="login"; $("register-form").hidden=mode!=="register";
  document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.auth===mode));
  $("auth-message").textContent="";
}
function showApp() { $("auth-view").hidden=true; $("app-view").hidden=false; }
function page(name) {
  document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===`page-${name}`));
  document.querySelectorAll(".nav").forEach(b=>b.classList.toggle("active",b.dataset.page===name));
  const titles={overview:"Overview",assessment:"New assessment",history:"Assessment history",recommendations:"Dietary recommendations",admin:"Admin dashboard"};
  $("page-title").textContent=titles[name]||"Overview";
  if(name==="history") loadHistory();
  if(name==="recommendations") loadRecommendations();
  if(name==="admin") loadAdmin();
}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>showAuth(b.dataset.auth)));
document.querySelectorAll(".nav").forEach(b=>b.addEventListener("click",()=>page(b.dataset.page)));
document.querySelectorAll("[data-goto]").forEach(b=>b.addEventListener("click",()=>page(b.dataset.goto)));
$("login-form").addEventListener("submit",async e=>{
  e.preventDefault(); const d=Object.fromEntries(new FormData(e.target));
  try { const x=await api("/api/auth/login",{method:"POST",body:JSON.stringify(d)}); token=x.token; localStorage.setItem("nt_token",token); await startApp(); }
  catch(err){$("auth-message").textContent=err.message;}
});
$("register-form").addEventListener("submit",async e=>{
  e.preventDefault(); const d=Object.fromEntries(new FormData(e.target));
  try { const x=await api("/api/auth/register",{method:"POST",body:JSON.stringify(d)}); token=x.token; localStorage.setItem("nt_token",token); await startApp(); }
  catch(err){$("auth-message").textContent=err.message;}
});
$("logout").addEventListener("click",()=>{token="";me=null;localStorage.removeItem("nt_token");showAuth();});
async function startApp(){
  try {
    me=await api("/api/auth/me"); showApp();
    $("user-name").textContent=me.name; $("welcome-name").textContent=me.name.split(" ")[0];
    $("user-avatar").textContent=me.name.charAt(0).toUpperCase();
    document.querySelectorAll(".admin-only").forEach(x=>x.hidden=me.role!=="admin");
    page("overview"); await loadDashboard();
  } catch(e){token="";localStorage.removeItem("nt_token");showAuth();}
}
function rowHtml(r, history=false){
  return `<tr><td>${safe(r.participant_name)}</td><td>${r.age_years}</td><td>${r.bmi.toFixed(2)}</td><td><span class="pill">${safe(r.indicator_status.replaceAll("_"," "))}</span></td><td>${new Date(r.created_at).toLocaleDateString()}</td><td><button class="action" data-report="${r.id}">PDF</button>${history?`<button class="action danger" data-delete="${r.id}">Delete</button>`:""}</td></tr>`;
}
async function loadDashboard(){
  try{
    const [s,rows,ml]=await Promise.all([api("/api/summary"),api("/api/assessments"),api("/api/ml/status")]);
    $("total").textContent=s.total_assessments;$("young").textContent=s.under_20_records;$("adult").textContent=s.adult_records;$("flags").textContent=s.review_flags;
    $("ml-status").textContent=ml.message;
    $("latest").innerHTML=s.latest_assessment?`<div class="latest-data"><b>${safe(s.latest_assessment.participant_name)}</b><br>Age: ${s.latest_assessment.age_years}<br>Descriptive BMI: ${s.latest_assessment.bmi}<br>Status: ${safe(s.latest_assessment.indicator_status.replaceAll("_"," "))}<br><button class="action" data-report="${s.latest_assessment.id}">Download report</button></div>`:`<div class="latest-empty">No assessments yet. Create your first assessment to see a summary here.</div>`;
    $("records").innerHTML=rows.slice(0,6).map(r=>rowHtml(r)).join("")||`<tr><td colspan="6">No assessments yet. Add your first record.</td></tr>`;
    drawChart(rows);
  }catch(e){$("ml-status").textContent="Unable to load data. Please refresh or sign in again.";}
}
function drawChart(rows){
  const list=[...rows].reverse().slice(-12),ctx=$("trend-chart");
  if(chart)chart.destroy();
  chart=new Chart(ctx,{type:"line",data:{labels:list.map(r=>r.participant_name),datasets:[{label:"Descriptive BMI",data:list.map(r=>r.bmi),borderColor:"#108675",backgroundColor:"rgba(16,134,117,.12)",fill:true,tension:.3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:false},x:{ticks:{maxRotation:0}}}}});
}
$("assessment-form").addEventListener("submit",async e=>{
  e.preventDefault();const d=Object.fromEntries(new FormData(e.target));
  ["age_years","height_cm","weight_kg","meals_per_day"].forEach(k=>d[k]=Number(d[k]));
  try{await api("/api/assessments",{method:"POST",body:JSON.stringify(d)});$("form-message").textContent="Assessment saved successfully.";e.target.reset();page("overview");await loadDashboard();}
  catch(err){$("form-message").textContent=err.message;}
});
async function loadHistory(){try{const rows=await api("/api/assessments");$("history-records").innerHTML=rows.map(r=>rowHtml(r,true)).join("")||`<tr><td colspan="6">No saved assessments.</td></tr>`;}catch(e){}}
async function loadRecommendations(){try{const x=await api("/api/recommendations");$("recommendation-list").innerHTML=x.recommendations.map(r=>`<article class="rec-card"><h3>${safe(r.category)}</h3><p>${safe(r.message)}</p></article>`).join("")||`<article class="rec-card"><h3>No recommendations yet</h3><p>Save an assessment to see general food and nutrition suggestions.</p></article>`;}catch(e){}}
async function loadAdmin(){try{const [s,users]=await Promise.all([api("/api/admin/stats"),api("/api/admin/users")]);$("admin-users").textContent=s.users;$("admin-assessments").textContent=s.assessments;$("admin-adult").textContent=s.adult_records;$("admin-young").textContent=s.under_20_records;$("admin-user-list").innerHTML=users.map(u=>`<tr><td>${safe(u.name)}</td><td>${safe(u.email)}</td><td>${safe(u.role)}</td><td>${new Date(u.created_at).toLocaleDateString()}</td></tr>`).join("");}catch(e){$("admin-user-list").innerHTML="<tr><td colspan='4'>Admin access required.</td></tr>";}}
document.addEventListener("click",async e=>{
  const report=e.target.dataset.report,del=e.target.dataset.delete;
  if(report){try{const res=await fetch(`${API}/api/assessments/${report}/report`,{headers:authHeaders()});if(!res.ok)throw Error("Could not generate report");const blob=await res.blob(),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=`nutritrack-report-${report}.pdf`;a.click();URL.revokeObjectURL(url);}catch(err){alert(err.message);}}
  if(del&&confirm("Delete this assessment?")){try{await api(`/api/assessments/${del}`,{method:"DELETE"});await loadHistory();await loadDashboard();}catch(err){alert(err.message);}}
});
$("refresh").addEventListener("click",loadDashboard);
if(token)startApp();else showAuth();
