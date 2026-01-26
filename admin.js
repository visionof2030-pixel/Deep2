const API = location.origin;
const token = localStorage.getItem("admin_token");

if (!token) {
  location.href = "/login.html";
}

async function loadCodes() {
  const res = await fetch(API + "/admin/codes", {
    headers: { "x-admin-token": token }
  });
  const data = await res.json();
  const table = document.getElementById("codes");
  table.innerHTML = "";

  data.forEach(c => {
    table.innerHTML += `
      <tr>
        <td>${c.name || "-"}</td>
        <td>${c.code}</td>
        <td><button onclick="copyCode('${c.code}')">نسخ</button></td>
        <td>${c.active ? "فعال" : "مغلق"}</td>
        <td>${c.expires_at || "-"}</td>
        <td><button onclick="toggle(${c.id})">تبديل</button></td>
        <td><button onclick="del(${c.id})">حذف</button></td>
      </tr>
    `;
  });
}

async function generate() {
  const days = document.getElementById("days").value;
  const limit = document.getElementById("limit").value;
  const name = document.getElementById("name").value;

  const res = await fetch(API + "/admin/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-admin-token": token
    },
    body: JSON.stringify({
      expires_at: days ? parseInt(days) : null,
      usage_limit: limit ? parseInt(limit) : null,
      name: name || null
    })
  });

  const data = await res.json();
  alert("تم توليد الكود:\n" + data.code);
  loadCodes();
}

async function toggle(id) {
  await fetch(API + `/admin/code/${id}/toggle`, {
    method: "PUT",
    headers: { "x-admin-token": token }
  });
  loadCodes();
}

async function del(id) {
  await fetch(API + `/admin/code/${id}`, {
    method: "DELETE",
    headers: { "x-admin-token": token }
  });
  loadCodes();
}

function copyCode(code) {
  navigator.clipboard.writeText(code);
  alert("تم النسخ");
}

loadCodes();