const API = location.origin;

/* التوكن الصحيح (متطابق مع login.html) */
const token = localStorage.getItem("ADMIN_TOKEN");

/* لو مافي توكن يرجع لصفحة الدخول */
if (!token) {
  location.href = "/static/login.html";
}

/* تحميل الأكواد */
async function loadCodes() {
  const res = await fetch(API + "/admin/codes", {
    headers: { "x-admin-token": token }
  });

  if (!res.ok) {
    alert("فشل جلب الأكواد");
    return;
  }

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
        <td><button onclick="toggleCode(${c.id})">تبديل</button></td>
        <td><button onclick="deleteCode(${c.id})">حذف</button></td>
      </tr>
    `;
  });
}

/* توليد كود */
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

  if (!res.ok) {
    alert("فشل توليد الكود");
    return;
  }

  const data = await res.json();
  alert("تم توليد الكود:\n" + data.code);
  loadCodes();
}

/* تفعيل / تعطيل */
async function toggleCode(id) {
  await fetch(API + `/admin/code/${id}/toggle`, {
    method: "PUT",
    headers: { "x-admin-token": token }
  });
  loadCodes();
}

/* حذف */
async function deleteCode(id) {
  if (!confirm("هل أنت متأكد من الحذف؟")) return;

  await fetch(API + `/admin/code/${id}`, {
    method: "DELETE",
    headers: { "x-admin-token": token }
  });
  loadCodes();
}

/* نسخ */
function copyCode(code) {
  navigator.clipboard.writeText(code);
  alert("تم النسخ");
}

/* تسجيل خروج */
function logout() {
  localStorage.removeItem("ADMIN_TOKEN");
  location.href = "/static/login.html";
}

loadCodes();