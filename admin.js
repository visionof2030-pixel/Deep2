const token = localStorage.getItem("ADMIN_TOKEN");
if(!token) location.href="/login.html";

function headers(){
  return {
    "Content-Type":"application/json",
    "x-admin-token": token
  }
}

async function load(){
  const r = await fetch("/admin/codes",{headers:headers()});
  if(r.status===401){logout();return}
  const data = await r.json();
  const rows = document.getElementById("rows");
  rows.innerHTML="";
  data.forEach(c=>{
    rows.innerHTML+=`
      <tr>
        <td>${c.name||""}</td>
        <td>${c.code}</td>
        <td><button onclick="copy('${c.code}')">📋</button></td>
        <td><button onclick="toggle(${c.id})">${c.active?"🟢":"🔴"}</button></td>
        <td>${c.remaining_days ?? "-"}</td>
        <td><button onclick="del(${c.id})">❌</button></td>
      </tr>
    `
  })
}

async function generate(){
  await fetch("/admin/generate",{
    method:"POST",
    headers:headers(),
    body:JSON.stringify({
      name: name.value || null,
      days: days.value ? parseInt(days.value):null,
      usage_limit: limit.value ? parseInt(limit.value):null
    })
  })
  load()
}

function copy(t){navigator.clipboard.writeText(t)}

async function toggle(id){
  await fetch(`/admin/code/${id}/toggle`,{method:"PUT",headers:headers()})
  load()
}

async function del(id){
  if(!confirm("حذف؟"))return
  await fetch(`/admin/code/${id}`,{method:"DELETE",headers:headers()})
  load()
}

function logout(){
  localStorage.removeItem("ADMIN_TOKEN");
  location.href="/login.html";
}

if("serviceWorker" in navigator){
  navigator.serviceWorker.register("/sw.js");
}

load()